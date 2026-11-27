# Harness 速查

各 harness 从哪里读指令、怎么一次性调用、评估时怎么隔离，以及踩过的坑。路径以各工具当前的文档为准，工具升级后用 `scripts/eval.py entry` 复查一次〔[SIM-004](sim.md#sim-004)〕。表里没有的工具，按[最后一节](#新工具怎么接)接。

## 入口和调用

| harness | 用户级入口 | 项目里读的文件 | 一次性调用（评估预设） | 评估时隔离用户配置 | 本机实测 |
| --- | --- | --- | --- | --- | --- |
| Codex | `~/.codex/AGENTS.md`（`$CODEX_HOME`），软链 | 从 git 根到当前目录的 `AGENTS.md` | `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -m <模型> <提示>` | 临时 `CODEX_HOME`，只带 `auth.json` | 通过 |
| Copilot CLI | `~/.copilot/instructions/*.instructions.md`（`$COPILOT_HOME`），软链；`copilot instruction list` 能看到实际加载了什么 | `AGENTS.md`、`.github/copilot-instructions.md`、`.github/instructions/*.instructions.md` | `copilot --model <模型> --allow-all-tools -p <提示>` | 临时 `COPILOT_HOME`，登录态在系统钥匙串里不受影响 | 通过 |
| Hermes Agent | 没有用户级指令文件。持久记忆 `~/.hermes/memories/MEMORY.md`（上限约 2200 字）充当这一层，写一条指向 wade-ai 的记忆 | 从 git 根到当前目录的 `AGENTS.md`，以及 `.hermes.md`、`CLAUDE.md`、`.cursorrules` | `hermes --yolo -z <提示>` | 临时 `HERMES_HOME`，带 `config.yaml`、`.env`、`auth.json` | 通过 |
| Claude Code | `~/.claude/CLAUDE.md` 里一行 `@~/ai-kb/wade-ai/AGENTS.md`（有的会话会跳过软链） | `CLAUDE.md`。项目只有 `AGENTS.md` 时，在 `CLAUDE.md` 里写一行 `@AGENTS.md` | `claude -p --dangerously-skip-permissions <提示>` | `CLAUDE_CONFIG_DIR` | 未测：本机未登录 |
| OpenCode | `~/.config/opencode/AGENTS.md`（`$XDG_CONFIG_HOME`），软链 | `AGENTS.md`，没有时读 `CLAUDE.md` | `opencode run <提示>` | 未定 | 未测：本机没装 |
| DeepSeek Harness | `~/.dsh/AGENTS.md`（`$DSH_HOME`），软链 | `AGENTS.md` | 未定，用自定义命令模板 | 未定 | 未测：本机没装 |

「本机实测」指 2026-11-27 在 macOS 上跑过 `entry`、`relay` 和 `claimed`，结果在 [evals/results](../evals/results/)。

## 踩过的坑

- **Codex**：用 ChatGPT 账号时，有的模型调不了（返回 `model_not_in_accessible_catalog`），`config.toml` 里写了这样的模型，所有调用都会失败。换一个能用的模型，或者调用时加 `-m`。`codex exec` 不重定向 stdin 时会一直等输入，脚本里要接 `/dev/null`。在非 git 目录里要加 `--skip-git-repo-check`。
- **Copilot CLI**：默认模型可能不可用，用 `--model auto` 或指定一个模型。`--no-custom-instructions` 会把项目里的 `AGENTS.md` 也一起关掉，只适合测「开场一句话」这一层。指令文件里的 `@` 导入不支持 `~/` 和绝对路径，所以用户级入口用软链。全局的 `instructions/` 下不要放某个仓库专用的规则，它们在所有目录里都会生效。
- **Hermes**：`--safe-mode` 会连 provider 配置一起关掉，输出为空，不能拿来做对照组，要用临时 `HERMES_HOME`。新的 `HERMES_HOME` 第一次运行会先安装依赖，大约慢 1 分钟。它的记忆里有过期的规则时，会照旧的执行，改 wade-ai 结构后顺带检查一遍。日志时间它会自己估，协议里写明了用 `date` 取。
- **Claude Code**：Cowork 和云端会话里不读软链的 `CLAUDE.md`，所以用 `@` 导入。
- **所有工具**：自带的记忆（Claude 项目记忆、Hermes 记忆、Copilot 记忆）可能还留着旧路径或旧规则。wade-ai 的结构变了以后，在这些地方搜一下旧文件名。

## Windows

- 用户目录是 `%USERPROFILE%`，上面的 `~/` 都换成它。安装和评估都用 `py scripts\wade.py …`、`py scripts\eval.py …`，脚本只用 Python 标准库。
- 没开「开发者模式」或不是管理员时建不了软链，`wade.py install` 会改为复制，并在第一行加一个标记。`git pull` 之后再运行一次 install，复制件会更新。
- npm 装的 CLI 在 Windows 上是 `.cmd` 包装，参数里有换行会被截断。评估的提示词都是一行；自己写命令模板时也保持一行。
- 超时后评估器用 `taskkill /T` 结束整个进程树，npm 包装下的 node 子进程也会被结束。
- CI 在 Windows 上跑 `wade.py check` 和 `test_wade.py`，覆盖了安装的复制回退、接力板生成和评估器本身（用内置的假 Agent）。真实 harness 在 Windows 上还没跑过。

## 新工具怎么接

1. 找它的用户级指令文件，运行 `wade.py install <路径>`。只支持导入语法的，手动加一行导入。
2. 没有用户级指令文件的，看它有没有持久记忆或类似 Hermes 的 `SOUL.md`，写一条「开发任务先读 wade-ai 的 AGENTS.md；项目里有 `.ai/CONTEXT.md` 时先读」。都没有，就靠项目 `AGENTS.md` 里的指针或开场一句话，见[接力与交接](../playbooks/handoff.md#怎么让-agent-读到)。
3. 用自定义命令模板跑一遍评估，`{prompt}` 是提示词的位置：

   ```bash
   python3 scripts/eval.py entry "mytool=mytool run --yes {prompt}"
   python3 scripts/eval.py relay codex "mytool=mytool run --yes {prompt}" hermes --via project
   ```

4. 把入口、调用方式和坑补进上面的表。
