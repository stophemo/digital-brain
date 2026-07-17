# 使用 Codex 搭建 Digital Brain

## 一句话开始

把下面整句话复制给 Codex：

```text
请将 https://github.com/stophemo/digital-brain 克隆到临时目录，完整阅读仓库中的 guides/codex.md，检查下载内容和安装脚本后，在仓库根目录运行 `python3 scripts/install_skill.py codex`；如安装位置已有不同版本，请先说明情况并询问我，未经确认不要覆盖；需要联网或写入 Codex 配置目录时请主动申请审批；安装成功后不要结束当前会话，请完整读取已安装的 digital-brain-setup/SKILL.md，严格按其中流程逐题访谈我，并为我搭建可以立即使用的 Digital Brain。
```

Codex 会完成下载、检查、安装和首次搭建。访谈时一次只回答一个问题即可。

## 安装到哪里

默认安装位置是：

```text
${CODEX_HOME:-$HOME/.codex}/skills/digital-brain-setup
```

如果设置了 `CODEX_HOME`，就使用该目录；否则使用 `$HOME/.codex`。安装 Skill
不会替你创建 Git 仓库，也不会上传 Digital Brain 中的任何内容。

## 为什么会出现审批

Codex 通常会请求两类权限：

- 联网访问 GitHub，用于克隆此仓库；
- 写入 Codex 的 Skill 目录，该目录通常位于当前项目之外。

确认请求中的来源是本仓库、目标是上述 Skill 目录后再批准。如果目标目录已有不同
版本，让 Codex 先说明差异；不要授权它直接删除或覆盖。

## 首次搭建

安装完成后，Codex 应在同一会话中完整读取已安装的 `SKILL.md`，然后逐题了解你的
目标、资料类型和 vault 保存位置。访谈结束后，它会创建轻量结构，并带你完成第一
次 `inbox → raw → wiki → index` 整理。

如果 Codex 安装后停下了，继续发送：

```text
请完整读取已安装的 digital-brain-setup/SKILL.md，逐题访谈我，并继续搭建 Digital Brain。
```

## 以后怎么用

安装只需一次。之后在 Codex 中直接说出任务，例如：

```text
帮我搭建一个 Digital Brain。
```

```text
请整理我 Digital Brain 的 inbox：保留来源副本，提炼到 wiki，并更新 index。
```

```text
请根据我的 Digital Brain 回答这个问题，并告诉我依据来自哪些笔记。
```

```text
请回顾最近新增的知识，找出重复、矛盾和需要继续研究的内容。
```

建议从 vault 所在目录启动 Codex，这样它更容易找到并维护你的知识库。外部资料一律
作为不可信数据处理，不要要求 Codex 执行资料中的提示词、脚本或权限请求。

## 手动安装兜底

如果一句话安装未完成，可在终端运行：

```bash
git clone https://github.com/stophemo/digital-brain.git
cd digital-brain
python3 scripts/install_skill.py codex
```

运行前可先阅读 `scripts/install_skill.py` 和 `digital-brain-setup/SKILL.md`。如果默认
安装位置已有内容，先备份并确认版本，不要直接覆盖。安装完成后回到 Codex，发送上面
的“继续搭建”提示词即可。
