# Digital Brain

一个由 LLM 持续维护、持久复利的个人知识库（wiki）——基于 Andrej Karpathy 的 **llm-wiki** 模式，安装/访谈流程借鉴 Yarchi 的 Second Brain Guide。

LLM 不在查询时临时检索资料，而是把知识**增量编译进一个持久化、相互链接的 wiki**：摄入资料、回答问题、健康检查，全由它按一套纪律化的规则完成。人负责选资料、定方向、问好问题；LLM 负责所有记账式维护（摘要、交叉引用、矛盾标注、一致性）。

> **不绑定某个 AI**——本质是一套规则（Schema），你用 Claude Code、Codex 或别的 Agent 都行，这正是 llm-wiki 的原意。
> 理论出处见 `inputs/llm-wiki-zh.md`（中译）/ `inputs/llm-wiki.md`（原文）。

## 三层模型

```
Schema 层    宪法 · 纯运行时规则 · Agent 无关（部署为 CLAUDE.md / AGENTS.md）
Wiki 层      LLM 提炼并维护的知识
Raw 层       只读 · 不可变的外部来源（事实来源）
```

## 快速开始：一句话搭建

克隆本仓库、在其中用你的 AI Agent（如 Claude Code）打开，粘这一句：

> **「读 `outputs/Schema.md` 和 `outputs/digital-brain-setup` skill，帮我在 `~/digital-brain` 搭建我的 Digital Brain。」**

Agent 会：脚手架目录 → 把 Schema 装成 vault 的规则文件 → **访谈你**（领域、数据源、目标）做定制 → 建好你的画像页 → 提示"可以开始摄入了"。

> Claude Code 会自动发现 `outputs/digital-brain-setup` skill；其他 Agent 直接按 skill 里的步骤走即可。

## 仓库内容

| 路径 | 给谁 | 作用 |
|------|------|------|
| `outputs/Schema.md` | AI | **可部署的宪法**——纯运行时规则，装成 vault 根的 `CLAUDE.md`/`AGENTS.md`。 |
| `outputs/digital-brain-setup/` | AI | 一句话搭建的安装 skill。 |
| `README.md` | 人 | 本文。 |
| `inputs/` | 参考 | 理论原典（Karpathy / Yarchi）。 |
| `process/` | 参考 | 各版本 Schema 设计说明（决策记录）。 |

## 日常怎么用（搭好之后）

- **摄入**：资料丢进 `raw/`，说"摄入这份" → 转成标准 md，暂停给你确认。
- **汲取**：确认后说"汲取" → 提炼进 wiki、更新交叉引用。
- **查询**：直接问 → 从 wiki 合成带引用的答案；好答案归档回 wiki。
- **体检**：说"lint" → wiki 健康检查（断链、孤岛、矛盾、过期…）。

## 装好后可按自己调的地方

搭建访谈会帮你填好；你随时可在 vault 的规则文件里再改：
1. **§5 领域标签** —— 换成你的工作/专业/兴趣领域。
2. **§2 raw/ 子目录** —— 按你的实际数据源增删（分类原则固定、子目录自由）。
3. **§6 摄入策略表** —— 只留你用得上的数据源适配行。

## 理论出处

- Andrej Karpathy, *LLM Wiki*（三层：Schema / Wiki / Raw）— `inputs/llm-wiki*.md`
- Yarchi（X）, *Claude + Obsidian Second Brain Guide*（安装/访谈法借鉴自此）— `inputs/claude-obsidian-second-brain-guide*.md`
