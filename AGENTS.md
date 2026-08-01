# Wade AI Knowledge Base — AI Agent Entry

本仓库是 Wade 的 AI 使用沉淀知识库(不含产品代码,只含可复用方法论)。

## Context loading order

1. `README.md` — 仓库索引与读取顺序。
2. `AI_DEV_INSTRUCTION.md` — AI-Native 开发体系总纲(SDD 流程 / AIOS 目录 / lane 模式 / 质量门禁 / 镜像源 / 运维坑)。
3. `ponytail.md` — 开发哲学(最短可行实现 / YAGNI / 根因修复)。

## 使用场景

- **开始新项目**:读取 `AI_DEV_INSTRUCTION.md` §2(新项目 15 分钟起步),复制核心文件到新项目。
- **开发中**:遵守 ponytail 哲学;按 instruction 的 lane 模式拆分任务;完成后把可复用经验回流本仓库。

## 沉淀规则

- 重复出现 2 次以上的可复用做法 → 提炼进本仓库。
- 文档保持简洁(表格/清单),不写长篇叙事。
- 完整落地范例见 [wadefengx/wade-ai-workspace](https://github.com/wadefengx/wade-ai-workspace)(AIOS 组织层 + specs + harness + Dashboard)。
