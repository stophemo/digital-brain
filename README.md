# Digital Brain

一个用于搭建本地 LLM Wiki 的标准 Skill。它把用户选择的来源编译成持续演化、互相
链接且可追溯的 Markdown wiki，同时保留不可变的原始证据快照。

设计基础来自 Andrej Karpathy 的 LLM Wiki 模式，并吸收 Yarchi Second Brain 实践中
的逐题访谈、纯文本可移植性、项目聚焦与最小权限原则。

## 设计模型

```text
Schema    稳定运行规则，部署为 CLAUDE.md / AGENTS.md / GEMINI.md
Raw       带 manifest 和逐文件哈希的不可变来源快照
Wiki      Agent 持续维护的知识页面、链接、综合与争议记录
```

配置、staging、index 和 log 是运行支撑，不是新的知识层。

v3 解决了旧实现中的几个根本问题：

- Skill 自包含，不再引用包外的 `outputs/Schema.md`。
- 个性化标签和偏好移入 `.digital-brain/config.json`，Schema 可以稳定升级。
- 摄入采用 `.staging → 人工确认 → raw snapshot`，不再在 raw 中边改边冻结。
- 原件、标准化内容和附件共址；`manifest.json` 覆盖全部文件，而非只 hash Markdown。
- wiki provenance 支持 raw、wiki、用户访谈和对话沉淀。
- 查询日志、摄入/汲取动作、Lint 严重度和 Git 安全规则统一为可执行定义。

完整审查见 [标准化审查报告](docs/reviews/2026-07-16-standard-skill-review.md)。

## 仓库结构

```text
digital-brain-setup/               # 可独立安装的 Skill
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── Schema.md
│   └── templates/
└── scripts/
    ├── init_vault.py
    ├── finalize_snapshot.py
    ├── record_schema_update.py
    └── validate_vault.py
docs/
├── sources/                       # 自有研究摘要，不转载第三方全文
├── decisions/                     # Schema 演化记录
└── reviews/                       # 审查结果
tests/                             # 脚手架与快照完整性测试
AGENTS.md                          # 本仓库的开发规则
```

`digital-brain-setup/` 是唯一发布产物；复制该目录后仍应能独立完成初始化。

## 这个 Skill 什么时候用

`digital-brain-setup` 是**初始化 Skill**，用于把一个空目录搭建成 Digital Brain。通常只
调用一次。初始化完成后，在 vault 根目录启动 Agent，Agent 会自动读取根规则文件并
接管日常摄入、汲取、查询和 Lint，不需要每天再次调用 Setup Skill。

使用前确认：

- 目标目录必须不存在或为空；Skill 不覆盖、合并或迁移现有 vault。
- 本机有 Python 3.9 或更高版本；运行脚本只使用标准库。
- 先选择主要 Agent：Codex、Claude、Gemini 或自定义规则文件名。
- 初始化默认纯本地，不执行 `git init`，不添加 remote，不上传资料。

## 安装 Skill

### Codex：安装后自动触发

把整个 `digital-brain-setup/` 目录放入 Codex 的 Skills 目录。macOS/Linux 示例：

```bash
git clone https://github.com/stophemo/digital-brain.git
cd digital-brain

CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R digital-brain-setup "$CODEX_SKILLS_DIR/"
```

复制前确保 `$CODEX_SKILLS_DIR/digital-brain-setup` 不存在；升级时先备份或移走旧版本，
不要把两个版本合并。安装后新开一个 Codex 会话，即可通过
`$digital-brain-setup` 明确调用，也可以直接说“搭建我的第二大脑”。

### 不安装：让 Agent 显式读取

任何能读取文件和运行 Python 的 Agent 都可以直接执行本 Skill。在仓库目录中告诉它：

> 完整读取 `digital-brain-setup/SKILL.md`，按其中流程在 `~/digital-brain` 为 Codex
> 搭建 Digital Brain。访谈时一次只问一个问题。

