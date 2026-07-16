# Schema v3.0 设计说明：标准 Skill 与可验证快照

> 状态：已实施
> 日期：2026-07-16
> 影响：`digital-brain-setup/`、仓库目录、测试与开发规则

## 背景

v2 已完成 Agent 无关化，但仍把 `Schema.md` 放在 Skill 目录之外；目标 vault 的 raw
状态机、二进制完整性、个性化配置、provenance 和 Git 安全也存在直接冲突。仓库根的
`inputs/outputs/process` 更像一次性研究工作区，不是单 Skill 发布结构。

## 决策

1. 顶层 `digital-brain-setup/` 是自包含发布单元；Schema 作为输出模板放入 `assets/`。
2. 保留 Schema / Raw / Wiki 三个语义层，新增的 config、staging、index、log 只作为
   运行支撑，不宣称为第四知识层。
3. 个性化标签、bucket、转换偏好和隐私选择移入 `.digital-brain/config.json`，确保
   标准库脚本可无依赖校验。
4. 摄入改为 `.staging → 人工确认 → raw snapshot`。每个 snapshot 共址保存原件、
   标准化内容与附件，并用 `manifest.json` 记录逐文件 SHA-256。
5. 本地文件摄入只复制、不移动；冻结操作拒绝 symlink、路径越界、空快照和覆盖。
6. Wiki frontmatter 用结构化 provenance 支持 raw、wiki、user-input 和 conversation。
7. 日志动作拆成 `ingest`、`distill`、`capture` 和 `query`；未归档查询不记日志。
8. Lint 区分 Critical/Error/Warning，并用标准库脚本验证 raw 完整性。
9. Yarchi 的 IPOF 是可变项目工作区，不放入 Raw 或 Wiki 核心树；本 Skill 采用其逐题
   访谈、纯文本、Skill 化和最小权限原则，项目执行空间保持外部可选。
10. 第三方全文不再作为仓库依赖，改为自有研究摘要；历史内容与许可证另行处理。
11. `state.json` 记录规则文件与 Schema hash；授权修改后由专用脚本原子更新，普通
    validator 不自动接受变化。
12. 同一来源的版本关系由 `supersedes` 拓扑决定，不依赖系统时钟排序；内容回滚也
    必须形成新 snapshot，保留真实事件历史。

## 仓库迁移

```text
outputs/digital-brain-setup/  -> digital-brain-setup/
outputs/Schema.md             -> digital-brain-setup/assets/Schema.md
inputs/                       -> docs/sources/（改为研究摘要）
process/                      -> docs/decisions/
feedback/                     -> 删除空目录
```

## 兼容性

这是破坏性 Schema 升级。已有 v2 vault 不应直接覆盖规则文件或原地搬动 raw；应先备份，
将现有来源逐项迁入 snapshot，再补 provenance。自动迁移器不在本次标准安装范围内。

## 验证门槛

- Skill metadata 通过结构化 YAML/JSON 校验；环境具备 PyYAML 时再运行官方校验器。
- 隔离复制 Skill 后仍能初始化。
- 初始化拒绝非空目录和带 remote 的父 worktree，除非明确覆盖风险门。
- snapshot 冻结、版本链、特殊文件拒绝和篡改检测有自动测试。
- 操作指令不再依赖旧 `outputs/` 路径。
