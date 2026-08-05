# Wade AI — AI 使用沉淀知识库

> **开发任何新项目之前,先读本仓库**——这里是 Wade 使用 AI 协作开发的完整背景知识。

## 这是什么

Wade 在使用 AI(Claude / GPT / DeepSeek / Hermes / Copilot 等)进行软件开发的实践中沉淀出的**方法论与体系**。与其他项目不同,本仓库**不包含产品代码**,只包含可复用的 AI 协作知识与规范。

## 读取顺序

| 顺序 | 文件 | 内容 |
|---|---|---|
| 1 | `.ai/runtime/AI_INSTRUCTION_V2.md` | **Runtime Operating Model 2.0(当前生效)**:Goal-First 哲学、Context Loading、Task Lifecycle、SDD、Planning、Skill 系统、动态 Subagent 模型、Execution / Verification(Iron Law) / Review / Memory / Self-Evolution Loops、Runtime Governance。**新项目直接按 v2 起步。** |
| 2 | `AI_DEV_INSTRUCTION.md` | v1(legacy 兼容):AI-Native 开发体系总纲——SDD 流程、AIOS 目录、多角色 lane 模式、质量门禁、镜像源、运维坑。新项目 15 分钟起步的原始模板。 |
| 3 | `ponytail.md` | **开发哲学**:最短可行实现、YAGNI、根因修复、证据先于断言。所有 AI 协作遵守此哲学。 |
| 4 | `wade-ai-workspace` 仓库 | 完整落地范例:AIOS 组织层(`.ai/`)、specs、harness regression、Dashboard 等,可参考其结构。 |

## 升级说明(v1 → v2)

- v2 是一次 **Runtime 架构升级**,不是增量补丁:把 Agent Prompt 升级为 **AI 软件工程运行时(Organization Runtime)规范**。
- v2 吸收 [obra/superpowers](https://github.com/obra/superpowers) 的思想:Skill 化(skill 是可执行的组织能力,1% 可能相关就 MUST invoke)、Brainstorm→Spec→Plan→Execute→Review 流程、动态 Subagent(每任务 fresh agent + task review + 终审 + fix loop + ledger)、Verification Loop(Iron Law:无新鲜证据不宣称完成)。
- 保留 AIOS 原有资产:Memory / Knowledge / Harness / Spec Driven Development / 镜像源。
- 补充:Goal-driven Loop、Self-improvement Loop、Runtime Governance。
- **向后兼容**:v1 保留可读,新项目用 v2,存量项目渐进迁移。

## 在新项目中使用

```bash
# 方式一:clone 知识库到本地,供 AI 读取
git clone https://github.com/wadefengx/wade-ai.git ~/ai-kb/wade-ai

# 方式二:直接把核心文件复制进新项目
cp ~/ai-kb/wade-ai/.ai/runtime/AI_INSTRUCTION_V2.md <新项目>/.ai/runtime/AI_INSTRUCTION_V2.md
cp ~/ai-kb/wade-ai/AI_DEV_INSTRUCTION.md <新项目>/AI_DEV_INSTRUCTION.md   # v1,可选
cp ~/ai-kb/wade-ai/ponytail.md <新项目>/.ai/skills/common/ponytail.md
```

然后按 `AI_INSTRUCTION_V2.md` 第 5-8 节(Task Lifecycle → Discovery → Spec → Plan)执行即可。

## 目录

- `.ai/runtime/AI_INSTRUCTION_V2.md` — **Runtime Operating Model 2.0(当前生效)**
- `AI_DEV_INSTRUCTION.md` — v1:AI-Native 开发体系(legacy,向后兼容)
- `ponytail.md` — Ponytail 开发哲学(skill 格式)
- `AGENTS.md` — 本知识库的 AI 读取入口

## 维护

- 沉淀原则:一个可复用的做法在项目中重复出现 2 次以上 → 提炼进本仓库(skill 化)。
- 更新后保持文件简洁(表格/清单风格),不写长篇叙事。
