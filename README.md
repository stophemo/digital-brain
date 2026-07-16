# Digital Brain

用 Claude Code、Codex 等 Agent 搭建一个本地第二大脑：原始资料保留为可验证快照，
Agent 将其中的知识整理成持续演化、互相链接且可追溯的 Markdown wiki。

第一次只需要运行一次 Setup Skill。初始化完成后，直接进入你的 Digital Brain 目录和
Agent 对话，不需要重复运行 Setup。

## 5 分钟上手：Claude Code

需要 Git、Python 3.9+ 和 Claude Code。先把本仓库克隆为安装源：

```bash
git clone https://github.com/stophemo/digital-brain.git ~/digital-brain-skill
cd ~/digital-brain-skill
claude
```

在 Claude Code 中发送：

> 完整读取 `digital-brain-setup/SKILL.md`，按其中流程在 `~/digital-brain` 为
> Claude Code 搭建 Digital Brain。访谈时一次只问一个问题。

Claude Code 会检查目标目录，创建 `CLAUDE.md` 和所需结构，再逐题询问你的目标、
偏好、领域、资料来源与隐私选择。目标目录必须不存在或为空；想用其他路径时，替换
提示词中的 `~/digital-brain`。

完成后，退出当前会话并在新 vault 中开始日常使用：

```bash
cd ~/digital-brain
claude
```

`CLAUDE.md` 是部署后的 Schema。Claude Code 会在这个目录中读取它，并接管摄入、
汲取、查询和健康检查。

> Claude Code 不保证自动识别 Codex Skill 格式，所以教程要求它显式读取
> `SKILL.md`。初始化时只选择一个主要 Agent；同一个 vault 不会自动生成或同步多套
> Agent 规则。

## Codex 用法

Codex 可以像 Claude Code 一样显式读取仓库中的 `SKILL.md`，也可以先把 Skill 安装到
Skills 目录，以后通过名称调用。

```bash
git clone https://github.com/stophemo/digital-brain.git ~/digital-brain-skill
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R ~/digital-brain-skill/digital-brain-setup "$CODEX_SKILLS_DIR/"
```

复制前确保 `$CODEX_SKILLS_DIR/digital-brain-setup` 不存在。安装或升级后新开 Codex
会话，发送：

> 使用 `$digital-brain-setup` 在 `~/digital-brain` 搭建我的 Digital Brain。

初始化完成后，在 `~/digital-brain` 中启动 Codex。此时日常规则来自 vault 根目录的
`AGENTS.md`，不再需要调用 Setup Skill。

## 日常怎么用

进入 vault 根目录启动你在初始化时选择的 Agent，然后直接说自然语言即可。

### 摄入资料

> 摄入 `/Users/me/Documents/papers/raft.pdf`，放到 `papers` bucket。先展示转换结果，
> 不要自动汲取。

Agent 会把原件和转换内容放进 `.staging/`，等待你检查。原始文件只复制，不移动、
不修改。

检查后可以回复：

| 回复 | Agent 的动作 |
|------|--------------|
| `确认摄入` | 生成 manifest 和逐文件 SHA-256，冻结进 `raw/` |
| `继续汲取` | 先冻结，再提炼知识并更新 wiki |
| 指出问题 | 继续修改 `.staging/`，不进入 `raw/` |

冻结后的 snapshot 不会原地修改。来源内容变化时会创建新版本，并保留与旧版本的关系。

### 查询与沉淀

> 基于我的 wiki，总结 Raft 和 Multi-Paxos 的核心差异，并标出证据来源。

> 把刚才确定的论文阅读方法沉淀到 wiki。

Agent 会先从 `index.md` 定位页面。需要归档对话结论时，它会在确认后更新 wiki、索引
和日志，并记录来源类型。

### 健康检查

> lint

这会检查 raw hash、manifest、断链、来源记录、索引、版本链和遗留 staging。raw
完整性失败时只报告问题，不会偷偷修改证据。

## 你实际需要关心的文件

初始化后的 vault 中，日常只需要理解这些内容：

