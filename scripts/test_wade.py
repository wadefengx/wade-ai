#!/usr/bin/env python3
"""Self-test for wade.py and eval.py; standard library only, run on every OS in CI."""
import contextlib, io, os, pathlib, shutil, subprocess, sys, tempfile, unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval as ev  # noqa: E402
import wade  # noqa: E402


def quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        fn(*a)
    return out.getvalue()


class Install(unittest.TestCase):
    def setUp(self):
        self.home = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, True)

    def test_link_then_idempotent_and_foreign_file_untouched(self):
        t = self.home / "tool" / "AGENTS.md"
        quiet(wade.install, [str(t)])
        self.assertIn(wade.SRC.read_text(encoding="utf-8"), t.read_text(encoding="utf-8"))
        self.assertTrue(quiet(wade.install, [str(t)]).startswith("ok"))
        other = self.home / "other.md"
        other.write_text("mine", encoding="utf-8")
        self.assertIn("WARN", quiet(wade.install, [str(other)]))
        self.assertEqual(other.read_text(encoding="utf-8"), "mine")

    def test_copy_fallback_is_refreshed(self):
        t = self.home / "AGENTS.md"
        with mock.patch.object(pathlib.Path, "symlink_to", side_effect=OSError("no privilege")):
            self.assertIn("copy", quiet(wade.install, [str(t)]))
            t.write_text(wade.COPY_MARK + "stale\n", encoding="utf-8")
            self.assertIn("update", quiet(wade.install, [str(t)]))
        self.assertEqual(t.read_text(encoding="utf-8"), wade.copy_text())

    def test_known_tools_and_claude_import(self):
        (self.home / ".claude").mkdir()
        (self.home / ".codex").mkdir()
        env = {"HOME": str(self.home), "USERPROFILE": str(self.home)}
        with mock.patch.dict(os.environ, env), mock.patch.object(pathlib.Path, "home", return_value=self.home):
            for var in ("CODEX_HOME", "COPILOT_HOME", "DSH_HOME", "XDG_CONFIG_HOME"):
                os.environ.pop(var, None)
            out = quiet(wade.install, [])
            self.assertIn("skip", out)
            self.assertTrue((self.home / ".codex" / "AGENTS.md").exists())
            self.assertFalse((self.home / ".copilot").exists())
            imp = (self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8").strip()
            self.assertTrue(imp.startswith("@"))
            self.assertIn("ok", quiet(wade.install, []).splitlines()[0])


class Relay(unittest.TestCase):
    def test_board_exclude_and_idempotent(self):
        repo = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / "sub").mkdir()
        run = lambda *a: subprocess.run([sys.executable, str(wade.__file__), "relay", *a], cwd=repo / "sub",
                                        capture_output=True, text=True, encoding="utf-8").stdout
        self.assertIn("wrote", run("示例 & 需求"))
        board = (repo / ".ai" / "CONTEXT.md").read_text(encoding="utf-8")
        self.assertTrue(board.startswith("# 示例 & 需求 · 接力板"))
        self.assertIn("exists", run("again"))
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
        self.assertEqual(status, "")
        exclude = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8").splitlines()
        self.assertEqual(exclude.count("/.ai/CONTEXT.md"), 1)


class Eval(unittest.TestCase):
    def run_eval(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = ev.main([*argv, "--no-save"])
        for line in out.getvalue().splitlines():
            if line.startswith("repo  "):
                shutil.rmtree(line[6:], ignore_errors=True)
        return code

    def test_fake_agent_passes_every_scenario(self):
        self.assertEqual(self.run_eval("relay", "fake", "fake", "fake"), 0)
        self.assertEqual(self.run_eval("relay", "fake", "fake", "fake", "--via", "project"), 0)
        self.assertEqual(self.run_eval("claimed", "fake"), 0)

    def test_agent_that_does_nothing_fails(self):
        self.assertEqual(self.run_eval("relay", "noop"), 1)
        self.assertEqual(self.run_eval("claimed", "noop"), 1)

    def test_custom_harness_template(self):
        h = ev.Harness(f"mine={sys.executable} -c pass {{prompt}}")
        self.assertEqual(h.command("hi")[-1], "hi")
        self.assertEqual(ev.Harness("hermes:deepseek-pro").argv[1:3], ["-m", "{model}"])
        self.assertEqual(ev.Harness('x=tool --system "be brief" {prompt}').argv, ["tool", "--system", "be brief", "{prompt}"])

    def test_timeout_kills_agent(self):
        h = ev.Harness(f'slow={sys.executable} -c "import time; time.sleep(60)" {{prompt}}')
        res = h.call("hi", tempfile.gettempdir(), True, 2)
        self.assertEqual(res["status"], "超时")
        self.assertLess(res["secs"], 30)
        self.assertFalse(res["isolated"])

    def test_scrub_hides_temp_and_home_paths(self):
        tmp, home = tempfile.gettempdir(), str(pathlib.Path.home())
        text = ev.scrub(f"{os.path.join(tmp, 'wade-eval-x', 'a.html')} {os.path.join(home, 'f')} {pathlib.Path(home).as_posix()}/g")
        self.assertNotIn(tmp, text)
        self.assertNotIn(home, text)
        self.assertIn("<tmp>", text)


if __name__ == "__main__":
    unittest.main()
