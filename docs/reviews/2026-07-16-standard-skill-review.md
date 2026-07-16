# 2026-07-16 标准 Skill 审查报告

## 结论

v2 可以表达 LLM Wiki 概念，但不适合直接作为标准 Skill 发布。阻断问题不是文案，而是
Skill 不自包含、Raw 并非真正快照、状态机自相矛盾、provenance 无法覆盖自身工作流，
以及 Git 与不可信来源缺少可靠边界。本轮以 v3 解决这些问题。

## 审查范围

- Karpathy *LLM Wiki* 中的三层模型、ingest/query/lint、index/log 原则。
- Yarchi Second Brain 中的逐题访谈、IPOF 项目实践、Skill 化和最小权限原则。
- v2 `Schema.md`、安装 Skill、README 和 v1.2/v1.4/v2.0 决策记录。
- 仓库打包、安装独立性、脚本可复现性和 GitHub 发布风险。

## 阻断级发现与处理

| 发现 | 风险 | v3 处理 |
|------|------|---------|
| Skill 引用父级 `outputs/Schema.md` | 单独安装后资源丢失 | Schema 移入 Skill `assets/`，所有路径包内相对 |
| raw 在步骤中先写、再人工改、最后改 frontmatter，却声称不可变 | 无明确冻结时刻 | 全部编辑在 `.staging/`；确认后脚本一次性写 manifest 并移动 |
| 二进制无法带 frontmatter，hash 只覆盖 Markdown 正文 | 原件和附件可被静默篡改 | 每个 snapshot 的 manifest 覆盖所有普通文件 |
| 只保存转换文本和外部绝对路径 | 原件丢失、路径泄露、无法复核 | 本地来源复制原件；locator 尽量稳定且脱敏 |
| Persona、查询和对话沉淀被强制要求 raw sources | Agent 会伪造来源或留空 | provenance 支持 raw/wiki/user-input/conversation |
| 任意来源内容没有 prompt injection 边界 | 文档可诱导 Agent 执行指令 | 所有摄入内容视为不可信数据；禁宏、脚本和权限扩张 |
| Agent 可无确认删除和批量重构 | 用户知识可能不可恢复 | 删除、10+ 文件或跨目录重构需计划、checkpoint 和确认 |
| “无 remote 所以 raw 可安全进 Git” | 父仓库或未来 remote 会泄露数据 | 初始化检查父 worktree；push/同步前重新确认文件集合 |

## 高严重度发现与处理

- `raw/wechat`、`raw/project`、`raw/assets` 混用来源、主题、介质分类轴。v3 只按已注册
  bucket 分类，每个 snapshot 自带 `original/content/assets`。
- 标签和转换偏好要求修改 Schema，与“Schema 修改先讨论”冲突。v3 全部放入 config。
- §9 要求未归档查询写日志，§12 又禁止。v3 只记录已归档查询。
- 摄入和汲取共用 `ingest`，无法审计 raw 何时冻结。v3 使用 `ingest` 与 `distill`。
- index 要更新 `Last updated/Total pages`，却没有初始化模板。v3 提供模板并定义计数。
- 所有页面至少两个出站链接会在空 vault 中制造断链。v3 只要求真实语义链接。
- “新来源通常胜出”忽略权威性和事件时间。v3 改为 claim 级争议与多因素判断。
- Lint 的孤立判断会被 index 链接永久掩盖。v3 排除导航链接后再判断。
- `search_files`、`shasum` 和 Agent 私有 memory 破坏 Agent 无关性。v3 使用能力描述和
  标准库脚本。
- 固定 `log-YYYY.md` 可能覆盖。v3 使用带 UTC 时间戳的不覆盖归档名。

## 独立复审追加修复

第一轮实现后又以独立代理和恶意 `/tmp` 样本做了负向复审，追加关闭：

- Agent 规则文件和 `manifest.json` 可被 symlink 冒充，以及 FIFO/device/socket 被忽略；
- `raw/`、`.staging/` 或 `wiki/` 根 symlink 导致 validator 读取 vault 外目录；
- 未注册 bucket、控制字符、hardlink 和伪造的顶层 `original` 文件；
- manual 空 locator 自环、断裂/分叉 supersedes 和依赖系统时钟的链排序；
- 来源 A→B→A 被错误去重为旧 A，丢失真实回滚事件；
- `profile` 路径越界、隐私开关和页面阈值类型未校验；
- 合法 Schema 修改后没有更新完整性状态的授权流程。

最终实现使用 `config.json` 进行无依赖结构校验，用 `state.json` 检测规则漂移，并提供
`record_schema_update.py` 记录经用户授权的 Schema 变更。

## 理论边界

Karpathy 明确具体目录与工具应按实例选择，因此 v2 的微信、项目、附件镜像和固定链接
数量都不应升级为普遍真理。Yarchi 的 IPOF 用于可变项目交付，与不可变 Raw 的语义
不同。本轮不把 IPOF 塞回核心树，而是保留其逐题访谈、纯文本、项目聚焦和最小权限
原则；需要时另建外部项目工作区。

## 仓库结构审查

`inputs/outputs/process` 表达创作阶段，不表达发布职责。v3 采用：

- `digital-brain-setup/`：独立发布包；
- `docs/sources/`：自有研究摘要；
- `docs/decisions/`：历史决策；
- `docs/reviews/`：审查证据；
- `tests/`：可复现验证。

历史设计记录保留原路径叙述，因为它们描述当时事实，不机械改写。

## 发布残余风险

1. 仓库没有许可证。本轮不擅自替维护者选择；GitHub 公开可见不等于开源授权。
2. canonical source URL 与第三方转载许可无法在当前环境核实，工作树已改为自有摘要。
3. Git 历史仍包含第三方全文。清理需要破坏性历史改写和强制推送，必须单独授权。
4. v2 vault 到 v3 snapshot 的迁移是破坏性数据迁移，本轮不自动执行。

## 本轮验证结果

- `python3 -m unittest discover -s tests -v`：19 项通过。
- `py_compile`：全部 Skill 脚本和测试通过（cache 定向到 `/tmp`）。
- Skill frontmatter、`agents/openai.yaml` 与 `config.json`：本地结构化解析通过。
- 自动测试包含隔离复制 Skill 后初始化和目标 vault 自校验。
- 独立前向测试完成访谈配置、画像/index/log、manual snapshot 冻结；冻结前后均为
  `0 个错误，0 个警告`，且未创建 Git 或修改仓库。
- `git diff --check`：通过；操作代码与 Skill 无旧 `outputs/` 路径。
- 官方 `quick_validate.py` 未运行：环境缺少 PyYAML，临时下载依赖被审批服务拒绝。
