# Wade AI

Wade 的 AI 协作开发约定。开新项目或换 Agent 时，把本仓库的 [AGENTS.md](AGENTS.md) 和目标仓库的约定一起读。按任务打开入口里相关的文档。

## 新项目怎么接入

一次性任务可以直接把这段发给 Agent：

> 开工前读 https://github.com/wadefengx/wade-ai/blob/main/AGENTS.md，再按本项目的约定和本轮任务执行。用实际验证结果说明交付状态。

想让后续会话自动接着用，把下面这段加进**新项目根目录的 `AGENTS.md`**。已有文件时追加到合适位置。

```markdown
## Wade 的协作约定

开工前先读 Wade AI 的 AGENTS.md，并按任务需要打开其中的链接。
若本项目固定了版本，使用该版本。其他情况使用近期同步的
~/ai-kb/wade-ai/AGENTS.md，或读取
https://github.com/wadefengx/wade-ai/blob/main/AGENTS.md 。
本项目的规则和当前任务决定实际改动范围、验收命令和交付权限。
```

如果 Agent 使用自己的项目指令文件，把同一段加进它会读取的文件。

本机可用 `git clone https://github.com/wadefengx/wade-ai.git ~/ai-kb/wade-ai` 安装一次。跟踪远端默认分支时，用 `git -C ~/ai-kb/wade-ai pull --ff-only` 同步。

需要跨机器固定版本或离线使用时，把指定提交的快照放进项目，再把上面的引用指向 `.ai/wade-ai/AGENTS.md`。从目标项目根目录执行：

```bash
mkdir -p .ai/wade-ai
git -C ~/ai-kb/wade-ai archive HEAD | tar -x -C .ai/wade-ai
```

## 按任务读

| 什么时候 | 文件 |
| --- | --- |
| 开工前 | [AGENTS.md](AGENTS.md) |
| 修 bug、做迁移、发包、看 CI 或验收 UI | [验证与回归](.ai/playbooks/verification.md) |
| Agent 反复犯错、验证漏项或经验需要迁移 | [SIM](.ai/playbooks/sim.md) |
| 想看验证如何覆盖旧数据和真实入口 | [Tags 回归案例](.ai/examples/tags-regression.md) |
| 需要完整 spec、计划、分工和接力 | [Runtime v2](.ai/runtime/AI_INSTRUCTION_V2.md) |
| 需要取舍依据或维护旧项目 | [Ponytail](ponytail.md) · [v1](AI_DEV_INSTRUCTION.md) |

Runtime v2 最初引入时的背景见[历史变更记录](.ai/changelog/2026-08-05-runtime-v2.md)。完整的目录和 harness 示例见 [wade-ai-workspace](https://github.com/wadefengx/wade-ai-workspace)。
