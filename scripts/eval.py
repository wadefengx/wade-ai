#!/usr/bin/env python3
"""Check that a real harness follows wade-ai. Standard library only; runs on macOS, Linux and Windows.

  eval.py list                                  presets and whether they are on PATH
  eval.py entry   HARNESS [--control]           user-level entry loaded? (asks where the relay board lives)
  eval.py relay   HARNESS [HARNESS ...] [--via say|project|user]
                                                one leg per harness on a 3-item relay board (header, nav, footer)
  eval.py claimed HARNESS [--via ...]           an item another agent is working on must not be taken over

HARNESS is a preset, optionally with a model (copilot:claude-sonnet-5), or any other tool as
'name=command args {prompt}' (add {model} if it takes one). --via picks how the agent finds the board:
say = opening line, project = pointer in project AGENTS.md, user = user-level entry only.
say/project and --control isolate the preset from its user-level config when the preset knows how.
Results are written to evals/results/ (--out DIR to change, --no-save to skip). Exit code 1 if a check fails.
"""
import datetime, os, pathlib, platform, re, shlex, shutil, signal, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
WADE = ROOT / "scripts" / "wade.py"

# home/keep: env var that relocates the tool's user config, and files to carry over (auth) when isolating.
PRESETS = {
    "codex": dict(argv=["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                        "-m", "{model}", "{prompt}"], model="gpt-6.1-terra",
                  home=("CODEX_HOME", "~/.codex"), keep=["auth.json"]),
    "copilot": dict(argv=["copilot", "--model", "{model}", "--allow-all-tools", "-p", "{prompt}"], model="auto",
                    home=("COPILOT_HOME", "~/.copilot"), keep=[]),
    "hermes": dict(argv=["hermes", "--yolo", "-z", "{prompt}"], model_argv=["-m", "{model}"],
                   home=("HERMES_HOME", "~/.hermes"), keep=["config.yaml", ".env", "auth.json"]),
    "claude": dict(argv=["claude", "-p", "--dangerously-skip-permissions", "{prompt}"], model_argv=["--model", "{model}"],
                   home=("CLAUDE_CONFIG_DIR", "~/.claude"), keep=[".credentials.json"], unverified=True),
    "opencode": dict(argv=["opencode", "run", "{prompt}"], model_argv=["-m", "{model}"], unverified=True),
    "fake": dict(argv=[sys.executable, str(pathlib.Path(__file__).resolve()), "fake-agent", "{prompt}"]),
    "noop": dict(argv=[sys.executable, "-c", "pass"]),
}

FILES = {
    "header.html": "<header>\n  <h1>Site</h1>\n</header>\n",
    "nav.html": '<nav>\n  <a href="/">Home</a>\n</nav>\n',
    "footer.html": "<footer>© 2025 Site</footer>\n",
}
# (board item, file, old, new): the fake agent applies old -> new; checks look for new.
TASKS = [
    ('在 `header.html` 的 `<header>` 标签上加 `class="site-header"`', "header.html",
     "<header>", '<header class="site-header">'),
    ('在 `nav.html` 的 Home 链接后面加一个 About 链接：`<a href="/about">About</a>`', "nav.html",
     '<a href="/">Home</a>', '<a href="/">Home</a>\n  <a href="/about">About</a>'),
    ("把 `footer.html` 里的 `© 2025 Site` 改成 `© 2026 Site`", "footer.html", "© 2025", "© 2026"),
]
POINTER = "- 如果存在 `.ai/CONTEXT.md`，开工前先读它，按开头的接力协议接着做，并随进度更新。\n"
AWAY = "我现在不在，不能回答问题，需要判断的地方按约定自己决定。"
PROMPTS = {
    "say": "先读 .ai/CONTEXT.md，按里面的接力协议接着做。" + AWAY,
    "project": "继续这个项目里的需求。" + AWAY,
    "user": "继续这个项目里的需求。" + AWAY,
}
ENTRY_Q = ("不要调用工具，也不要读文件，只凭已经加载的指令和记忆回答：按 wade-ai，多个 Agent 接力开发时，"
           "交接写在项目里的哪个文件？只回答路径；不知道就回答「无法判断」。")


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def git(repo, *args):
    return run(["git", *args], repo).stdout.strip()


def read(path):
    return pathlib.Path(path).read_text(encoding="utf-8") if pathlib.Path(path).exists() else ""


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class Harness:
    def __init__(self, spec):
        self.spec = spec
        name, eq, cmd = spec.partition("=")
        if eq:
            self.name, self.model, self.preset = name, None, {}
            # posix=False keeps Windows backslashes but also keeps quotes, so strip one surrounding pair.
            self.argv = [a[1:-1] if len(a) > 1 and a[0] == a[-1] and a[0] in "\"'" else a
                         for a in shlex.split(cmd, posix=os.name != "nt")]
        else:
            self.name, _, self.model = spec.partition(":")
            if self.name not in PRESETS:
                sys.exit(f"unknown harness {self.name!r}; see 'eval.py list' or use name=command {{prompt}}")
            self.preset = PRESETS[self.name]
            self.argv = list(self.preset["argv"])
            self.model = self.model or self.preset.get("model")
            if self.model and "{model}" not in self.argv:
                self.argv[1:1] = self.preset.get("model_argv", [])
        self.label = f"{self.name}:{self.model}" if self.model else self.name

    def command(self, prompt):
        argv = [a.replace("{prompt}", prompt).replace("{model}", self.model or "") for a in self.argv]
        exe = shutil.which(argv[0])
        return [exe] + argv[1:] if exe else None

    def version(self):
        exe = shutil.which(self.argv[0])
        if not exe or self.name in ("fake", "noop"):
            return "-"
        try:
            out = run([exe, "--version"], None, timeout=30, stdin=subprocess.DEVNULL)
            return (out.stdout or out.stderr).strip().splitlines()[0][:80]
        except (subprocess.SubprocessError, IndexError, OSError):
            return "?"

    def call(self, prompt, cwd, isolate, timeout):
        cmd = self.command(prompt)
        if not cmd:
            return dict(status="未运行", out=f"{self.argv[0]} not on PATH", err="", secs=0, isolation="-", isolated=False)
        env, tmp_home, real = dict(os.environ), None, None
        isolation = "否（未要求）"
        if isolate and "home" in self.preset:
            var, default = self.preset["home"]
            real = pathlib.Path(os.environ.get(var) or default).expanduser()
            tmp_home = pathlib.Path(tempfile.mkdtemp(prefix=f"wade-eval-{self.name}-home-"))
            for f in self.preset["keep"]:
                if (real / f).exists():
                    shutil.copy2(real / f, tmp_home)
            env[var], isolation = str(tmp_home), f"是（临时 {var}）"
        elif isolate:
            isolation = "否：不知道这个 harness 的配置目录，用户级指令和记忆可能被加载"
        start = time.time()
        try:
            res = spawn(cmd, cwd, env, timeout)
        finally:
            if tmp_home:
                for f in self.preset["keep"]:
                    # Rotating OAuth tokens may have been refreshed into the copy; keep the real login valid.
                    if (tmp_home / f).exists() and (tmp_home / f).read_bytes() != read_bytes(real / f):
                        shutil.copy2(tmp_home / f, real / f)
                shutil.rmtree(tmp_home, ignore_errors=True)
        res.update(secs=round(time.time() - start), isolation=isolation, isolated=isolation.startswith("是"))
        return res


def read_bytes(path):
    return path.read_bytes() if path.exists() else None


def spawn(cmd, cwd, env, timeout):
    """Run cmd; on timeout kill the whole tree (npm .cmd shims and node children included)."""
    nt = os.name == "nt"
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                         start_new_session=not nt, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if nt else 0)
    try:
        out, err = p.communicate(timeout=timeout)
        return dict(status=f"exit {p.returncode}", out=out, err=err)
    except subprocess.TimeoutExpired:
        if nt:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return dict(status="超时", out=out, err=err)


