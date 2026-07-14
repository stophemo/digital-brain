# Schema v1.2 设计说明 — 工作区分层

> **状态**：✅ 已实施（2026-07-13，Schema v1.2）
> **日期**：2026-07-13
> **影响文件**：`CLAUDE-schema.md`（宪法，新节定为 §16）、`Digital Brain 落地方案.md`、新增 `workspaces.md`
> **一句话**：把"活的工作区"从只读的 `raw/` 里请出来，独立成层——**所有项目工作区都放 vault 外、逐个登记进 `workspaces.md`**，`raw/` 回归纯粹的不可变事实来源。

> **修订（2026-07-13，讨论中）**：初版设计为"两类工作区（vault 内 `projects/` + 外部注册）"。后确认 Claude Code 会**向上递归加载父级 `CLAUDE.md`**——在 vault 内 `projects/{项目}` 启动 claude 会连带加载整个 Schema，串入 wiki 维护职责。故**取消 vault 内 `projects/` 层**，所有工作区改为 vault 外任意路径、逐个登记（外部路径的祖先目录里没有 vault Schema，天然隔离，无需 `claudeMdExcludes`）。以下正文 §3.1/3.2/3.3/3.4 已按本修订更新。

---

## 一、问题

### 1.1 现有 Schema 自相矛盾

当前 `CLAUDE-schema.md` 对 `raw/` 的定位在三处互相打架：

| 位置 | 说法 |
|------|------|
| §1 权限 | "raw/ ——只读。这是**不可变**的事实来源"、"**你不能动**" |
| §2 目录结构 | "raw/ ← **不可变**原始资料（只读）" |
| §6④ 录入 SOP | "需要修改的话**直接改 raw/ 下的文件**，改完告诉我'继续'" |
| §14 Lint #8 | "raw/ 漂移（sha256 与存储值不匹配 → 来源已变更）"——把 raw 变化当**异常**报警 |

§1/§2 说绝对不可变，§6 却开了"录入窗口期可编辑"的口子，§14 又假设摄取后不该变。三者没对齐。

### 1.2 根因：两套哲学被塞进同一个抽屉

- **llm-wiki（Karpathy）**：`raw = 不可变事实来源`，是整个 wiki 可信度的地基；wiki 从 raw *派生*。原文 line 29 明确："These are immutable — the LLM reads from them but never modifies them. **This is your source of truth.**" llm-wiki **没有"项目/工作区/产出成品"概念**，纯知识累积器。
- **Second Brain Guide（IPOF）**：每个项目是**独立工作区**（Inputs/Process/Outputs/Feedback），各自带 CLAUDE.md，工作时"**只打开这一个项目当 vault**"（step 6-7："Don't work from the giant vault. The big vault plans. A single project ships."）。IPOF 是这份 guide 自己加的，**不是 Karpathy 的**。

用户把个人/公司项目放进了 `raw/personal`、`raw/company`——即把"不可变来源"和"活的工作区"两种语义不同的东西放进了同一个目录，于是撞上"raw 只读 vs 我要在里面干活"的矛盾。

### 1.3 两份原典指向同一答案

- Karpathy：raw 恒定只读 → 工作区不能在 raw 里。
- Guide：项目是独立顶层文件夹、独立打开 → 工作区在 vault 根，不在 raw 底下。

用户落地方案 §8.4 其实早已写下这个意图："需要独立文档产出时，**在 vault 根创建项目文件夹**，参考 IPOF。（注：此为 v1.2 改动前的 §8.4 原文；现 §8.4 已按本方案改为"工作区都在 vault 外"，故此处引文与现文相反是预期的）"

---

## 二、设计决策

**不让 raw 可编辑，而是把"要编辑的东西"从 raw 里请出来，独立成"工作区"层。**

比"raw 可编辑 + 重新摄取门"更优的理由：
1. 让 raw 可编辑会侵蚀 "source of truth" 地基，wiki 引用 raw 的可信度打折。
2. "改后更新 sha256 / 漂移检测开例外 / 改完确认再摄取"这堆复杂度，在正确架构下**根本不需要存在**——工作区压根不是"摄取后冻结"的 raw。
3. 同时忠于两份原典。

---

## 三、目标模型

### 3.1 层次（三层 → 四层）

```
┌─ Schema 层（CLAUDE.md）──────────────── 宪法·纯规则·Agent 无关
├─ Wiki 层（LLM 维护）──────────────────── 提炼的知识（大脑）
├─ Raw 层（只读来源）──────────────────── 不可变外部快照·事实来源
└─ Workspace 层（人+LLM 共同演化）──────── 【新增】活的工作区·IPOF
     └─ 全部在 vault 外·经 workspaces.md 逐个登记
```

### 3.2 工作区：全部外部登记

所有项目工作区（个人、公司一视同仁）都在 vault **外**任意路径，逐个登记进 `workspaces.md`，各套 IPOF + 项目级 CLAUDE.md。brain 按每条登记的 access 权限读写；详设留原地，wiki 只存摘要+指针。

