# Wade AI

这里是 Wade 和 AI Agent 协作开发的约定。开新项目、换 Agent，或在几个 harness 之间接力时，Agent 读一遍 [AGENTS.md](AGENTS.md)，就知道怎么开工、哪些事可以直接推进、哪些要先问 Wade，以及验证到什么程度才算交付。

## 接入

### 本机一次性安装

```bash
git clone https://github.com/wadefengx/wade-ai.git ~/ai-kb/wade-ai
~/ai-kb/wade-ai/scripts/install.sh
```

各 harness 基本都有一个「用户级指令文件」，每次会话都会加载。接入就是让这个文件指向 wade-ai 的 `AGENTS.md`，任何工具都一样。

- 不带参数运行 `install.sh`，会处理下表里本机已安装的工具。
- 其他工具，找到它的用户级指令文件路径，运行 `install.sh <路径>` 建软链。工具只支持导入语法的（像 Claude 的 `@路径`），就手动加一行导入。
- 工具没有用户级入口时，可以靠项目里的 `AGENTS.md`，或者开场说一句话，见[接力与交接](playbooks/handoff.md#怎么让-agent-读到)。

重复运行没有副作用。目标位置已经有别的文件时，脚本只提示，不会覆盖。

| 已知工具 | 用户级入口 | 接法 |
| --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | 一行 `@<wade-ai 路径>/AGENTS.md` 导入 |
| Codex | `~/.codex/AGENTS.md` | 软链 |
| Copilot CLI | `~/.copilot/instructions/wade-ai.instructions.md` | 软链。`@` 导入不支持 `~/` 和绝对路径 |
| OpenCode | `~/.config/opencode/AGENTS.md` | 软链 |
| DeepSeek Harness | `~/.dsh/AGENTS.md`（或 `$DSH_HOME`） | 软链 |

这张表只是现在已知的路径，以各工具的文档为准。更新：`git -C ~/ai-kb/wade-ai pull --ff-only`。软链指向的是仓库里的文件，所以拉取后各工具就会读到新内容。

**接入自检。** 在一个空目录里启动工具，问「按 wade-ai，新开 PR 之前要不要先问 Wade？」，回答「要」就说明已经接上。新工具、工具升级或换机器后再做一次。

**只对某个项目有效的指令**（门禁脚本、测试框架、覆盖率要求）放在那个仓库里，例如 `AGENTS.md` 或 `.github/instructions/*.instructions.md`，并用 `applyTo` 限定文件范围。不要放进用户级入口，否则在其他项目里也会生效。

### 多个 Agent 接力

同一个需求可以先用 Codex 改 header，关掉后用 Copilot 改 nav bar，再交给 OpenCode 或任何别的 harness 改 footer。接力只靠项目里的 `.ai/CONTEXT.md` 和 git。

- 文件开头自带接力协议，接手的 Agent 读到它就知道前面谁做了什么、自己接哪一项、做完怎么更新，不需要为某个工具单独配置。
- 开一个接力板：在项目根目录运行 `~/ai-kb/wade-ai/scripts/relay-init.sh "<需求名>"`。
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
| [scripts/](scripts/) | `install.sh` 接入，`relay-init.sh` 开接力板，`check.py` 文档自检 |
| [archive/](archive/) | 已归档的 [v1](archive/v1-ai-dev-instruction.md)、[Runtime v2](archive/runtime-v2.md) 和当时的[升级记录](archive/2026-08-05-runtime-v2-changelog.md) |

## 维护

- 改规则就是改 Agent 的 harness。改之前在 [memory/sim.md](memory/sim.md) 写下理由和预期，在规则行末用 `〔SIM-xxx〕` 回链，下次用到时回填实测结果。
- 提交前运行 `python3 scripts/check.py`，检查相对链接、锚点和入口文件的行数。CI 也会跑同样的检查。
- 公开仓库只放脱敏后可以迁移的内容：不写真实人名、内部链接、客户和账号信息。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)。
