# 接力与交接

适用场景：同一个需求先后交给不同的 Agent 或 harness，或者需要跨会话、等上游、预计超过一天。工具可以是任意的：Codex、Claude Code、Copilot、OpenCode、DeepSeek Harness，或者以后出现的新工具。

对话上下文会被压缩，关掉 harness 就没了，能留下来的只有文件和 git 历史。所以接力只靠项目里的一个 Markdown 文件 `.ai/CONTEXT.md` 加上 git。任何能读写文件、能运行 git 的 Agent，读完它就能接着干。〔[SIM-003](../memory/sim.md#sim-003)〕

## 通用的前提

- **协议写在文件里。** 接力板开头自带一段「接力协议」，Agent 不需要装 wade-ai，也不需要任何配置，读到这个文件就知道怎么接、怎么更新。
- **只用文件和 git。** 不依赖某个工具特有的东西，比如 hooks、斜杠命令、会话恢复、内置的 todo 或 memory、MCP。这些都可以用，但用完要把结论写回接力板，因为下一个 harness 读不到它们。
- **身份用自由文本。** 每一棒写成「<harness> / <模型>」，不需要事先登记，新工具也一样。

## 怎么让 Agent 读到

三层，从下往上覆盖，任何一层生效就够了：

| 层 | 做法 | 覆盖哪些工具 |
| --- | --- | --- |
| 开场一句话 | 「先读 `.ai/CONTEXT.md`，按里面的协议接着做。」 | 任何能读文件的 Agent，保证能接上 |
| 项目指令文件 | 在项目已有的 Agent 指令文件里加一行，见下面 | 读项目 `AGENTS.md` 的工具（多数 harness 支持这个开放约定）。只读 `CLAUDE.md` 这类文件的，把同一行放进去 |
| 用户级入口 | wade-ai 的 [AGENTS.md](../AGENTS.md) 已经写了「有 `.ai/CONTEXT.md` 就先读」，按 [README · 接入](../README.md#接入)挂上 | 本机已接入的工具。只是省事，不是必需的 |

项目指令文件里加的那一行：

```markdown
- 如果存在 `.ai/CONTEXT.md`，开工前先读它，按开头的接力协议接着做，并随进度更新。
```

这一行会进项目的 git。不想提交时就跳过这一层，靠另外两层。

**开一个接力板：** 在项目根目录运行 `~/ai-kb/wade-ai/scripts/relay-init.sh "<需求名>"`，它会用[模板](../templates/CONTEXT.md)生成 `.ai/CONTEXT.md`，并把 `/.ai/CONTEXT.md` 和 `/.ai/notes/` 写进 `.git/info/exclude`，不改团队的 `.gitignore`，也不影响项目要提交的其他 `.ai/` 文件。没有 wade-ai 的 Agent 直接照下面的示例手写一份。项目已经有自己的 `.ai/` 结构或交接文件时，沿用项目的，只补缺少的栏目。

**接力板在哪里。** 它不进 git，只在创建它的那个目录里。所以：

- 找不到接力板时，先看主工作树（`git worktree list` 的第一行）和上层工作区目录，确认都没有再新建，避免出现两块各写各的板。
- 几个仓库一起改时，把接力板放在上层的工作区目录里，在「基线」里列出每个仓库，并且从这个目录启动 harness。不少 harness 只能读写启动目录以内的文件。各仓库的指针那一行写实际路径，比如 `../.ai/CONTEXT.md`。
- 要跨机器，或者交给在云端、新 clone 里运行的 Agent 时，本地文件带不过去。这时把接力板提交到任务分支上：它在 exclude 里，要用 `git add -f .ai/CONTEXT.md`（链接到的 `.ai/notes/` 文件也一起加），再用 `git ls-files .ai` 确认已经进了 git。合并前删掉。

## 每一棒怎么做

**开工**

1. 读完 `.ai/CONTEXT.md`。
2. 用 git 核对：`git status`、`git log --oneline -10`，必要时看 `git diff`。文件里写的和 git 对不上时，以 git 和 CI 为准，并在日志里写明差异。
3. 「进度」里有别的 Agent 留下的「进行中」，而接力日志里没有它的「已收尾」记录：它可能还在跑，也可能被关掉了。先问 Wade；问不到时看日志最后的时间和工作区里没提交的改动，确认已经中断了再接手，并在日志里写明。
4. 在要做的那一项上标「进行中」，写上 harness、模型和时间。

**做的过程中**

- 每完成一项：验证 → commit（有授权时）→ 把这一项改成已完成，附 commit SHA → 写一条接力日志。这样即使 harness 被突然关掉，最多丢一项的进度。
- Wade 在这一棒里给出的新约定和纠正，马上写进「约定」。说过两次的事一定要在那里。

**收尾**

- 把这一棒里 Wade 的决定和纠正逐条过一遍，确认每一条都写进了「约定」「进度」或「当前状态」，或者写明为什么不写。
- 更新「当前状态」，写一条接力日志，去掉自己的「进行中」标记。
- 没提交的改动要在「当前状态」里写明文件和原因。
- 遇到上一棒的误判、规则缺口或返工，在日志里写一句，满足条件时按 [SIM](sim.md) 记录。

## 规则

- 「目标」到「当前状态」这几节加起来不超过 40 行，只写现在的情况。过程和长篇记录放进 `.ai/notes/YYYY-MM-DD-<主题>.md`，这里只留链接。
- 授权只保留当前有效的一份，写明日期。授权变了就直接替换，不在后面追加。
- 接力日志最新的写在最上面，每条写时间、harness / 模型、做了什么、怎么验证的、下一棒要注意什么，一行到 6 行。超过 15 条时，把旧的移到 `.ai/notes/relay-archive.md`。
- 不写密钥、token、密码和个人信息，只写它们存在哪里。
- 文件只是索引，代码、提交和 CI 状态以 git 和 CI 平台为准。「基线」里不抄 HEAD SHA，最新提交看 `git log`；只在「进度」的已完成项上附当时的 SHA。

## 填好的示例

空白模板在 [templates/CONTEXT.md](../templates/CONTEXT.md)。下面是 Codex 改完 header、Copilot 改完 nav bar，交给第三棒（比如 OpenCode）时的样子，开头的接力协议省略了：

```markdown
# 站点改版 · 接力板

> **接力协议** …（同模板）

## 目标
- header、nav bar 和 footer 改版
- 验收：三个组件用同一套 token；桌面和窄屏手测通过；单测和构建通过
- 不改：路由和导航链接的目标地址

## 约定
- 授权（11-27）：可以本地 commit 和 push 到 feat/site-redesign；新开 PR 先问 Wade
- 样式沿用 header 的 token；用 3000 端口验证

## 进度
- [x] 改 header · Codex / gpt · 11-27 · a1b2c3d
- [x] 改 header 里的 nav bar · Copilot CLI / claude · 11-27 · d4e5f6a
- [ ] 改 footer

## 当前状态（更新于 11-27 16:05）
- 基线：feat/site-redesign · 未开 PR
- 未提交：无
- 下一步：改 `src/components/Footer.tsx`，复用 `LinkList`
- 等待：无
- 未验证：Safari 没测，本机没有

## 接力日志（最新在上）

### 11-27 16:05 · Copilot CLI / claude · 已收尾
- 做了：nav bar 改成横向菜单加窄屏折叠，`src/components/Header/Nav.tsx`，commit d4e5f6a
- 验证：单测通过；3000 端口手测桌面和窄屏通过；构建通过
- 注意：footer 和 nav 共用 `LinkList`，改 footer 时别动它的 props
- 下一棒：改 footer，见「进度」第 3 项

### 11-27 14:30 · Codex / gpt · 已收尾
- 做了：header 改版，commit a1b2c3d
- 验证：单测和构建通过
- 下一棒：nav bar
```

## 多仓库工作区

多个仓库一起改，或者任务规则很多时，可以在工作区目录里另放一份 `AGENT.md`，写不常变的内容：仓库表（路径、分支、用途）、任务特有的规则和常用命令。CONTEXT.md 的开头链接到它。
