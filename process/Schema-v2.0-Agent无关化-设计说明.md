# Schema v2.0 设计说明 — Agent 无关化 + 去工作区层 + 一句话搭建

> **状态**：✅ 已实施（2026-07-14，Schema v2.0）
> **日期**：2026-07-14
> **影响文件**：`outputs/CLAUDE-schema.md` → **`outputs/Schema.md`**（v1.4 → v2.0）；新增 `outputs/digital-brain-setup/SKILL.md`；重写 `README.md`；删除 `落地方案.md` / `workspaces.md` / `实操流程.md`
> **一句话**：把 schema 从"Claude 专属、四层、录入/摄取"收敛为 **Agent 无关、纯 llm-wiki 三层、术语更准**的规则文件，并让别的用户**粘一句话就能让任意 AI 搭好自己的 Digital Brain**。

---

## 一、动机（用户决定）

1. **不绑定 Claude**——"这只是个规则，用户用哪个 AI 工具按理说是自由的，这也符合 llm-wiki"。llm-wiki 原文本就说"copy paste 到你自己的 LLM Agent（Codex / Claude Code / OpenCode…）"。
2. **回归简洁**——README 给人看、其余给 AI 看；删掉人看的规划文档（落地方案/实操流程）与工作区层，聚焦"一句话搭建"。
3. **术语更准**——"录入 + 摄取"用词不合理，改 **摄入 + 汲取**（合称仍叫摄取）。
4. **命名保留**——讨论过 `digital-brain`（比喻 vs 机制、红海可发现性、已部署迁移成本）后，决定保留。

---

## 二、主要改动

### A. Agent 无关化
- 文件重命名 `CLAUDE-schema.md` → **`Schema.md`**；标题 `# CLAUDE.md` → `# Schema`，副标题加"Agent 无关"，说明"部署为你的 Agent 规则文件（Claude→CLAUDE.md、Codex→AGENTS.md、其他→各自约定）"。
- 去硬耦合：§1/§2 的"本文件（CLAUDE.md）"泛化为"本 Schema（部署后的 CLAUDE.md/AGENTS.md）"；§12 config 动作文件名泛化；§15 的 `.claude/settings.json` deny 降级为"Claude Code 示例"，通则改为"用你的 Agent 的权限层"。
- 保留的 Claude 字样均为**有意的示例/清单**（§6 偏好持久化的多 Agent 清单、§15 示例、目录树注释）。

### B. 移除工作区层（§16）→ 纯 llm-wiki 三层
- 删除整个 §16（工作区 SOP / IPOF / workspaces.md 规范 / 沉淀门）+ `workspaces.md` 文件。
- 连带清理：§1 删"工作区你可以干活"权限块与"workspaces.md 格式"条；§2「四层职责」→「三层职责」（raw / wiki / 本文件）；§12 删 `project` 日志动作；§15 删"位置即锁=工作区外置"引用；§6④ 删"想持续干活的是工作区—见 §16"括注。
- 理据：工作区(IPOF)本是 Second Brain Guide 扩展、非 Karpathy 原典；移除后回到 llm-wiki 三层，最贴合"一句话搭建"。

### C. 术语：录入/摄取 → 摄入/汲取/摄取
- **录入 → 摄入**（外部文件 → raw/.md，含冻结）：全文 18 处。
- **§7 摄取 SOP → 汲取 SOP**（raw/.md → wiki）：§7 标题、§6④"继续汲取/进入汲取"、§10"与汲取的区别"。
- **"摄取" = 两步合称**（做完摄入+汲取）：保留于 log `ingest（摄取）`、§14"一次大型摄取完成后"。
- 细节：§6④"sha256、摄取完成即冻结"→**摄入**完成（冻结属摄入尾）。

### D. raw/ 结构（用户手改）+ 下游对齐
- 用户手动把 §2 raw/ 树改为 `wechat/ + project/ + assets/`（本设计说明不动其树）。
- 对齐下游引用到该结构：§2 附件镜像示例（company/articles → project/wechat）、§4 溯源示例（articles → project）、§6 路由（company/personal/bookmarks/articles → project/wechat/assets）。

### E. outputs 精简 + 一句话搭建 skill
- **删**：`Digital Brain 落地方案.md`、`workspaces.md`、`实操流程-ClaudeCode+Obsidian.md`（人看的规划/上手职责由 README + skill 承接）。
- **新增** `outputs/digital-brain-setup/SKILL.md`：一句话触发 → 脚手架 vault → 装 Schema 为 Agent 规则文件 → **访谈定制**（仿 Second Brain Step 5，一次一问：领域/数据源/目标）→ 建 persona 页 → 提示"可以开始摄入了 + 怎么用"。
- **README 重写**：三层模型、一句话安装、日常用法、装后可调点、Karpathy/Yarchi 署名；去所有指向已删文件的死链。角色分工：**README 给人，Schema/skill 给 AI**。

---

## 三、验证

- grep `Schema.md`：`工作区`/`§16`/`workspaces`/`录入`/`落地方案` 残留 **全 0**；`摄取` 仅 2 处（均合称义）；`汲取` 5 处到位。
- 活跃文件（README / Schema / SKILL）无对已删文件或旧名 `CLAUDE-schema` 的死链。
- git 识别重命名 `CLAUDE-schema.md => Schema.md (73%)`，历史连续。
- Schema.md 465 行（删 §16 后 −59）。

---

## 四、备注

- v1.4 设计说明（`Schema-v1.4-开源通用化-设计说明.md`）描述的是本次之前的状态（含 workspaces、录入/摄取、CLAUDE-schema.md 名），作为历史决策记录保留，不回改。