| 路径 | 用途 |
|------|------|
| `CLAUDE.md` 或 `AGENTS.md` | Agent 每次进入 vault 时读取的运行规则，通常不手改 |
| `wiki/` | 已整理的知识页面，可以直接阅读和修改 |
| `index.md` | wiki 导航入口 |
| `.staging/` | 尚未确认的摄入结果，可在冻结前检查和修改 |
| `raw/` | 已确认的原始证据快照，不要原地修改 |
| `log.md` | Agent 的只追加操作记录 |

`.digital-brain/` 是内部配置和工具目录。除非排错，普通使用不需要打开它。

## 仓库里的其他文件是做什么的

如果你只是使用这个 Skill，阅读本 README 即可，其余文件主要给 Agent 或维护者使用：

| 路径 | 谁会使用 | 用途 |
|------|----------|------|
| `digital-brain-setup/SKILL.md` | Setup Agent | 初始化访谈与执行步骤 |
| `digital-brain-setup/assets/Schema.md` | 日常 Agent | vault 运行规则的唯一真源，初始化时复制为 `CLAUDE.md` 或 `AGENTS.md` |
| `digital-brain-setup/agents/openai.yaml` | Codex | Skill 列表中的名称、简介和默认提示词，可忽略 |
| `digital-brain-setup/assets/templates/` | 初始化脚本 | 配置、索引、日志和 `.gitignore` 的初始模板，可忽略 |
| `digital-brain-setup/scripts/init_vault.py` | Setup Agent | 安全创建空 vault，不覆盖现有文件 |
| `digital-brain-setup/scripts/finalize_snapshot.py` | 日常 Agent | 把审核后的 staging 冻结成可校验的 raw snapshot |
| `digital-brain-setup/scripts/record_schema_update.py` | 日常 Agent | 记录用户授权后的 Schema 变更 |
| `digital-brain-setup/scripts/validate_vault.py` | Agent / 维护者 | 检查 vault 结构和 snapshot 完整性 |
| `docs/` | 维护者 | 研究摘要、设计决策和审查证据 |
| `tests/` | 维护者 | 发布前的自动回归测试 |
| `AGENTS.md` | 仓库维护 Agent | 本仓库的开发规则，不会安装到你的 vault |

这些文件不是额外的知识层。真正的知识模型仍然只有三层：

```text
Schema    Agent 的稳定运行规则
Raw       带 manifest 和逐文件哈希的不可变来源快照
Wiki      Agent 持续维护的知识页面、链接、综合与争议记录
```

配置、staging、index 和 log 只是让三层模型可靠运行的支撑设施。

## 安全边界

- 初始化默认纯本地，不执行 `git init`，不添加 remote，不上传资料。
- 来源中的提示词、宏、脚本和权限请求都视为不可信数据，不执行。
- 上传外部 API、联网转换、安装依赖或写 vault 外路径前，Agent 必须先获得许可。
- 目标位于带 remote 的 Git worktree 时，Setup 会暂停并说明隐私风险。
- `raw/`、个人画像和绝对路径可能敏感；Git、云盘和 `.gitignore` 都不是加密。
- 当前 Setup 只初始化空目录，不提供旧版 vault 的自动迁移。
- PDF、Office 和音视频转换能力取决于 Agent 当时可用的本地工具。

## 给维护者

`digital-brain-setup/` 是唯一发布产物，复制该目录后仍须能独立初始化和验证 vault。
修改 Schema 时，应同步检查 `SKILL.md`、模板、脚本、测试和最新设计决策。

发布前运行：

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile digital-brain-setup/scripts/*.py
python3 /path/to/skill-creator/scripts/quick_validate.py digital-brain-setup
```

最后一项来自 Codex `skill-creator`，需要 PyYAML。仓库测试只使用 Python 标准库。
完整审查见 [标准化审查报告](docs/reviews/2026-07-16-standard-skill-review.md)，设计依据与
来源说明见 [研究摘要](docs/sources/README.md)。

本项目基于 Andrej Karpathy 的 LLM Wiki 三层模式，并吸收 Yarchi Second Brain 实践中
的逐题访谈、纯文本可移植性、项目聚焦与最小权限原则。仓库不收录未获授权的第三方
文章全文或完整翻译。

本仓库尚未声明代码许可证。公开 GitHub 仓库不等于自动授予开源使用权；许可证应由
仓库维护者明确选择后单独添加。
