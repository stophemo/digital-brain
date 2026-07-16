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

## 使用

把 `digital-brain-setup/` 安装到所用 Agent 的 Skill 目录后调用：

> 使用 `$digital-brain-setup` 在 `~/digital-brain` 搭建我的 Digital Brain。

Skill 会先做目标目录和 Git remote 预检，再创建脚手架、安装对应 Agent 规则文件，
一次一个问题地访谈用户，最后生成配置、画像、index 和 log 并运行验证。

只测试基础脚手架时可以直接运行：

```bash
python3 digital-brain-setup/scripts/init_vault.py /tmp/my-brain --agent codex
python3 /tmp/my-brain/.digital-brain/scripts/validate_vault.py /tmp/my-brain
```

初始化脚本只接受空目录，不覆盖现有 vault，不执行 `git init`，不添加 remote，也不
复制任何用户来源。

## 日常循环

1. **摄入**：提供文件或 URL；Agent 复制到 `.staging/`，在本地转换并展示结果。
2. **确认**：用户明确确认后，脚本生成 manifest 并原子冻结到 `raw/`。
3. **汲取**：Agent 与用户确认重点，再更新 wiki、provenance、index 和 log。
4. **查询**：从 wiki 综合答案；有长期价值的结果归档回 wiki。
5. **Lint**：校验 raw 哈希、断链、provenance、index、争议、孤立和配置一致性。

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
