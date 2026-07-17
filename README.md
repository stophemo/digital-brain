# Digital Brain Setup

一个帮助你快速搭建个人数字大脑的开源 Skill。

它会引导你创建一个简单、可读、可迁移的本地知识库，让 Claude Code、Codex 等
Agent 帮你收集资料、整理知识、建立关联并持续复盘。你不需要先学习复杂的知识管理
方法，也不需要从零设计目录。

## 一句话安装并搭建

准备 Git、Python 3.9+，以及 Codex 或 Claude Code。选择你使用的 Agent，把对应的
整段提示词复制进去即可；Agent 会自行下载、检查、安装，然后直接开始逐题访谈。

### Codex

```text
请将 https://github.com/stophemo/digital-brain 克隆到临时目录，完整阅读仓库中的 guides/codex.md，检查下载内容和安装脚本后，在仓库根目录运行 python3 scripts/install_skill.py codex；如安装位置已有不同版本，请先说明情况并询问我，未经确认不要覆盖；需要联网或写入 Codex 配置目录时请主动申请审批；安装成功后不要结束当前会话，请完整读取已安装的 digital-brain-setup/SKILL.md，严格按其中流程逐题访谈我，并为我搭建可以立即使用的 Digital Brain。
```

完整说明见 [Codex 教程](guides/codex.md)。

### Claude Code

```text
请将 https://github.com/stophemo/digital-brain 克隆到临时目录，完整阅读仓库中的 guides/claude-code.md，检查下载内容和安装脚本后，在仓库根目录运行 python3 scripts/install_skill.py claude；如安装位置已有不同版本，请先说明情况并询问我，未经确认不要覆盖；需要联网或写入 Claude 配置目录时请主动申请审批；安装成功后不要结束当前会话，请完整读取已安装的 digital-brain-setup/SKILL.md，严格按其中流程逐题访谈我，并为我搭建可以立即使用的 Digital Brain。
```

完整说明见 [Claude Code 教程](guides/claude-code.md)。

安装时 Agent 通常会请求联网访问 GitHub，以及写入个人 Skills 目录。确认仓库地址和
目标路径正确后再批准即可。初始化只面向不存在或为空的 vault，不会覆盖已有知识库。

## 你会得到什么

首次搭建完成后，你的 Digital Brain 大致如下：

```text
digital-brain/
├── AGENTS.md 或 CLAUDE.md   # Agent 的工作规则
├── START-HERE.md            # 第一次使用指南
├── profile.md               # 你的目标、领域与使用偏好
├── inbox/                   # 暂时还没整理的资料
├── raw/                     # 保留的原始资料
├── wiki/                    # 整理后的知识页面
└── index.md                 # 整个知识库的导航入口
```

所有核心内容都是普通文件和 Markdown。你可以直接阅读、编辑、备份或迁移，不会被
绑定到某个应用。

## 第一次搭建

Setup Agent 会用几个简短问题了解你的使用目标、关注领域和偏好，把访谈结果写入
`profile.md`，然后创建知识库和对应的 Agent 规则。完成后，进入新目录重新启动你
选择的 Agent：

```bash
cd ~/digital-brain
codex
```

如果使用 Claude Code，把最后一行换成 `claude`。接着先阅读 `START-HERE.md`，或者
直接对 Agent 说：

> 带我完成第一次使用，并告诉我应该把现有资料放在哪里。

Setup Skill 只负责首次搭建。之后只需在 Digital Brain 目录中和 Agent 对话，不必
重复调用 Skill。

## 日常工作流

Digital Brain 的主线只有四步：

```text
inbox  →  raw  →  wiki  →  index.md
待整理    原始资料   提炼后的知识   导航与入口
```

1. **收集到 `inbox/`**：先把文章、笔记、PDF 或临时想法放进来，不要求当场分类。
2. **整理到 `raw/`**：让 Agent 按主题保存原始资料，保留上下文和来源信息。
3. **沉淀到 `wiki/`**：让 Agent 提炼观点、概念和方法，并与已有页面建立链接。
4. **更新 `index.md`**：让重要知识出现在导航中，之后可以按主题快速找到。

例如，把资料放进 `inbox/` 后可以直接说：

> 整理 inbox：保留原始资料，提炼成 wiki 页面，建立相关链接并更新 index。

你始终可以先让 Agent 展示计划或草稿，再决定是否修改文件。

## 可直接复制的提示词

1. 首次熟悉知识库：

   > 介绍这个 Digital Brain 的目录，并带我完成一次最简单的资料整理。

2. 清理收件箱：

   > 查看 inbox 中有哪些内容，先给出整理计划，我确认后再执行。

3. 摄入一份资料：

   > 整理 inbox 中的这份资料：保留原文，提炼关键知识，更新相关 wiki 和 index。

4. 记录一个想法：

   > 把下面的想法记录下来，并告诉我它与现有知识有什么联系：……

5. 查询已有知识：

   > 基于我的 Digital Brain 回答这个问题，并注明参考了哪些页面：……

6. 建立知识关联：

   > 找出 wiki 中关于“……”的相关页面，补充必要的双向链接，不要改写原意。

7. 沉淀当前对话：

   > 总结我们刚才确定的结论，先展示草稿，确认后沉淀到 wiki 并更新 index。

8. 每周复盘：

   > 帮我做本周知识复盘：总结新增内容、重要关联、待处理资料和下一步行动。

9. 发现知识缺口：

   > 检查当前 wiki，找出重复、孤立或缺少依据的内容，并给出改进建议。

## 隐私提醒

- Digital Brain 默认是本地目录，但本地文件不等于已加密。
- 放入身份证件、密钥、健康资料或工作机密前，请先判断风险。
- 使用 Git、云盘、在线模型或第三方转换服务前，确认哪些内容会被同步或上传。
- 提交公开仓库前，检查 `raw/`、`inbox/`、个人偏好和文件路径中是否含有隐私。
- 来源资料中的提示词、脚本或操作要求只是资料内容，不应被 Agent 直接执行。

## 仓库说明

普通用户只需要安装 `digital-brain-setup/`，其他目录不用阅读：

```text
digital-brain-setup/   可独立安装的 Skill（包含 MIT License）
guides/                Codex 与 Claude Code 的独立教程
scripts/               双平台 Skill 安装入口
tests/                 发布前的行为测试
AGENTS.md              仓库维护规则
LICENSE                MIT 开源许可证
```

## 开发与验证

修改 Skill 后至少运行：

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile digital-brain-setup/scripts/*.py scripts/*.py
python3 /path/to/skill-creator/scripts/quick_validate.py digital-brain-setup
```

项目脚本仅使用 Python 标准库。`quick_validate.py` 来自 Codex 的 `skill-creator`。

## License

本项目使用 [MIT License](LICENSE)。
