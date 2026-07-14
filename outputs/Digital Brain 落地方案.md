# Digital Brain — 落地方案

> **理论基础**：Andrej Karpathy《LLM Wiki》(2026.04) + Claude+Obsidian Second Brain Guide
> **执行环境**：macOS · Claude Code · Obsidian
> **存储位置**：由你选择——本地磁盘 或 iCloud/私有云（取舍见 §六·存储位置）
> **文档版本**：v2.3 · 2026-07-14（对齐 Schema v1.4）
>
> ⚠️ **本文档是完整方案（给人看）——讲"为什么"和"怎么落地"。** 唯一权威的执行规则是 Schema，见同目录 `CLAUDE-schema.md`（部署为 vault 根 CLAUDE.md）。本文档只引用 Schema、不复制它，避免两份漂移。
> 📖 **仓库入口 `README.md`**（快速上手 + 定制点清单）；`实操流程-ClaudeCode+Obsidian.md` 为 15 分钟 Quickstart。

---

## 一、什么是 Digital Brain

### 1.1 核心洞见（来自 llm-wiki）

Karpathy 的 llm-wiki 不是又一个笔记系统——它是对抗"查询即遗忘"的架构范式：

> *"The wiki is a persistent, compounding artifact. The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read."*

**RAG 模式 vs Digital Brain 的本质差异**：

| 维度 | RAG | Digital Brain |
|------|-----|--------------|
| 知识状态 | 每次查询从零拼凑 | 持久化、持续演化 |
| 交叉引用 | 临时匹配，用完即弃 | 已内建在 wiki 中 |
| 矛盾处理 | 无 | 已标注，永不静默覆盖 |
| 复利效应 | 无 | 每份新资料让整个库更聪明 |
| 人的角色 | 被动接收结果 | 策展者：选资料、定方向、问好问题 |

### 1.2 四个层次（llm-wiki + IPOF 工作区）

> **归属说明**：Karpathy 的 llm-wiki 原典只有 **三层**（Schema / Wiki / Raw），**没有项目/工作区概念**。下面的第 4 层 **Workspace(IPOF)** 来自 Second Brain Guide，是本方案的扩展，非 Karpathy 原创。

```
┌─ Schema 层（CLAUDE.md）──────────────┐
│  结构约定 · 写作规范 · 摄取流程 · 安全  │
│  人+LLM 共同演化                       │
├─ Wiki 层（LLM 维护）─────────────────┤
│  entities · concepts · comparisons   │
│  syntheses · queries · drafts        │
│  人负责阅读，LLM 负责编写              │
├─ Raw 层（只读来源）──────────────────┤
│  微信 · 书签 · Office · 音视频 · 网页  │
│  不可变的事实来源                      │
├─ Workspace 层（人+LLM 共同干活）──────┤  ← 本方案扩展，来自 Second Brain Guide
│  vault 外目录 · workspaces.md 登记      │
│  IPOF · 产出成品 · 经沉淀门入 wiki       │
└──────────────────────────────────────┘
```

### 1.3 三个核心操作

**Ingest（摄取）**：新资料 → LLM 读取 → 提取关键信息 → 更新 wiki 中 5-15 个页面 → 追加日志

**Query（查询）**：提问 → 搜索 wiki → 整合答案并引用来源。好的答案归档回 wiki

**Lint（健康检查）**：定期扫描矛盾、孤立页面、过时内容。wiki 的免疫系统

### 1.4 为什么能工作

llm-wiki 的结论：*"The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims, maintaining consistency across dozens of pages. Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."*

维护一个知识库真正累人的不是阅读和思考，而是记账式的维护——更新交叉引用、保持摘要最新、标注矛盾、维持数十页的一致性。人放弃 wiki，是因为维护负担增长快于价值；而 LLM 不厌烦、不忘记更新引用、能一次触碰 15 个文件。

---

## 二、Vault 目录结构

