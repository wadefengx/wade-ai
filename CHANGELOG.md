# 变更记录

## 2026-11-27 · 入口 v3

- 结构扁平化：`.ai/playbooks` 和 `.ai/examples` 移到根目录下的 `playbooks/` 和 `examples/`；v1、Runtime v2 和当时的升级记录移到 `archive/`。
- AGENTS.md 增加：授权和沟通的默认值，行为保持型改动的验收要求，提交前逐个核对文件，多 Agent 接力和共享工作区的规则。
- 新增 playbook：[复杂任务](playbooks/complex-work.md)（取代 Runtime v2）、[评审与修复循环](playbooks/review.md)、[接力与交接](playbooks/handoff.md)。
- 验证与回归增加：行为保持型变更和跨平台两行，「什么能证明什么」的证据表，常见误判。
- SIM：方法里加了编号、验证前预期的写法、迁移判断、读旧记录的步骤，以及项目里的 RSI；新增共享记录 [memory/sim.md](memory/sim.md)，把这次对规则的改动作为 SIM-002 到 SIM-005 记下来，等待实测回填。
- Ponytail 成为唯一版本，补上「先理解再选做法」和「留一个可运行的检查」。
- 多 Agent 接力：任意 harness 都能接力。接力协议写在 `.ai/CONTEXT.md` 开头（[模板](templates/CONTEXT.md)），只依赖文件和 git；发现方式有三层：开场一句话、项目指令文件、用户级入口。Codex 和 Copilot CLI 三棒实测，见 [SIM-003](memory/sim.md#sim-003)。
- 新增脚本：`install.sh` 把入口挂到已知工具，也可以带路径参数接入任意工具；`relay-init.sh` 生成接力板；`check.py` 做文档自检，CI 也会跑。

## 2026-08-05 · Runtime v2

见[归档的升级记录](archive/2026-08-05-runtime-v2-changelog.md)。
