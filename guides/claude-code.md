# Claude Code：一句话安装并搭建 Digital Brain

在 Claude Code 中复制下面这一句话即可：

```text
请从 https://github.com/stophemo/digital-brain/releases 获取最新的非草稿、非预发布正式版本，记录它的 tag，把该 tag 的源码下载或克隆到临时目录，并确认检出的 HEAD 正是该 tag 指向的 commit；如果没有正式 Release，请停止并告诉我，不要改用 main；完整阅读该版本中的 guides/claude-code.md，检查下载内容和安装脚本后，在仓库根目录运行 python3 scripts/install_skill.py claude；如安装位置已有不同版本，请先说明情况并询问我，未经确认不要覆盖；需要联网或写入 Claude 配置目录时请主动申请审批；安装成功后不要结束当前会话，请完整读取已安装的 digital-brain-setup/SKILL.md，严格按其中流程逐题访谈我，并为我搭建可以立即使用的 Digital Brain。
```

## 会发生什么

Claude Code 会：

1. 请求联网权限，从 GitHub 下载最新正式 Release 到临时目录；没有正式版本时停止。
2. 检查安装内容，再把 Skill 安装到 Claude Code 的 skills 目录。
3. 若发现不同版本，停下来征求你的确认，不会直接覆盖。
4. 完整读取安装后的 `SKILL.md`，一次只问一个问题。
5. 根据你的回答创建 vault，并询问现在完成第一次知识整理，还是稍后开始。

默认安装位置是：

```text
~/.claude/skills/digital-brain-setup
```

如果设置了 `CLAUDE_CONFIG_DIR`，则使用：

```text
$CLAUDE_CONFIG_DIR/skills/digital-brain-setup
```

安装时出现联网或写入上述目录的审批提示属于正常现象。确认请求的仓库地址和目标路径无误后再批准。

## 日常使用

以后进入你的 vault，再启动 Claude Code：

```bash
cd /你的/Digital-Brain/路径
claude
```

你可以直接说：

- “整理 `inbox/` 里的新资料。”
- “把这篇资料保存到 `raw/`，再整理成一篇 wiki。”
- “根据现有 wiki 回答这个问题，并标出来源。”
- “更新 `index.md`，让我快速看到最近积累了什么。”

日常使用无需再次调用 `digital-brain-setup`。如果 Claude Code 没有遵循知识库规则，
确认从 vault 根目录启动，并让它先读取根目录的 `CLAUDE.md`。

## 手动安装兜底

自动安装不可用时，打开 [GitHub Releases](https://github.com/stophemo/digital-brain/releases/latest)，
确认页面显示的是正式版本，然后下载页面中的 Source code 并解压。不要从 `main`
下载源码。进入解压后的仓库根目录，检查安装脚本后执行：

```bash
python3 scripts/install_skill.py claude
```

然后启动 Claude Code，并说：

```text
请完整读取已安装的 digital-brain-setup/SKILL.md，逐题访谈我，并为我搭建 Digital Brain。
```