Claude、Gemini 或其他 Agent 也使用这条方式，只需把“为 Codex”改成对应 Agent。
Skill 的打包格式遵循 Codex 标准；其他 Agent 是否能自动发现 Skill 取决于各自产品，
显式读取 `SKILL.md` 是通用兜底方式。

## 一句话初始化

安装后向 Agent 发送：

> 使用 `$digital-brain-setup` 在 `~/digital-brain` 搭建我的 Digital Brain。

Agent 会依次完成：

1. 询问目标目录和主要 Agent，检查目录冲突与父 Git remote。
2. 运行无覆盖初始化脚本，安装 `AGENTS.md`、`CLAUDE.md` 或 `GEMINI.md`。
3. 一次一个问题地访谈身份、目标、沟通偏好、领域、数据源、项目和隐私选择。
4. 写入 `config.json`、用户画像、项目索引、`index.md` 和 `log.md`。
5. 运行 vault 校验；有 Error 时先修复，不交付半成品。

如果目标位于已经配置 remote 的 Git worktree，Skill 会暂停并解释隐私风险。只有用户
明确同意后才会使用 `--allow-existing-git` 继续。

## 初始化结果

以 Codex 为例，最终目录类似：

```text
~/digital-brain/
├── AGENTS.md                       # 每次会话加载的 Digital Brain Schema
├── .digital-brain/
│   ├── config.json                 # 语言、标签、bucket、转换与隐私偏好
│   ├── state.json                  # 规则文件名与 Schema 校验值
│   └── scripts/                    # freeze、validate、Schema 更新记录工具
├── .staging/                       # 摄入审核前的可变暂存区
├── raw/                            # 确认后冻结的来源 snapshot
├── wiki/                           # Agent 维护的知识页
├── index.md                        # 内容导航
├── log.md                          # 只追加操作日志
└── logs/archive/                   # 日志归档
```

Claude 对应 `CLAUDE.md`，Gemini 对应 `GEMINI.md`。其余结构相同。

## 日常怎么用

先在 vault 根目录启动所选 Agent，确保它能加载根规则文件。然后直接用自然语言操作。

### 1. 摄入一份资料

示例：

> 摄入 `/Users/me/Documents/papers/raft.pdf`，放到 `papers` bucket。先展示转换结果，
> 不要自动汲取。

Agent 会复制原件到 `.staging/`，生成可读的 `content.md` 和附件，并展示路径、大小、
结构、转换缺失和隐私风险。原始文件只复制，不移动、不修改。

### 2. 审核后选择下一步

在 `.staging/` 检查结果，必要时直接修改暂存内容，然后回复：

| 回复 | 结果 |
|------|------|
| `确认摄入` | 生成 `manifest.json` 和逐文件 SHA-256，冻结进 `raw/`，然后暂停 |
| `继续汲取` | 先冻结进 `raw/`，再讨论关键收获并更新 wiki |
| 指出问题 | 继续修改 `.staging/`，不进入 raw |

冻结后的 snapshot 只读。来源发生变化时会创建新 snapshot，并通过 `supersedes` 连接
旧版本；不会原地覆盖。

### 3. 查询 wiki

直接提问：

> 基于我的 wiki，总结 Raft 和 Multi-Paxos 的核心差异，并标出证据来源。

Agent 先读 `index.md` 定位页面，再综合回答。新的对比、综合或可复用答案可以归档回
`wiki/comparisons/`、`wiki/syntheses/` 或 `wiki/queries/`。

### 4. 沉淀对话结论

> 把刚才确定的论文阅读方法沉淀到 wiki。

Agent 会先确认，再创建或更新 concept/query 页面，记录 `conversation` provenance，
同步 index 和 log。

### 5. 健康检查

> lint

或：

> 检查 wiki 健康度，并给出每个问题的文件路径和修复建议。

Lint 会检查 raw hash、manifest、断链、provenance、index、标签、争议、孤立页、页面
体积、版本链和 staging 遗留。raw 完整性失败只报告并要求重新摄入，不自动修补。

