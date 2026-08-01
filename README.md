# Wade AI — AI 使用沉淀知识库

> **开发任何新项目之前,先读本仓库**——这里是 Wade 使用 AI 协作开发的完整背景知识。

## 这是什么

Wade 在使用 AI(Claude / GPT / DeepSeek / Hermes / Copilot 等)进行软件开发的实践中沉淀出的**方法论与体系**。与其他项目不同,本仓库**不包含产品代码**,只包含可复用的 AI 协作知识与规范。

## 读取顺序

| 顺序 | 文件 | 内容 |
|---|---|---|
| 1 | `AI_DEV_INSTRUCTION.md` | **AI-Native 开发体系总纲**:SDD 流程、AIOS 目录、多角色 lane 模式、质量门禁、镜像源、运维坑。新项目 15 分钟起步。 |
| 2 | `ponytail.md` | **开发哲学**:最短可行实现、YAGNI、根因修复、不建无用抽象。所有 AI 协作遵守此哲学。 |
| 3 | `wade-ai-workspace` 仓库 | 完整落地范例:AIOS 组织层(`.ai/`)、specs、harness regression、Dashboard 等,可参考其结构。 |

## 在新项目中使用

```bash
# 方式一:clone 知识库到本地,供 AI 读取
git clone https://github.com/wadefengx/wade-ai.git ~/ai-kb/wade-ai

# 方式二:直接把核心文件复制进新项目
cp ~/ai-kb/wade-ai/AI_DEV_INSTRUCTION.md <新项目>/AI_DEV_INSTRUCTION.md
cp ~/ai-kb/wade-ai/ponytail.md <新项目>/.ai/skills/common/ponytail.md
```

然后按 `AI_DEV_INSTRUCTION.md` 第 2 节(新项目启动步骤)执行即可。

## 目录

- `AI_DEV_INSTRUCTION.md` — AI-Native 开发体系(通用模板)
- `ponytail.md` — Ponytail 开发哲学(skill 格式)
- `AGENTS.md` — 本知识库的 AI 读取入口

## 维护

- 沉淀原则:一个可复用的做法在项目中重复出现 2 次以上 → 提炼进本仓库。
- 更新后保持文件简洁(表格/清单风格),不写长篇叙事。
