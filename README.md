# Digital Brain

一个由 LLM 维护的个人知识库（wiki）——基于 Andrej Karpathy 的 **llm-wiki** 模式 + Obsidian Second Brain Guide 的 IPOF 工作区层。

LLM 不在查询时临时检索资料，而是把知识**增量编译进一个持久化、持续复利的 wiki**：录入资料、回答问题、健康检查，都由它按一套纪律化的规则完成。人负责选资料、定方向、问好问题；LLM 负责所有记账式维护（摘要、交叉引用、矛盾标注、一致性）。

> 理论出处见 `inputs/llm-wiki-zh.md`（中译）与 `inputs/llm-wiki.md`（原文）。

## 四层模型

```
Schema 层（CLAUDE.md）    宪法·纯运行时规则·Agent 无关
Wiki 层（LLM 维护）        提炼的知识（大脑）
Raw 层（只读来源）         不可变的外部快照·事实来源
Workspace 层（人+LLM）     活的工作区·IPOF·在 vault 外登记
```

## 仓库内容

| 路径 | 作用 |
|------|------|
| `outputs/CLAUDE-schema.md` | **可部署的 Schema（宪法）**——纯运行时规则。复制到你的 vault 根目录、改名 `CLAUDE.md` 即用。 |
| `outputs/Digital Brain 落地方案.md` | 完整落地方案（给人看：为什么、怎么部署、数据源、路线图）。 |
| `outputs/实操流程-ClaudeCode+Obsidian.md` | 日常实操流程与技巧。 |
| `outputs/workspaces.md` | 外部工作区登记表模板。 |
| `process/` | 各版本 Schema 设计说明（决策记录）。 |
| `inputs/` | 理论原典与参考资料。 |

## 快速开始

1. 复制 `outputs/CLAUDE-schema.md` 到你的知识库目录，改名为 `CLAUDE.md`。
2. 在该目录用 Claude Code（或其他 Agent）启动，让它按 §2 创建目录骨架。
3. （可选）用 Obsidian 打开同一目录作为 vault，边做边看。
4. 按下面的「定制点」把模板改成你自己的。

详细步骤与取舍见 `outputs/Digital Brain 落地方案.md`。

## 定制点（模板 → 你的实例）

Schema 的通用规则照用，只有以下几处按你的领域替换：

1. **§2 目录树** —— 是示例结构。`raw/` 子目录（`wechat/`、`personal/`、`company/`…）按你实际的数据源与领域增删；`raw/` 只有分类原则固定（按数据源边界分类），具体子目录自由。
2. **§5 领域标签** —— 表中「领域」一行是占位（`领域A`/`领域B`），换成你自己的工作/专业/兴趣领域。
3. **§6 录入策略表 · §7 聚合源约定** —— 含数据源适配示例（如微信导出、微信群）。用不到的整行删除；有新数据源照样式加一行。

其余（权限模型、录入/摄取/查询/沉淀 SOP、frontmatter、Lint、安全、工作区）无需改动。

## 理论出处

- Andrej Karpathy, *LLM Wiki*（三层：Schema / Wiki / Raw）
- Claude + Obsidian Second Brain Guide（IPOF 工作区层为其所加，非 llm-wiki 原典）
