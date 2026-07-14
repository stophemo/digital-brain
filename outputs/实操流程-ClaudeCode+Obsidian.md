# Digital Brain 实操流程 · Claude Code + Obsidian

> 版本 v2.1 · 2026-07-14 · Quickstart（15 分钟冷启动）

---

## 前置条件（开始前先自检）

- [ ] **Claude Code** 已安装，且账号是**付费计划**（免费档不支持）
- [ ] **Obsidian** 已安装（免费）
- [ ] **macOS**（本流程按 macOS 写；部分工具如 mlx-whisper 为 Apple Silicon）
- [ ] 命令行工具：`git`；按需 `pandoc`、`python3`、`ffmpeg`（各数据源用到时再装）
- [ ] 想好 **vault 放哪**（见下方"存储位置")

**存储位置**：本地磁盘（推荐，Git 最稳）或 iCloud/私有云（备份省事，但 `.git` 与 iCloud 同步可能损坏——见落地方案 §六）。下文用 `$BRAIN` 代指你选定的路径。

```bash
# 例：本地磁盘
export BRAIN="$HOME/digital-brain"
# 或：iCloud（注意 .git 同步风险）
# export BRAIN="$HOME/Library/Mobile Documents/com~apple~CloudDocs/digital-brain"
```

---

## 第一步：创建 vault，种下种子（2 分钟）

### 1. 创建空文件夹

```bash
mkdir -p "$BRAIN"
```

### 2. Obsidian 打开为 vault

打开 Obsidian → 点击左下角 vault 名 → "打开文件夹作为 Vault" → 选择 `$BRAIN` → 信任。

此时 vault 里是空的——只有 Obsidian 自动生成的 `.obsidian/` 配置目录。

### 3. 放入 CLAUDE.md（种子文件）

把本仓库的 `CLAUDE-schema.md` 复制为 vault 根的 `CLAUDE.md`：

```bash
cp /path/to/CLAUDE-schema.md "$BRAIN/CLAUDE.md"
```

这是唯一需要手动放进去的文件。CLAUDE.md 就是 Digital Brain 的种子——它定义了整个 wiki 的结构、规则和工作流。剩下的交给 Claude。

> **首次自定义**：打开 `$BRAIN/CLAUDE.md`，把 §5 标签表里的「领域」一行换成你自己的实际领域（工作、专业、兴趣）。其余先用默认（完整定制点清单见仓库 `README.md`）。

---

## 第二步：启动 Claude，让它初始化一切

```bash
cd "$BRAIN"
claude
```

Claude Code 自动读取根目录的 CLAUDE.md。验证一下它懂了：

> 你是什么角色？

它应该回答自己是"wiki 维护者"。然后告诉它：

> 初始化 Digital Brain——创建所有必要的目录结构、index.md、log.md、.gitignore。
> 按 CLAUDE.md §2 的目录结构来。

Claude 会自己创建：

```
digital-brain/
├── CLAUDE.md
├── index.md          ← Claude 创建
├── log.md            ← Claude 创建
├── .gitignore        ← Claude 创建（排除 .DS_Store + .obsidian/）
├── raw/
│   ├── wechat/
│   ├── bookmarks/
│   ├── personal/
│   ├── company/
│   ├── articles/
│   └── assets/{images,audio,video,html}/
└── wiki/
    ├── entities/
    ├── concepts/
    ├── comparisons/
    ├── syntheses/
    ├── queries/
    └── drafts/
```

切换到 Obsidian 看一眼——目录结构已经出现在文件列表里了。

---

## 第三步：配置 Obsidian（3 分钟，一次性）

**附件路径**：设置 → 文件与链接 → "附件文件夹路径" → `raw/assets/images`

**图片下载快捷键**：设置 → 快捷键 → 搜索 "Download attachments for current file" → 绑定 `Ctrl+Shift+D`

**其他推荐插件**：Dataview（frontmatter 查询）、Web Clipper 浏览器扩展（一键抓取网页）

> Local REST API 插件当前**不需要**（Claude Code 直接读写文件）；仅在将来换 Agent / 需要 MCP 连接时再装，且它的 API Key 存 `.obsidian/`，装了要确认 `.obsidian/` 已被 gitignore。

