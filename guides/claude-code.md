# Claude Code：一句话安装并搭建 Digital Brain

在 Claude Code 中复制下面这一句话即可：

```text
请将 https://github.com/stophemo/digital-brain 克隆到临时目录，完整阅读仓库中的 guides/claude-code.md，检查下载内容和安装脚本后，在仓库根目录运行 python3 scripts/install_skill.py claude；如安装位置已有不同版本，请先说明情况并询问我，未经确认不要覆盖；需要联网或写入 Claude 配置目录时请主动申请审批；安装成功后不要结束当前会话，请完整读取已安装的 digital-brain-setup/SKILL.md，严格按其中流程逐题访谈我，并为我搭建可以立即使用的 Digital Brain。
```

## 会发生什么

Claude Code 会：

1. 请求联网权限，从 GitHub 下载仓库到临时目录。
2. 检查安装内容，再把 Skill 安装到 Claude Code 的 skills 目录。
3. 若发现不同版本，停下来征求你的确认，不会直接覆盖。
4. 完整读取安装后的 `SKILL.md`，一次只问一个问题。
5. 根据你的回答创建 vault，并带你完成第一次使用。

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

如果新会话没有自动识别 Skill，请明确说“使用 `digital-brain-setup` Skill”，或重启一次 Claude Code。

## 手动安装兜底

自动安装不可用时，先克隆仓库并进入仓库根目录：

```bash
git clone https://github.com/stophemo/digital-brain.git
cd digital-brain
```

检查安装脚本后执行：

```bash
python3 scripts/install_skill.py claude
```

然后启动 Claude Code，并说：

```text
请完整读取已安装的 digital-brain-setup/SKILL.md，逐题访谈我，并为我搭建 Digital Brain。
```