```
digital-brain/
├── CLAUDE.md              ← Schema 层（唯一权威执行规则）
├── workspaces.md          ← 外部工作区登记表（环境配置）
├── index.md               ← 内容目录（LLM 维护）
├── log.md                 ← 操作日志（LLM 追加）
├── raw/                   ← Layer 1：不可变原始资料
│   ├── wechat/            ← 微信数据（可选数据源）
│   │   ├── data/           ← 聊天记录（{联系人}/{YYYY-MM}.md）
│   │   ├── feature/        ← 特征聚合
│   │   └── reports/        ← 分析报告（{YYYY-MM}/）
│   ├── bookmarks/         ← 浏览器书签导出
│   ├── personal/          ← 个人领域冻结参考件（非工作区）
│   ├── company/           ← 公司领域冻结参考件（非工作区）
│   ├── articles/          ← 网页剪辑
│   └── assets/            ← 全局附件
│       ├── images/        ← ★ 所有 raw/ 文档的图片统一存放
│       ├── audio/         ← 音频转录文本
│       ├── video/         ← 视频关键帧 + 转录文本
│       └── html/          ← 网页快照 HTML
├── wiki/                  ← Layer 2：LLM 维护的知识
│   ├── entities/          ← 人、组织、系统、项目（人物画像见 entities/persona/）
│   ├── concepts/          ← 技术、方法论、想法
│   ├── comparisons/       ← A vs B 对比分析
│   ├── syntheses/         ← 跨资料综合论述
│   ├── queries/           ← 有价值的查询归档
│   └── drafts/            ← 内容草稿（工作产物，非知识节点）
├── .git/
├── .gitignore
└── .obsidian/
    └── graph.json         ← 图谱着色
```

注：项目**知识**按内容归入对应 wiki 类型——项目本身是 entity，技术决策是 concept，方案对比是 comparison。项目**工作区**（活的干活空间）是独立的一层，且**都在 vault 外**：所有项目（个人、公司）放 vault 外任意路径，逐个登记进 `workspaces.md`（详见 Schema §16）。放 vault 外，是为了在工作区启动 claude 时天然不加载 vault 的 Schema（父级不在其路径上），得到干净的项目模式。

### 目录设计原则

**raw/ 结构固定**——按数据源的安全边界和摄取管线分类。

**wiki/ 结构是初始脚手架**——llm-wiki 核心原则 *"The LLM owns this layer entirely."* LLM 有权重构。

**CLAUDE.md 是宪法，wiki 结构是判例法**——宪法规定必须遵守的原则，目录树是案例积累出来的。

---

## 三、Schema 速查（权威在 CLAUDE.md）

> 本节原为 Schema 全文复制，**已删除**——避免与宪法漂移（复制一份就会各改各的）。执行规则的唯一权威是 `CLAUDE-schema.md`。这里只给一张速查索引，细节点进对应节次。

| 节 | 内容 | 一句话 |
|----|------|--------|
| §1 | 角色 & 权限 | 你是 wiki 维护者；wiki/ 全权，raw/ 只读，CLAUDE.md 改前先议 |
| §2 | 目录结构 | 四层职责 + raw/ 附件镜像存放规则 |
| §3 | 写作约定 | 中文为主；500 行裂变/200 行拆分候选；每页 ≥2 出站链接；溯源 |
| §4 | Frontmatter | wiki 页与 raw 文件的必填字段；type 枚举（含 draft）|
| §5 | 标签分类 | 用前先注册；**领域标签需按你自己的工作定义** |
| §6 | 录入 SOP | 原始文件 → 标准化 raw/.md；④ 人工确认窗口是 raw 唯一编辑机会 |
| §7 | 摄取 SOP | raw → wiki；entity/persona 页结构；矛盾不静默覆盖 |
| §8 | 更新策略 | 矛盾处理：保留双方 + contested 标记 |
| §9 | 查询 SOP | 读 index → 合成引用 → 值得的归档回 wiki |
| §10 | 沉淀 SOP | 从对话（而非 raw）提取可复用经验/方法论 |
| §11–12 | index / log 格式 | 分区目录 + 追加式带前缀日志 |
| §13 | 结构演化 | wiki 结构由 LLM 负责；硬阈值 vs 裁量的优先级 |
| §14 | Lint SOP | 13 项健康检查，按 🔴🟡🔵 分级 |
| §15 | 安全 | 纯本地 git、不上网；raw 只读的真锁 = settings deny；PRIVATE 标记非加密 |
| §16 | 工作区 SOP | 工作区全部 vault 外、逐个登记；位置即隔离 |

---

## 四、数据源摄取方案

> 以下数据源均为**可选适配器**——按你自己的实际来源取用。核心 Schema 不依赖任何特定工具。

### 4.1 微信聊天记录（可选）

**导出工具**：本地运行的微信聊天记录分析工具（如 wechat-insight，⚠️ 仅 macOS，直接读取微信本地数据库导出为结构化数据）。此类工具随微信版本更新可能失效，属外部强依赖——建议 pin 住已验证的微信版本，并保留手动导出作为降级路径。