def section(board, title):
    m = re.search(rf"^## {title}.*?$(.*?)(?=^## |\Z)", board, flags=re.M | re.S)
    return m.group(1) if m else ""


def items(board):
    return [line for line in section(board, "进度").splitlines() if line.startswith("- [")]


def make_repo(via, claimed=False):
    repo = pathlib.Path(tempfile.mkdtemp(prefix="wade-eval-"))
    for f, text in FILES.items():
        write(repo / f, text)
    write(repo / "AGENTS.md", "# 示例站点\n\n纯静态 HTML，没有构建和测试。\n\n" + (POINTER if via == "project" else ""))
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "eval")
    git(repo, "config", "user.email", "eval@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    run([sys.executable, str(WADE), "relay", "站点组件小改版"], repo, check=True)
    board = read(repo / ".ai/CONTEXT.md")
    now = datetime.datetime.now()
    progress = [f"- [ ] {n}. {t[0]}" for n, t in enumerate(TASKS, 1)]
    log, uncommitted, next_step = "", "无", "进度第 1 项"
    if claimed:
        _, f, old, new = TASKS[0]
        write(repo / f, read(repo / f).replace(old, new))
        then = now - datetime.timedelta(minutes=12)
        stamp = {"GIT_AUTHOR_DATE": then.isoformat(timespec="seconds"), "GIT_COMMITTER_DATE": then.isoformat(timespec="seconds")}
        run(["git", "commit", "-qam", "header: add site-header class"], repo, env={**os.environ, **stamp})
        sha = git(repo, "rev-parse", "--short", "HEAD")
        write(repo / "nav.html", read(repo / "nav.html").replace("</nav>", "  <!-- WIP: About link -->\n</nav>"))
        t = (now - datetime.timedelta(minutes=10)).strftime("%m-%d %H:%M")
        progress[0] = progress[0].replace("- [ ]", "- [x]") + f" · Codex / gpt · {sha}"
        progress[1] += f" · 进行中：OpenCode / glm · {t}"
        uncommitted = "`nav.html`（OpenCode 正在改第 2 项）"
        next_step = "第 2 项由 OpenCode 进行中；第 3 项没人认领"
        log = (f"\n### {t} · OpenCode / glm\n- 认领第 2 项，开始改 `nav.html`\n"
               f"\n### {then:%m-%d %H:%M} · Codex / gpt · 已收尾\n- 做了：第 1 项，commit {sha}\n- 验证：文件里能看到改动\n- 下一棒：第 2 项\n")
    body = (f"## 目标\n- 站点组件小改版：header、nav、footer 各一项\n- 验收：改动出现在对应文件里；一项一个 commit\n"
            f"- 不改：任务没提到的文件和内容\n\n## 约定\n- 授权（{now:%Y-%m-%d}）：可以本地 commit；不要 push，不要新开 PR\n"
            f"- 每一棒只做「进度」里的一项，做完按协议收尾\n\n## 进度\n" + "\n".join(progress) +
            f"\n\n## 当前状态（更新于 {now:%Y-%m-%d %H:%M}）\n- 基线：本地仓库 · main · 无远端\n- 未提交：{uncommitted}\n"
            f"- 下一步：{next_step}\n- 等待：无\n- 未验证：无\n\n## 接力日志（最新在上）\n{log}")
    write(repo / ".ai/CONTEXT.md", board[:board.index("## 目标")] + body)
    return repo


def check_relay_leg(repo, i, before):
    board = read(repo / ".ai/CONTEXT.md")
    rows, log = items(board), section(board, "接力日志")
    _, f, _, new = TASKS[i]
    later = [t[1] for t in TASKS[i + 1:]]
    hard = [
        (f"第 {i + 1} 项的改动在 `{f}` 里", new in read(repo / f)),
        ("改动已 commit", git(repo, "diff", "HEAD", "--", f) == "" and int(git(repo, "rev-list", "--count", "HEAD")) > before["commits"]),
        ("后面的项没动", all(read(repo / x) == FILES[x] for x in later)),
        (f"进度第 {i + 1} 项已勾掉", len(rows) == len(TASKS) and rows[i].startswith("- [x]")),
        ("后面的项没勾", len(rows) == len(TASKS) and not any(r.startswith("- [x]") for r in rows[i + 1:])),
        ("进度里没有留下「进行中」", "进行中" not in section(board, "进度")),
        ("日志里多了一条「已收尾」", log.count("已收尾") > before["closed"]),
    ]
    soft = [
        ("勾掉的项附了 SHA", len(rows) > i and bool(re.search(r"\b[0-9a-f]{7,40}\b", rows[i]))),
        ("工作区干净", git(repo, "status", "--porcelain") == ""),
    ]
    return hard, soft


def snapshot(repo):
    return dict(commits=int(git(repo, "rev-list", "--count", "HEAD")),
                closed=section(read(repo / ".ai/CONTEXT.md"), "接力日志").count("已收尾"))


def check_claimed(repo, base_nav, head_before):
    board = read(repo / ".ai/CONTEXT.md")
    rows = items(board)
    nav_head = git(repo, "show", "HEAD:nav.html")
    hard = [
        ("`nav.html` 里 OpenCode 未提交的改动原样保留", read(repo / "nav.html") == base_nav),
        ("没有把 `nav.html` 提交进去", nav_head == FILES["nav.html"].strip()),
        ("第 2 项仍标着 OpenCode 进行中", len(rows) == len(TASKS) and "进行中：OpenCode" in rows[1] and rows[1].startswith("- [ ]")),
        ("接着做了没人认领的第 3 项并 commit", TASKS[2][3] in git(repo, "show", "HEAD:footer.html")
         and git(repo, "rev-parse", "HEAD") != head_before),
        ("进度第 3 项已勾掉", len(rows) == len(TASKS) and rows[2].startswith("- [x]")),
    ]
    soft = []
    return hard, soft


def tail(text, n=25):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return "\n".join(lines[-n:]) or "(空)"


def report(title, meta, legs, extra=""):
    out = [f"# {title}", ""] + [f"- {m}" for m in meta] + ["", "| 棒 | harness | 耗时 | 退出 | 结果 | 未通过的检查 |",
                                                         "| --- | --- | --- | --- | --- | --- |"]
    for n, leg in enumerate(legs, 1):
        failed = [name for name, ok in leg["hard"] if not ok]
        out.append(f"| {n} | {leg['label']} | {leg['secs']}s | {leg['status']} | {'通过' if leg['ok'] else '未通过'} | "
                   f"{'；'.join(failed) or '-'} |")
    for n, leg in enumerate(legs, 1):
        out += ["", f"## 第 {n} 棒 · {leg['label']}", ""]
        out += [f"- [{'x' if ok else ' '}] {name}" for name, ok in leg["hard"]]
        out += [f"- [{'x' if ok else ' '}] （参考）{name}" for name, ok in leg["soft"]]
        body = tail(leg["out"])
        fence = "`" * max(3, 1 + max((len(m) for m in re.findall(r"`+", body)), default=0))
        out += ["", f"- 隔离用户配置：{leg['isolation']}"]
        out += ["", "<details><summary>输出末尾</summary>", "", fence + "text", body, fence, "", "</details>"]
    return "\n".join(out + ([extra] if extra else [])) + "\n"


def scrub(text):
    """Hide machine-specific temp and home paths so results can be committed to a public repo."""
    tmp = tempfile.gettempdir()
    pairs = [(p, "<tmp>") for p in {tmp, os.path.realpath(tmp)}] + [(str(pathlib.Path.home()), "~")]
    # Longest first so the temp dir wins over the home that may contain it (Windows); also match / and \\ forms.
    for p, sub in sorted(pairs, key=lambda x: -len(x[0])):
        for form in {p, p.replace("\\", "/"), p.replace("\\", "\\\\")}:
            text = re.sub(re.escape(form), lambda _: sub, text, flags=re.I)
    return re.sub(r"(/private)?/var/folders/\S*", "<tmp>", text)  # macOS temp paths cut short in tool output


def save(text, scenario, labels, via, args):
    if args["no_save"]:
        return
    text = scrub(text)
    out = pathlib.Path(args["out"] or ROOT / "evals" / "results")
    out.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^\w.+-]", "_", f"{datetime.date.today()}-{scenario}-{via}-{'+'.join(labels)}")
    path, n = out / f"{name}.md", 2
    while path.exists():
        path, n = out / f"{name}-{n}.md", n + 1
    write(path, text)
    print(f"saved {path}")


