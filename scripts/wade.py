#!/usr/bin/env python3
"""wade-ai helper, standard library only (macOS, Linux, Windows).

  wade.py install [PATH ...]  link AGENTS.md into user-level instruction entries
  wade.py relay [NAME]        create .ai/CONTEXT.md (relay board) in the current git project
  wade.py check               check docs: relative links, anchors, entry file length
"""
import os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "AGENTS.md"
COPY_MARK = "<!-- wade-ai copy of "


def say(tag, msg):
    print(f"{tag:<6}{msg}")


def place(target):
    """Symlink target -> AGENTS.md; copy with a marker where symlinks are not allowed (Windows)."""
    target = pathlib.Path(target).expanduser()
    if target.is_symlink():
        if target.resolve() == SRC.resolve():
            return say("ok", target)
        return say("WARN", f"{target} links elsewhere; left untouched")
    if target.exists():
        head = target.read_text(encoding="utf-8", errors="replace")
        if not head.startswith(COPY_MARK):
            return say("WARN", f"{target} exists; merge it into wade-ai or remove it, then rerun")
        copy = copy_text()
        if head == copy:
            return say("ok", f"{target} (copy)")
        target.write_text(copy, encoding="utf-8")
        return say("update", f"{target} (copy)")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.symlink_to(SRC)
        say("link", f"{target} -> {SRC}")
    except OSError:
        # ponytail: Windows without Developer Mode cannot symlink; a marked copy is refreshed by rerunning install.
        target.write_text(copy_text(), encoding="utf-8")
        say("copy", f"{target} (rerun install after git pull)")


def copy_text():
    return f"{COPY_MARK}{SRC.as_posix()}; rerun wade.py install after git pull -->\n" + SRC.read_text(encoding="utf-8")


def claude_import(home):
    """Claude Code reads ~/.claude/CLAUDE.md; an @import survives sessions that skip symlinks."""
    claude = home / ".claude"
    if not claude.is_dir():
        return say("skip", f"{claude / 'CLAUDE.md'} (tool not installed)")
    md = claude / "CLAUDE.md"
    try:
        line = "@~/" + SRC.relative_to(home).as_posix()
    except ValueError:
        line = "@" + SRC.as_posix()
    if not md.exists():
        md.write_text(line + "\n", encoding="utf-8")
        return say("write", md)
    lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
    if line in lines or "@" + SRC.as_posix() in lines:
        return say("ok", md)
    say("WARN", f"{md} exists; add this line yourself: {line}")


def install(paths):
    if paths:
        for p in paths:
            place(p)
        return 0
    home = pathlib.Path.home()
    env = os.environ.get
    claude_import(home)
    xdg = pathlib.Path(env("XDG_CONFIG_HOME") or home / ".config")
    for tool_home, rel in [
        (env("CODEX_HOME") or home / ".codex", "AGENTS.md"),
        (env("COPILOT_HOME") or home / ".copilot", "instructions/wade-ai.instructions.md"),
        (xdg / "opencode", "AGENTS.md"),
        (env("DSH_HOME") or home / ".dsh", "AGENTS.md"),
    ]:
        tool_home = pathlib.Path(tool_home)
        if tool_home.is_dir():
            place(tool_home / rel)
        else:
            say("skip", f"{tool_home / rel} (tool not installed)")
    if (home / ".hermes").is_dir():
        say("note", "Hermes has no user-level instruction file; it reads the project AGENTS.md (see playbooks/handoff.md)")
    return 0


def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else None


def relay(name):
    cwd = pathlib.Path.cwd()
    top = pathlib.Path(git("rev-parse", "--show-toplevel") or cwd)
    dest = top / ".ai" / "CONTEXT.md"
    if dest.exists():
        print(f"exists {dest}")
        return 0
    first = (git("worktree", "list", "--porcelain") or "").splitlines()[:1]
    if first and first[0].startswith("worktree "):
        main = pathlib.Path(first[0][len("worktree "):]) / ".ai" / "CONTEXT.md"
        if main.exists() and main.resolve() != dest.resolve():
            print(f"exists {main} (main worktree); use it instead of a second board")
            return 0
    tpl = (ROOT / "templates" / "CONTEXT.md").read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(tpl.replace("<需求名>", name or "<需求名>", 1))
    ex = git("rev-parse", "--git-path", "info/exclude")
    if ex:
        ex = cwd / ex
        ex.parent.mkdir(parents=True, exist_ok=True)
        old = ex.read_text(encoding="utf-8") if ex.exists() else ""
        # Only the relay files; a project may commit other things under .ai/.
        add = [p for p in ("/.ai/CONTEXT.md", "/.ai/notes/") if p not in old.splitlines()]
        if add:
            with open(ex, "a", encoding="utf-8", newline="\n") as f:
                f.write(("" if not old or old.endswith("\n") else "\n") + "\n".join(add) + "\n")
    print(f"wrote {dest}")
    return 0


LIMITS = {"AGENTS.md": 80, "playbooks/complex-work.md": 120}


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def anchors(path):
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    return {slug(h) for h in re.findall(r"^#+ (.+)$", text, flags=re.M)}


def check():
    errors = []
    for md in sorted(ROOT.rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix()
        if ".git" in md.parts or rel.startswith("evals/results/"):  # results hold raw agent output
            continue
        text = md.read_text(encoding="utf-8")
        if rel in LIMITS and text.count("\n") > LIMITS[rel]:
            errors.append(f"{rel}: {text.count(chr(10))} lines > {LIMITS[rel]}")
        for target in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"```.*?```|`[^`]*`", "", text, flags=re.S)):
            if re.match(r"[a-z]+:", target):
                continue
            file, _, anchor = target.partition("#")
            dest = (md.parent / file).resolve() if file else md
            if not dest.exists():
                errors.append(f"{rel}: missing {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                errors.append(f"{rel}: missing anchor {target}")
    print("\n".join(errors) or "docs ok")
    return 1 if errors else 0


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "install":
        return install(args)
    if cmd == "relay":
        return relay(" ".join(args))
    if cmd == "check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