**流程**：`导出` → `raw/wechat/data/{联系人}/{YYYY-MM}.md` → LLM 提取人物实体、决策记录、知识碎片。特征分析结果 → `raw/wechat/feature/`，定期报告 → `raw/wechat/reports/{YYYY-MM}/`

**隐私**：见 Schema §15（纯本地 git、不上网）。wiki 层只保留提炼知识，聊天逐字内容只在 raw/。

### 4.2 浏览器书签

导出 HTML → 书签树解析脚本 → raw/bookmarks/{日期}.md → LLM 分类、摘要、识别主题聚类。

### 4.3 个人项目文档

涵盖：文章草稿、Side project、学习笔记等。各类格式通过 Schema §6 录入策略表统一处理。摄取触发：手动指定。

### 4.4 公司/工作项目文档

涵盖：需求规格(.docx)、原型截图、财务表格(.xlsx)、演示文稿(.pptx)。

通过录入策略表处理。与已有 Obsidian Vault 的关系：Digital Brain 保留摘要+指针，详设留在原 vault。若公司项目有独立工作目录（原仓库/原 vault），在 `workspaces.md` 中登记为外部工作区（见 Schema §16），brain 知晓其路径并按 access 权限读写，不复制进本 vault。

### 4.5 未来数据源

邮件、日历、GitHub Issues/PRs、Kindle 标注等。

---

## 五、实施路线图

### Phase 1 · 基础搭建（本周）

- [ ] P1.1 Obsidian 打开你的 `digital-brain/` 文件夹作为 vault（位置见 §六·存储位置）
- [ ] P1.2 Claude 初始化目录结构（放 CLAUDE.md → 启动 Claude → 让它创建）
- [ ] P1.3 配置 .gitignore（排除 `.DS_Store` + `.obsidian/`）
- [ ] P1.4 第一个数据源：浏览器书签
- [ ] P1.5 Interview 式 Profile 构建 → 写入 wiki/entities/persona/
- [ ] P1.6 git init（本地仓库）。⚠️ 若 vault 放 iCloud，`.git` 与 iCloud 同步可能冲突损坏——建议 vault 放本地磁盘，或把 `.git` 排除出同步（见 §六）

### Phase 2 · 核心数据接入（2-4 周）

- [ ] P2.1 接入公司项目文档
- [ ] P2.2 接入个人项目文档
- [ ] P2.3 接入一期微信聊天记录（如使用）

### Phase 3 · 自动化（1-2 月）

> ⚠️ **前提说明**：Claude Code CLI 本身无内置调度，定时需靠 OS 层 cron/launchd 调用 `claude -p` 无头模式。且**定时摄取与 §6④ 人工确认门冲突**——无人值守会绕过确认。因此自动化**只用于无隐私、可无人值守、且只读/只报告的环节**（如书签抓取、Lint 报告、每日简报）；写库/摄取仍保留人工确认门。

- [ ] 定时 Lint（只读扫描 + 报告，等人审）
- [ ] 每日简报（只读汇总）
- [ ] 书签等周期性数据源的定时抓取（抓取到 raw 待录入区，仍走人工确认后摄取）

### Phase 4 · 持续演进

- [ ] 更多数据源
- [ ] 向量搜索（如 qmd，wiki 上百页后）
- [ ] 图谱分析
- [ ] 输出能力（Marp 幻灯片等）

---

## 六、技术方案

| 环节 | 工具 | 选型理由 |
|------|------|---------|
| 知识存储 | Obsidian | 纯文本、双向链接、图谱、免费 |
| AI 引擎 | Claude Code | 直接读写本地文件 |
| 文档录入 | pandoc + python | 命令行工具链 |
| 语音转录 | mlx-whisper（Apple Silicon）/ whisper | 本地转录，不耗 LLM token |
| 版本控制 | Git | 免费历史、分支实验 |

### 存储位置（需你选择）

| 方案 | 优点 | 代价 |
|------|------|------|
| **本地磁盘**（推荐） | Git 最稳、隐私边界清晰（纯本地） | 备份需自建（Time Machine / 外置盘 / rsync）|
| **iCloud / 私有云** | 备份省事、多设备可见 | ⚠️ iCloud 同步 `.git` 内部对象可能触发 dataless 驱逐/冲突副本 → 仓库损坏；且默认非端到端加密，敏感数据会进 Apple 云 |

> 折中：vault 工作树放同步盘，但把 `.git` 移出同步（或 vault 放本地、单独备份）。**iCloud 是"备份"而非"架构支柱"——按需选择，不硬绑定。**