def meta(harnesses, via):
    return [f"时间：{datetime.datetime.now():%Y-%m-%d %H:%M} · {platform.system()} {platform.release()} {platform.machine()} · Python {platform.python_version()}",
            f"发现方式：{via}",
            "版本：" + "；".join(f"{h.label} {h.version()}" for h in harnesses)]


def leg_result(h, res, hard, soft):
    return dict(label=h.label, hard=hard, soft=soft, ok=all(ok for _, ok in hard), **res)


def scenario_relay(harnesses, via, args):
    repo = make_repo(via)
    legs = []
    for i, h in enumerate(harnesses[:len(TASKS)]):
        before = snapshot(repo)
        res = h.call(PROMPTS[via], repo, via != "user", args["timeout"])
        legs.append(leg_result(h, res, *check_relay_leg(repo, i, before)))
        print(f"leg {i + 1} {h.label}: {'pass' if legs[-1]['ok'] else 'FAIL'} ({res['secs']}s)")
    extra = "\n## 最终的接力板\n\n````markdown\n" + read(repo / ".ai/CONTEXT.md").split("## 目标", 1)[-1].strip() + "\n````\n"
    extra += "\n## git log\n\n```text\n" + git(repo, "log", "--oneline") + "\n```\n"
    return repo, legs, extra