**为什么全放 vault 外**：
1. **天然隔离**——在工作区目录启动 claude 时，向上递归到不了 vault 的 `CLAUDE.md`，只加载全局 `~/.claude/CLAUDE.md` + 项目 CLAUDE.md，得到干净项目模式（keys not prompts，无需 `claudeMdExcludes`）。
2. **不重复建设**——公司项目常已有自己的仓库/原 vault（落地方案 §七·2「不做重复建设」/ §4.4）。
3. **隐私/位置**——公司数据不宜进 iCloud 私有 vault（落地方案 §4.4："保留摘要+指针，详设留在原 vault"）。

### 3.3 目录结构

```
digital-brain/                     ← vault
├── CLAUDE.md            ← Schema 宪法（战略层）
├── workspaces.md        ← 【新增】工作区登记表（环境配置层）
├── index.md / log.md
├── raw/                 ← 【只读·不可变】外部快照
│   ├── wechat/ bookmarks/ articles/
│   └── （录入的 docx/pdf 等冻结参考件）
└── wiki/                ← 【LLM 维护的知识】大脑

（工作区不在 vault 内，示意）
/任意/外部/路径/{项目}/    ← 在 workspaces.md 登记
├── inputs/ process/ outputs/ feedback/
└── CLAUDE.md            ← 项目级战术层（是什么·唯一目标·brain 的角色）
```

### 3.4 各层关系

- **raw → wiki**：摄取，规则不变。
- **工作区 → wiki（沉淀门）**：工作区里干出来、值得记住的东西（决策/经验/成品）——**不是每次编辑都回灌 wiki**，触发以 §10 沉淀 SOP 为准（保住用户的关切：改多次、测多次，最后一次再入库）。wiki 里只留项目"索引卡"（`entity` / `entity-type: project`）+ 指针（= workspaces.md 里的登记名），活儿在工作区干。
- **工作区的 inputs** 可引用 raw/ 或 wiki/。

---

## 四、workspaces.md 规范

外部工作区登记表，属**环境配置层**（机器相关，绝对路径不进纯 Schema，保持 CLAUDE.md 可迁移；对应落地方案 §8.11 的三层分离）。

每条登记至少包含：

```markdown
## {项目名}
- path: /absolute/path/to/external/workspace   # vault 外绝对路径
- type: personal | company | other
- purpose: 一句话说明这是什么、brain 该怎么用它
- wiki: [[对应的 wiki 索引卡页面]]              # brain 在 wiki 里的入口
- access: read-only | read-write               # brain 对该目录的权限意图
```

brain 每次会话读 workspaces.md → 知道有哪些外部工作区、在哪、权限如何。换机器只改此文件，宪法不动。

---

## 五、对现有文件的改动清单

### 5.1 `CLAUDE-schema.md`

| 节 | 改动 |
|----|------|
| §1 角色 & 权限 | "你不能动 raw/"→ 明确"raw 摄取后不可变；录入窗口期（§6④）是唯一编辑机会"。新增：brain 在 vault 外、workspaces.md 登记的工作区内为项目目标自由创建/编辑（按 access 权限）；破坏性操作（删目录、大重构）先问。 |
| §2 目录结构 | 目录树加 `workspaces.md`（**不加 projects/**，工作区在 vault 外）；补"四层职责"说明；澄清 raw/ 只放不可变来源。 |
| §6④ 录入 SOP | 明确"录入窗口是 raw 唯一编辑机会；摄取（写 sha256）后即冻结；外部来源真变了走重新摄取=新快照，不原地改"。 |
| 新增节 §16 工作区 SOP | 定义工作区（**全部 vault 外、逐个登记**）、IPOF、项目级 CLAUDE.md、沉淀门（触发以 §10 为准）、workspaces.md 用法、放 vault 外的隔离原理。 |
| §12 log 格式 | 新增 `project` 动作（`## [日期] project \| {项目名}`）。 |
| 页脚版本 | v1.1 → v1.2。 |

### 5.2 `Digital Brain 落地方案.md`

| 节 | 改动 |
|----|------|
| §1.2 三个层次 | 三层图 → 四层（加 Workspace 层，工作区在 vault 外）。 |
| §二 Vault 目录结构 | 目录树加 `workspaces.md`（**不加 projects/**）；更新注释：工作区都在 vault 外、逐个登记进 workspaces.md。 |
| §4.4 公司项目 | 与"外部注册工作区"机制对齐，指向 workspaces.md。 |
| §8.4 独立项目空间 | 从"可选"升为正式的 Workspace 层说明（全部 vault 外）。 |

### 5.3 新增 `workspaces.md`

按第四节规范创建，含表头说明 + 空模板（初始无真实条目，或按用户当前公司项目登记）。

---

## 六、无需迁移

`raw/personal`、`raw/company` 现有内容是**已走录入 SOP 的冻结来源**（手动录入的参考材料），位置正确，保持不动——它们本就是 raw，不是放错位置的工作区。

工作区是**面向未来**的：新的项目干活目录放 vault 外任意路径，登记进 `workspaces.md` 即可。不涉及对现有文件的移动。

---

## 七、未决 / 待实施时细化

- ~~§16 新节编号~~ → 已定为 §16。
- 项目级 CLAUDE.md 的最小模板（工作区在 vault 外，模板可在实际建工作区时再定）。
- workspaces.md 是否需要 brain 在 Lint 时校验（如登记路径是否存在、access 是否越权）。
