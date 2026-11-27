# Wade AI

这里是 Wade 和 AI Agent 协作开发的约定。开新项目、换 Agent，或在几个 harness 之间接力时，Agent 读一遍 [AGENTS.md](AGENTS.md)，就知道怎么开工、哪些事可以直接推进、哪些要先问 Wade，以及验证到什么程度才算交付。

## 接入

### 本机一次性安装

```bash
git clone https://github.com/wadefengx/wade-ai.git ~/ai-kb/wade-ai
python3 ~/ai-kb/wade-ai/scripts/wade.py install
```

Windows（PowerShell）：

```powershell
git clone https://github.com/wadefengx/wade-ai.git $HOME\ai-kb\wade-ai
py $HOME\ai-kb\wade-ai\scripts\wade.py install
```

各 harness 基本都有一个「用户级指令文件」，每次会话都会加载。接入就是让这个文件指向 wade-ai 的 `AGENTS.md`，任何工具都一样。

- 不带参数运行 `install`，会处理本机已安装的 Claude Code、Codex、Copilot CLI、OpenCode 和 DeepSeek Harness。
- 其他工具，找到它的用户级指令文件路径，运行 `wade.py install <路径>`。没有用户级指令文件的（比如 Hermes），见 [Harness 速查](memory/harnesses.md#新工具怎么接)。
- 建不了软链时（Windows 没开开发者模式），脚本会改为复制并加标记，`git pull` 之后再运行一次 install 就会更新。
- 重复运行没有副作用。目标位置已经有别的文件时，脚本只提示，不会覆盖。

各工具的入口路径、一次性调用方式和踩过的坑，见 [Harness 速查](memory/harnesses.md)。更新：`git -C ~/ai-kb/wade-ai pull --ff-only`。

**接入自检。** 新工具、工具升级或换机器后，跑一次 `python3 ~/ai-kb/wade-ai/scripts/eval.py entry <harness>`，见下面的[评估](#评估)。

**只对某个项目有效的指令**（门禁脚本、测试框架、覆盖率要求）放在那个仓库里，例如 `AGENTS.md` 或 `.github/instructions/*.instructions.md`，并用 `applyTo` 限定文件范围。不要放进用户级入口，否则在其他项目里也会生效。

### 多个 Agent 接力

同一个需求可以先用 Codex 改 header，关掉后用 Copilot 改 nav bar，再交给 OpenCode 或任何别的 harness 改 footer。接力只靠项目里的 `.ai/CONTEXT.md` 和 git。

- 文件开头自带接力协议，接手的 Agent 读到它就知道前面谁做了什么、自己接哪一项、做完怎么更新，不需要为某个工具单独配置。
- 开一个接力板：在项目里运行 `python3 ~/ai-kb/wade-ai/scripts/wade.py relay "<需求名>"`。
- 让 Agent 读到它的三种方式（开场一句话、项目指令文件、用户级入口）和每一棒的做法，见[接力与交接](playbooks/handoff.md)。

### 不装也能用

一次性的任务，把这段直接发给 Agent：

> 开工前读 https://github.com/wadefengx/wade-ai/blob/main/AGENTS.md ，再按本项目的约定和本轮任务执行。用实际的验证结果说明交付状态。

要固定版本，或者离线使用时，在目标项目的根目录执行下面的命令放一份快照，然后让项目的 `AGENTS.md` 指向 `.ai/wade-ai/AGENTS.md`：

```bash
mkdir -p .ai/wade-ai && git -C ~/ai-kb/wade-ai archive HEAD | tar -x -C .ai/wade-ai
```

## 目录

| 文件 | 内容 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 入口：授权和沟通、开工、验收、交付、接力、沉淀经验 |
| [playbooks/verification.md](playbooks/verification.md) | 验证与回归：按变更类型怎么验，什么证据能证明什么，常见误判 |
| [playbooks/complex-work.md](playbooks/complex-work.md) | 复杂任务：spec、计划、并行和子代理、何时停下来问 |
| [playbooks/review.md](playbooks/review.md) | 评审与修复循环：分级、一轮怎么算、何时停 |
| [playbooks/handoff.md](playbooks/handoff.md) | 接力与交接：`.ai/CONTEXT.md` 模板，每一棒开工、过程和收尾 |
| [playbooks/sim.md](playbooks/sim.md) | SIM 方法：什么时候写，怎么写，怎么用旧记录，项目里的 RSI |
| [memory/sim.md](memory/sim.md) | wade-ai 共享的 SIM 记录，也记录 wade-ai 规则本身的改动 |
| [ponytail.md](ponytail.md) | 实现上的取舍：先理解，再选最省的做法 |
| [examples/tags-regression.md](examples/tags-regression.md) | 一个从真实入口验收的脱敏案例 |
| [templates/CONTEXT.md](templates/CONTEXT.md) | 接力板模板，开头自带接力协议 |
| [memory/harnesses.md](memory/harnesses.md) | Harness 速查：各工具的入口、一次性调用、隔离方式和坑 |
| [scripts/](scripts/) | `wade.py`：`install` 接入、`relay` 开接力板、`check` 文档自检；`eval.py` 用真实 harness 做评估；`test_wade.py` 脚本自测 |
| [evals/results/](evals/results/) | 评估结果，每次运行一份，含最终接力板和 git log |
| [archive/](archive/) | 已归档的 [v1](archive/v1-ai-dev-instruction.md)、[Runtime v2](archive/runtime-v2.md) 和当时的[升级记录](archive/2026-08-05-runtime-v2-changelog.md) |

## 评估

规则写了不等于 Agent 会照做。`scripts/eval.py` 在临时 git 仓库里调用真实的 harness，检查结果，结果写到 `evals/results/`。

| 场景 | 测什么 | 命令 |
| --- | --- | --- |
| `entry` | 只靠入口，Agent 能不能答出一个猜不到的约定。加 `--control` 跑对照组，去掉入口后应该答不出 | `python3 scripts/eval.py entry codex` |
| `relay` | 三个 harness 依次各做一项，每一棒都要做对自己那一项、不碰别人的、更新接力板 | `python3 scripts/eval.py relay codex copilot hermes` |
| `claimed` | 有一项标着别人「进行中」、还有未提交的改动时，Agent 要跳过它、不动那些改动 | `python3 scripts/eval.py claimed copilot` |

- `--via` 指定 Agent 从哪里读到接力板：`say`（开场一句话，默认）、`project`（项目 `AGENTS.md` 里的指针）、`user`（本机的用户级入口）。前两种会把预设里已知配置目录的 harness（codex、copilot、hermes、claude）换到临时目录，只带登录文件，结束后登录文件有更新会写回。命令模板和 opencode 没法隔离，结果里会注明，入口对照组也会判为不通过。
- harness 可以写预设名（`python3 scripts/eval.py list` 查看），也可以写 `预设:模型`，或者任意命令模板 `"名字=命令 {prompt}"`。表里没有的工具也能直接测。
- Windows 上把 `python3` 换成 `py`，路径用 `scripts\eval.py`。

## 维护

- 改规则就是改 Agent 的 harness。改之前在 [memory/sim.md](memory/sim.md) 写下理由和预期，在规则行末用 `〔SIM-xxx〕` 回链，下次用到时回填实测结果。
- 提交前运行 `python3 scripts/wade.py check`（相对链接、锚点、入口文件行数）和 `python3 scripts/test_wade.py`（脚本自测，含一个按协议工作的假 Agent）。CI 在 Linux、macOS 和 Windows 上都会跑。
- 改了接力协议或入口，再用真实 harness 跑一次相关的评估，结果提交到 `evals/results/`。
- 公开仓库只放脱敏后可以迁移的内容：不写真实人名、内部链接、客户和账号信息。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)。