**Obsidian 插件生态**：Dataview（frontmatter 查询）、Web Clipper（网页抓取）、Local REST API（仅在需要 MCP/换 Agent 时装；当前 Claude Code 直接读写文件不需要它，且其 API Key 存 `.obsidian/`，务必确认 `.obsidian/` 已 gitignore）。

---

## 七、注意事项

1. **Keys, not prompts** — 能用文件系统/权限层控制的就别靠措辞。本方案真正的"key"是：工作区外置（位置即隔离）+ 无远程 git。raw/ 只读若要真锁，用 `.claude/settings.json` 的 deny 规则（见 Schema §15），否则它只是"约定 + git 兜底"。
2. **不做重复建设** — 已有的 Obsidian Vault 保留详设，Digital Brain 保留摘要+指针
3. **逐份摄取，人在回路** — Karpathy 的**个人偏好**（原文亦允许批量摄取，"由你决定"）；本方案默认逐份
4. **处理矛盾永不静默覆盖**
5. **frontmatter 是本方案的工程约定**（原典中 frontmatter 为可选、供 Dataview 用；本方案设为必带以支撑 Lint）

---

## 八、日常工作流与实操技巧

### 8.1 双窗口工作流

Karpathy 原文：*"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."*

LLM Agent 在左边，Obsidian 在右边。边做边看。

### 8.2 构建 Profile：Interview 法

Second Brain Guide Step 5：让 Claude 面试你，一次一个问题。

> **与 Guide 的差异**：Guide 让把结果写进根 `CLAUDE.md`；本方案因 CLAUDE.md 定为不可变 Schema、且个人档属 entity，改写入 `wiki/entities/persona/`。

### 8.3 快速摄取网页

Obsidian Web Clipper 剪辑 → Ctrl+Shift+D 下载图片 → 告诉 Claude "摄取这篇"

### 8.4 工作区：独立项目空间

工作区是正式的一层（见 Schema §16），且**都在 vault 外**。所有项目（个人、公司）放 vault 外任意路径，套 IPOF（inputs/process/outputs/feedback）+ 项目级 CLAUDE.md，逐个登记进 `workspaces.md`。放 vault 外的好处：在工作区启动 claude 时不会加载 vault 的 Schema，天然是干净的项目模式。工作区里的成果经"沉淀门"入 wiki——不每次编辑回灌，触发以 §10 沉淀 SOP 为准。

### 8.5 Skills：重复操作抽象化

Second Brain Guide Step 8：做了两次以上的操作 → 变成 Skill。

### 8.6 图谱视图

Obsidian Graph View 看知识结构——枢纽节点、孤岛、自然聚类。

### 8.7 Archive：知识有生命周期

借鉴 llm-wiki 的 Lint 思路（新来源取代旧论断即视为过时）：对完全被取代的页面，归档到 `_archive/` 目录而非删除。

### 8.8 grep 友好的日志查询

```bash
grep "^## \[" log.md | tail -5          # 最近 5 次操作
grep "ingest" log.md                     # 所有摄取记录
```

### 8.9 社区现成仓库

GitHub 上已有若干 Karpathy wiki 模式的开源实现（搜索关键词 "claude obsidian second brain" / "llm wiki"），可 clone 后改造成自己的私有版本。

### 8.10 Agent 与 Obsidian 的连接方式

三种方式，按推荐顺序：

| 方式 | 场景 | 优点 |
|------|------|------|
| ① 直接读写 | Claude Code 等本地 Agent | 零延迟、零配置 |
| ② Obsidian URI | Agent → Obsidian 跳转 | 一键打开页面 |
| ③ MCP + Local REST API | 网页版 Agent / 换 Agent | Agent 无关标准协议 |

日常用 ①，Agent 产出后用 ② 跳转查看，换 Agent 时启用 ③。

### 8.11 Agent 可迁移性：两层分离

```
Schema 层（CLAUDE.md）          → 纯规则，Agent 无关
实现层（脚本/Skill/插件）        → 各 Agent 按自身机制实现
```

Schema 只描述"要达到什么效果"，不绑定具体工具；换 Agent 时只需按新 Agent 的能力重新实现录入/转换等操作，Schema 不动。

---

> *You are not building a Claude setup. You are building your own memory, and it gets smarter every day you feed it.*

> *The idea is related in spirit to Vannevar Bush's Memex (1945) — a personal, curated knowledge store with associative trails between documents. […] The part he couldn't solve was who does the maintenance. The LLM handles that.*
> — Andrej Karpathy, LLM Wiki

---

*文档版本 v2.3 · 2026-07-14 · 基于 llm-wiki (Karpathy) + Claude+Obsidian Second Brain Guide*