---

## 第四步：第一次摄取

建议从浏览器书签开始——最快见效，无隐私顾虑。

1. 浏览器 → 导出书签为 HTML → 保存到 Downloads
2. 在 Claude Code 里说：

> 摄取 ~/Downloads/bookmarks.html

Claude 按 CLAUDE.md 的录入 SOP 自动处理：识别书签格式 → 解析 → 放入 raw/bookmarks/ → 展示摘要 → **暂停等你确认**。

3. 确认后说"继续摄取"。

4. 切到 Obsidian → Graph View，第一批节点出现。

---

## 第五步：把你自己装进去

Second Brain Guide Step 5 的标题就是 *"Load yourself into the brain"*。不是手写自我介绍——是让 Claude 面试你。

在 Claude Code 里说：

> 你现在帮我建立 Digital Brain 的自我认知。一次只问一个问题，等我回答完再问下一个。
> 深入了解：我是谁、做什么工作、今年的目标、我希望你怎么跟我沟通、
> 我的优势和短板、当前在做的项目。
> 全部回答完后，把内容写入 wiki/entities/persona/ 下我的个人页面，带完整 frontmatter。

> **与 Guide 的差异**：Guide 让写进根 `CLAUDE.md`；本方案因 CLAUDE.md 是不可变 Schema，个人档改写入 `wiki/entities/persona/`。

以后每次摄取新资料，Claude 会按摄取 SOP 自动更新你的任务画像和变化记录，不用你再手动维护。

---

## 第六步：建技能，别再重复自己

Second Brain Guide Step 8：做了两次以上的操作 → 变成 Skill。

在 Claude Code 里说：

> 把「摄取浏览器书签」这个操作写成一个 Skill。

下次直接说"运行书签摄取 Skill"就行了。天然的 Skill 候选：书签摄取、Office 文档录入、每日简报、健康检查。每稳定执行 2-3 次后就让 Claude 写成 Skill。

---

## 日常使用

**摄取新资料**：在 vault 目录下启动 Claude，说"摄取 ~/Documents/某文档.docx"

**查询知识**：直接提问，Claude 从 wiki 中整合答案

**健康检查**：说"lint"

---

## Troubleshooting（常见问题）

- **Claude 不认为自己是 wiki 维护者** → 确认你在 vault 根目录启动 `claude`，且 `CLAUDE.md` 在根目录；重启会话。
- **git 报 `object file is empty` / `bad ref`** → 多半是 vault 在 iCloud、`.git` 被同步撕裂。把 `.git` 移出同步目录，或 vault 改放本地磁盘。
- **首次运行 Claude 要很多权限确认** → 正常。可在 vault 的 `.claude/settings.local.json` 里把常用只读命令加入 allow 白名单减少打断（但**不要**给 raw/ 写权限——见 Schema §15 的 deny 模板）。
- **Obsidian 图片显示不出来** → 确认"附件文件夹路径"设为 `raw/assets/images`，且图片按 §2 镜像规则存放。
- **想自动化定时任务** → Claude Code CLI 无内置调度，用 macOS `launchd`/`cron` 调 `claude -p`；且只自动化只读/只报告的环节（Lint、简报），摄取保留人工确认。

---

## 关于 MCP（可选项，暂不需要）

当前 Claude Code 直接读写 vault 文件——这是最快的路径，覆盖绝大多数场景。**不需要配 MCP。**

以下情况才需要：换成网页版 Claude（不能读写本地文件）、或换成其他不支持本地文件读写的 Agent。配置方法见落地方案 §8.10。

---

## 验证清单

- [ ] Claude 成功初始化了目录结构（raw/ + wiki/ 都在）
- [ ] 完成一次完整摄取：raw/ 有文件 → wiki/ 有新页面 → index.md 已更新 → log.md 有记录
- [ ] Obsidian Graph View 能看到节点
- [ ] Interview 生成的个人页面在 wiki/entities/persona/ 下且带 frontmatter
- [ ] `Ctrl+Shift+D` 图片下载快捷键生效
- [ ] `.gitignore` 已排除 `.DS_Store` 和 `.obsidian/`
