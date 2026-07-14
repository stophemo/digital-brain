---
name: digital-brain-setup
description: 一句话把一个空目录搭建成 Digital Brain——由 LLM 持续维护、持久复利的个人知识 wiki（llm-wiki 模式）。当用户想"搭建/初始化/bootstrap digital-brain、建第二大脑、建知识 vault/知识库"时使用：脚手架 vault 目录、把 Schema 装成 Agent 规则文件、访谈用户建 persona 与定制、交付后提示可开始摄入。触发词：搭建 digital-brain、建我的第二大脑、初始化知识库、setup digital brain、bootstrap knowledge vault。
---

# Digital Brain 一键搭建

把一个空目录变成可用的 Digital Brain：脚手架 → 装宪法 → 访谈定制 → 交付。
**访谈时一次只问一个问题，等答完再问下一个，别一次抛一堆。**

## 前置
- 定位 `Schema.md`（本 skill 同仓库的 `outputs/Schema.md`，或用户指定路径）——它是 vault 宪法的来源，**逐字复制、不改写**。
- 问用户：vault 建在哪个目录？（默认当前目录下 `digital-brain/`）

## 步骤

### 1. 脚手架目录
在 vault 目录下创建（`raw/` 子目录先给默认，第 3 步按用户领域/数据源再增改——见 Schema §2「分类原则固定、子目录按需增删」）：
```
<vault>/
├── raw/
│   ├── project/                        # 一般资料默认桶
│   └── assets/{images,audio,video,html}/
├── wiki/{entities,concepts,comparisons,syntheses,queries,drafts}/
├── index.md                            # 空目录，按 Schema §11 起头
└── log.md                              # 空日志，按 Schema §12 起头
```

### 2. 安装宪法
把 `Schema.md` 内容**逐字**写成 vault 根的 Agent 规则文件：Claude Code → `CLAUDE.md`；Codex → `AGENTS.md`；其他 Agent → 各自约定文件。
这是唯一手动放进去的"种子"——它定义整个 wiki 的结构、规则与工作流，剩下交给 LLM。

### 3. 访谈定制（一次一个问题）
逐个问、等回答，再用回答定制：
1. 你是谁、做什么？
2. 今年的主要目标？
3. 希望我怎么跟你说话（风格、详略）？
4. 你的**领域**有哪些（工作/专业/兴趣）？→ 替换宪法 §5「领域」标签行；按需增改 `raw/` 子目录桶。
5. 你有哪些**数据源**（文档/网页/书签/聊天导出/音视频…）？→ 按需在 `raw/` 建对应桶；§6 策略表只留用得上的适配行。
6. 手头在推进的项目？

访谈完：
- 画像写进 `wiki/entities/persona/<你>.md`（按 Schema §4 补 frontmatter；persona 放 wiki，**不塞进宪法**）。
- 把宪法 §5 的「领域」行改成用户真实领域。
- `index.md` 记一行、`log.md` 追加一条 `create` 日志。

### 4. 本地 git（可选，按 Schema §15）
`git init`——**纯本地、不加远程、不 push**；`.gitignore` 排除 `.DS_Store` 与编辑器配置目录。

### 5. 交付 & 使用提示
告诉用户：
> ✅ Digital Brain 搭好了，可以开始**摄入**了。
> - **摄入**：把资料丢进 `raw/`，说"摄入这份 `<路径>`" → 我转成标准 md，暂停给你确认。
> - **汲取**：确认后说"汲取" → 我提炼进 wiki、更新交叉引用。
> - **查询**：直接问，我从 wiki 合成带引用的答案。
> - **体检**：说"lint" → 我做一次 wiki 健康检查。

---
*本 skill 是 Digital Brain 的安装器；规则本身见同仓库 `Schema.md`（Agent 无关）。*