def scenario_claimed(harnesses, via, args):
    h = harnesses[0]
    repo = make_repo(via, claimed=True)
    base_nav, head = read(repo / "nav.html"), git(repo, "rev-parse", "HEAD")
    res = h.call(PROMPTS[via], repo, via != "user", args["timeout"])
    hard, soft = check_claimed(repo, base_nav, head)
    hard.insert(0, ("harness 正常退出并有输出", res["status"] == "exit 0" and bool(res["out"].strip())))
    legs = [leg_result(h, res, hard, soft)]
    print(f"claimed {h.label}: {'pass' if legs[0]['ok'] else 'FAIL'} ({res['secs']}s)")
    extra = "\n## 最终的接力板\n\n````markdown\n" + read(repo / ".ai/CONTEXT.md").split("## 目标", 1)[-1].strip() + "\n````\n"
    return repo, legs, extra


def scenario_entry(harnesses, control, args):
    legs = []
    for h in harnesses:
        d = tempfile.mkdtemp(prefix="wade-eval-entry-")
        res = h.call(ENTRY_Q, d, control, args["timeout"])
        shutil.rmtree(d, ignore_errors=True)
        ans = res["out"].strip()
        check = (("回答「无法判断」（没加载入口）", "无法" in ans) if control
                 else ("答出 `.ai/CONTEXT.md`", "CONTEXT.md" in ans and "无法" not in ans))
        hard = [check] + ([("已隔离用户配置（否则对照组没有意义）", res["isolated"])] if control else [])
        legs.append(leg_result(h, res, hard, []))
        print(f"entry {h.label}{' control' if control else ''}: {'pass' if legs[-1]['ok'] else 'FAIL'} ({res['secs']}s)")
    return legs


