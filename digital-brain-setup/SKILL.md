---
name: digital-brain-setup
description: 搭建并定制由 LLM 持续维护的本地 Digital Brain 知识库。用户要求初始化第二大脑、llm-wiki、知识 vault、个人 wiki，或把 Karpathy LLM Wiki 模式落地为可供 Claude Code、Codex、Gemini 等 Agent 使用的目录时使用；负责安全预检、创建三层结构、安装 Agent 规则、逐题访谈、生成画像与配置，并验证交付结果。
---

# Digital Brain Setup

把一个空目录初始化为可运行的 Digital Brain。保持 Schema、Raw、Wiki 三个语义层，
并用确定性脚本完成脚手架和 raw 快照校验。

## 资源

以当前 Skill 目录为 `<skill-dir>`：

- `assets/Schema.md`：部署到 vault 的固定运行时规则，不做实例化改写。
- `assets/templates/`：JSON 配置、索引、日志和 `.gitignore` 模板。
- `scripts/init_vault.py`：无覆盖初始化。
- `scripts/finalize_snapshot.py`：把已审核 staging 原子冻结为 raw snapshot。
- `scripts/record_schema_update.py`：记录用户已授权的 Schema 变更。
- `scripts/validate_vault.py`：验证目录与 snapshot 完整性。

不要依赖 Skill 目录之外的仓库文件。

## 工作流

### 1. 预检

一次只问一个问题，先确认：

1. vault 目标路径；默认 `<当前目录>/digital-brain`。
2. 使用哪个 Agent：Codex、Claude、Gemini 或其他规则文件名。

检查目标路径：

- 目标已存在且非空时停止，列出冲突；不要覆盖或合并。
- 目标位于现有 Git worktree 时检查 remote。存在 remote 时，解释 raw 和个人资料的
  泄露风险；只有用户明确确认后才允许在该 worktree 内初始化。
- 不创建网络连接，不安装依赖，不执行 `git init`。

### 2. 初始化

从 `<skill-dir>` 运行：

```bash
python3 scripts/init_vault.py <vault> --agent codex
```

Agent 映射：Codex 使用 `AGENTS.md`，Claude 使用 `CLAUDE.md`，Gemini 使用
`GEMINI.md`。其他 Agent 使用：

```bash
python3 scripts/init_vault.py <vault> --agent other --rule-file <规则文件名.md>
```

若用户已明确允许在带 remote 的现有 worktree 中创建，再加
`--allow-existing-git`。不要用该参数绕过未确认的风险。

初始化后确认规则文件与 `assets/Schema.md` 字节一致。实例偏好只写
`.digital-brain/config.json`。

### 3. 逐题访谈

严格一次问一个问题，等用户回答后再继续：

1. 你是谁、主要做什么？
2. 你今年最重要的目标是什么？
3. 你希望 Agent 采用什么沟通方式和详略程度？
4. 你的优势、限制或需要特别留意的工作习惯是什么？
5. 需要长期积累的工作、专业和兴趣领域有哪些？
6. 会摄入哪些数据源？按信任边界或处理管线应分成哪些 bucket？
7. 当前有哪些项目？这里只建立知识索引，不在 raw 中创建可变工作区。
8. 是否允许使用外部转换/API 处理资料？默认不允许。

访谈过程中不要把凭据、token、身份证号等秘密写入 vault。

### 4. 写入实例配置

根据明确回答更新 `.digital-brain/config.json`，保持有效 JSON：

- `language` 和沟通偏好；
- `source_buckets`，使用最长 64 字符的小写 kebab-case 且含义单一；
- `taxonomy`，只注册实际需要的小写 kebab-case 标签；
- `ingestion.preferences`；
- `privacy.allow_external_processing`。

创建 `wiki/entities/people/self.md`，使用 Schema §5 frontmatter；provenance 写：

```yaml
provenance:
  - kind: user-input
    ref: setup-interview:YYYY-MM-DD
```

按需为当前项目创建 `wiki/entities/projects/` 页面。不要凭空补全用户未提供的信息；
不确定内容标 `confidence: low`。

### 5. 更新索引和日志

- 在 `index.md` 的 Entities 分区登记画像与项目页面。
- 重算 `wiki/` 下 `.md` 数量，更新 `total_pages` 和日期。
- 在 `log.md` 追加具体的 `create` 与 `config` 记录。
- 日志不记录完整访谈、秘密或敏感个人细节。

### 6. 验证

运行：

```bash
python3 <vault>/.digital-brain/scripts/validate_vault.py <vault>
```

并人工确认：

- 目录、规则文件、`config.json`、`state.json`、index、log 和运行脚本齐全；
- 规则文件仍与 Skill 的 `assets/Schema.md` 一致；
- 画像 frontmatter、index 条目和日志相互一致；
- `.staging/` 已被 `.gitignore` 排除；
- 未创建 remote、未 push、未把源资料复制到 raw。

修复所有 Error 后再交付。

### 7. 可选 Git

只有用户明确要求时才初始化本地 Git。执行前再次说明：Git 历史不是加密，未来添加
remote 可能暴露 raw 和个人资料。不要自动添加 remote 或 push。

### 8. 交付

报告 vault 路径、规则文件名、验证结果和已登记的 buckets。然后简要说明：

- 摄入：提供来源路径或 URL，Agent 在 `.staging/` 转换并等待审核。
- 确认摄入：冻结为带 manifest 和哈希的 raw snapshot。
- 汲取：从冻结 snapshot 更新 wiki、index 和 log。
- 查询：基于 wiki 回答，重要结果可归档。
- 体检：说“lint”运行 Schema 中的健康检查。