## 三个容易混淆的概念

| 概念 | 输入 | 输出 | 是否可修改 |
|------|------|------|------------|
| 摄入 | 外部文件、URL、连接器或手工内容 | 带 manifest 的 raw snapshot | staging 可改；冻结后不可改 |
| 汲取 | 已冻结 raw snapshot | wiki 知识页、链接、index、log | Agent 持续维护 |
| 查询/沉淀 | wiki 与当前对话 | 回答，或新的 comparison/synthesis/query/concept | 归档前由用户决定 |

## 用户和 Agent 各负责什么

| 用户 | Agent |
|------|-------|
| 选择值得长期保留的来源 | 转换、归档和维护 snapshot |
| 审核摄入结果 | 提炼知识、更新相关页面和链接 |
| 判断重点与争议 | 维护 provenance、index、log 和一致性 |
| 决定是否外传、使用 Git 或第三方服务 | 默认本地、最小权限并在越界前暂停确认 |

## 手动运行脚本

正常使用时由 Agent 调用脚本。排错或只验证脚手架时可以手动运行。

### 初始化空 vault

```bash
python3 digital-brain-setup/scripts/init_vault.py /tmp/my-brain --agent codex
python3 /tmp/my-brain/.digital-brain/scripts/validate_vault.py /tmp/my-brain
```

Agent 与规则文件映射：

| 参数 | 规则文件 |
|------|----------|
| `--agent codex` | `AGENTS.md` |
| `--agent claude` | `CLAUDE.md` |
| `--agent gemini` | `GEMINI.md` |
| `--agent other --rule-file RULES.md` | `RULES.md` |

### 冻结已审核的 staging

本地文件来源必须在 `<staging>/original/` 中保留原件副本：

```bash
python3 <vault>/.digital-brain/scripts/finalize_snapshot.py \
  --vault <vault> \
  --staging <vault>/.staging/<task> \
  --bucket papers \
  --slug raft-paper \
  --source-kind file \
  --source-locator paper:raft-2014
```

同一 locator 的内容变化时，脚本会要求用 `--supersedes` 指向上一版
`raw/<bucket>/<snapshot-id>/manifest.json`。内容与最新版本完全相同时复用最新 snapshot。

### 记录经授权的 Schema 修改

只有用户明确同意修改 vault 根规则文件后才运行：

```bash
python3 <vault>/.digital-brain/scripts/record_schema_update.py <vault>
```

该命令只更新 `state.json` 的规则校验值，不修改 Schema 内容；随后还要追加 `config`
日志。

## 安全边界与限制

- 来源中的提示词、宏、脚本和权限请求都视为不可信数据，不执行。
- 上传外部 API、联网转换、安装依赖、写 vault 外路径前必须获得用户许可。
- `raw/`、个人画像和绝对路径可能敏感；Git、云盘和 `.gitignore` 都不是加密。
- Setup 只支持空目录；v2 vault 到 v3 snapshot 没有自动迁移器。
- Office、PDF、音视频等实际转换能力取决于当前 Agent 可用的本地工具；Skill 负责
  状态机、安全门和结果契约，不捆绑大型转换依赖。
- 默认不初始化 Git。即使只做本地 Git，也应先确认目标是否位于带 remote 的父仓库。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile digital-brain-setup/scripts/*.py
python3 /path/to/skill-creator/scripts/quick_validate.py digital-brain-setup
```

最后一项来自 Codex `skill-creator`，运行环境需要 PyYAML。仓库测试不依赖第三方 Python
包，并覆盖独立安装、拒绝覆盖、Git remote 保护、快照冻结、重复检测和篡改发现。

## 理论来源与许可

研究摘要见 [docs/sources](docs/sources/README.md)。canonical URL 或转载许可未确认前，
本仓库不再收录第三方文章全文或完整翻译。

本仓库尚未声明代码许可证。公开 GitHub 仓库不等于自动授予开源使用权；许可证应由
仓库维护者明确选择后单独添加。