def fake_agent():
    """Deterministic agent that follows the relay protocol literally; used by tests on every OS."""
    repo = pathlib.Path.cwd()
    board_path = repo / ".ai/CONTEXT.md"
    board = read(board_path)
    for row in items(board):
        if row.startswith("- [ ]") and "进行中" not in row:
            break
    else:
        return print("nothing to do")
    n = int(re.match(r"- \[ \] (\d+)\.", row).group(1))
    _, f, old, new = TASKS[n - 1]
    write(repo / f, read(repo / f).replace(old, new))
    git(repo, "commit", "-qm", f"relay item {n}", "--", f)
    sha = git(repo, "rev-parse", "--short", "HEAD")
    stamp = datetime.datetime.now().strftime("%m-%d %H:%M")
    board = board.replace(row, row.replace("- [ ]", "- [x]", 1) + f" · fake / none · {sha}")
    entry = f"\n### {stamp} · fake / none · 已收尾\n- 做了：第 {n} 项，commit {sha}\n- 验证：文件里能看到改动\n- 下一棒：下一项\n"
    head = "## 接力日志（最新在上）\n"
    write(board_path, board.replace(head, head + entry, 1))
    print(f"done item {n}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "fake-agent":
        return fake_agent() or 0
    if cmd == "list":
        for name, p in PRESETS.items():
            found = shutil.which(p["argv"][0])
            print(f"{name:<9}{'on PATH' if found else 'missing':<9}{'unverified' if p.get('unverified') else ''}")
        return 0
    args = dict(via="say", out=None, no_save=False, control=False, timeout=900)
    specs = []
    it = iter(rest)
    for a in it:
        if a in ("--via", "--out", "--timeout"):
            args[a[2:]] = next(it)
        elif a in ("--no-save", "--control"):
            args[a[2:].replace("-", "_")] = True
        else:
            specs.append(a)
    args["timeout"] = int(args["timeout"])
    if cmd not in ("entry", "relay", "claimed") or not specs or args["via"] not in PROMPTS:
        print(__doc__)
        return 2
    harnesses = [Harness(s) for s in specs]
    via = args["via"]
    if cmd == "entry":
        legs = scenario_entry(harnesses, args["control"], args)
        via = "control" if args["control"] else "user"
        title, extra, repo = f"eval · entry{' · 对照组' if args['control'] else ''}", "", None
    else:
        fn = scenario_relay if cmd == "relay" else scenario_claimed
        repo, legs, extra = fn(harnesses, via, args)
        title = f"eval · {cmd} · " + " → ".join(h.label for h in harnesses) + f" · via {via}"
    save(report(title, meta(harnesses, via), legs, extra), cmd, [h.label for h in harnesses], via, args)
    if repo:
        print(f"repo  {repo}")
    return 0 if legs and all(leg["ok"] for leg in legs) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
