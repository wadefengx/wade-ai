# Wade AI Knowledge Base — AI Agent Entry (Runtime v2)

本仓库是 Wade 的 AI 使用沉淀知识库(不含产品代码,只含可复用方法论)。

## Context loading order

1. `README.md` — 仓库索引与读取顺序。
2. `.ai/runtime/AI_INSTRUCTION_V2.md` — **Runtime Operating Model 2.0(当前生效)**:Mission / Goal-First / Context Loading / Task Lifecycle / SDD / Planning / Skill 系统 / 动态 Subagent / Execution·Verification·Review·Memory·Self-Evolution Loops / Runtime Governance。
3. `AI_DEV_INSTRUCTION.md` — v1(legacy,向后兼容):AI-Native 开发体系总纲(SDD 流程 / AIOS 目录 / lane 模式 / 质量门禁 / 镜像源 / 运维坑)。新项目按 v2 起步,v1 保留可读。
4. `ponytail.md` — 开发哲学(最短可行实现 / YAGNI / 根因修复 / 证据先于断言)。

## 使用场景

- **开始新项目**:读 `.ai/runtime/AI_INSTRUCTION_V2.md`(Runtime Operating Model 2.0)——Goal First,Spec 先行,Plan bite-size,Subagent 执行,Verification 出证据,Memory/Skill 回流。
- **开发中**:遵守 ponytail 哲学;任何任务先查 skill(1% 可能相关就 MUST invoke);完成后把可复用经验回流本仓库(重复 2 次以上 → 提炼)。

## 沉淀规则

- 重复出现 2 次以上的可复用做法 → 提炼进本仓库(skill 化:SKILL.md + examples/templates/scripts)。
- 文档保持简洁(表格/清单),不写长篇叙事。
- 完整落地范例见 [wadefengx/wade-ai-workspace](https://github.com/wadefengx/wade-ai-workspace)(AIOS 组织层 + specs + harness + Dashboard)。
