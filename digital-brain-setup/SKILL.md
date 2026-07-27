---
name: digital-brain-setup
description: 新建、初始化或首次配置本地 Digital Brain 知识库，并教会用户开始使用。用户要求从零创建数字大脑、第二大脑、个人 wiki 或知识 vault 时使用；负责创建简单的 inbox、raw、wiki 和 index 结构，安装 Agent 规则，通过简短访谈生成个人画像，并邀请用户完成第一次知识摄入。不要因查询、整理或维护已有知识库而触发。
---

# Digital Brain Setup

把一个空目录初始化为简单、可读、可持续使用的本地知识库。目标是让用户几分钟内
完成搭建并马上学会使用，而不是建立复杂的知识管理基础设施。

## 资源

以当前 Skill 目录为 `<skill-dir>`：

- `assets/Schema.md`：复制为目标 vault 的 Agent 规则文件。
- `assets/templates/START-HERE.md`：面向用户的上手教程。
- `assets/templates/profile.md`：访谈结果模板。
- `assets/templates/index.md`：知识导航模板。
- `scripts/init_vault.py`：无覆盖地创建基础目录和文件。

不要依赖 Skill 目录之外的仓库文件。

## 工作流

### 1. 确认位置和 Agent

一次只问一个问题：

1. vault 放在哪里；默认 `<当前目录>/digital-brain`。
2. 主要使用哪个 Agent：Codex、Claude、Gemini 或其他。

目标必须不存在或为空。目标已包含文件时停止，不覆盖、不合并。若目标位于带 remote
的 Git 仓库、云盘或同步目录，先提醒 `raw/` 和 `profile.md` 可能包含私人信息，获得
明确确认后再继续。

不要自动执行 `git init`、添加 remote、上传资料、安装依赖或调用外部服务。

### 2. 做一次简短访谈

严格一次问一个问题；用户说“跳过”时采用通用默认值：

1. 你建立 Digital Brain 最想解决什么问题？
2. 你希望长期积累哪些领域、兴趣或项目知识？
3. 你通常会放入哪些资料，例如文章、PDF、会议记录或个人想法？
4. 你喜欢 Agent 怎样沟通，例如简洁、详细、先给结论或多举例？

只记录用户明确提供的信息。不要收集或写入密码、token、身份证号等秘密。

### 3. 初始化

在 `<skill-dir>` 中运行：

```bash
python3 scripts/init_vault.py <vault> --agent codex
```

Agent 映射：

- Codex：`AGENTS.md`
- Claude：`CLAUDE.md`
- Gemini：`GEMINI.md`

其他 Agent 使用：

```bash
python3 scripts/init_vault.py <vault> --agent other --rule-file <规则文件名.md>
```

### 4. 写入个人画像

根据访谈回答更新 `<vault>/profile.md`：

- 写清主要目标、关注领域、常见资料和沟通偏好。
- 保留用户没有回答的部分为“待补充”，不要猜测。
- 只写长期有用的信息，不写完整对话或敏感细节。

不要个性化改写 Agent 规则文件；日后用户可以直接维护 `profile.md`。

### 5. 验证

确认以下结果存在：

```text
<vault>/
├── <Agent 规则文件>
├── START-HERE.md
├── profile.md
├── index.md
├── inbox/
├── raw/
└── wiki/
```

确认生成结果只包含上述轻量结构，没有额外隐藏状态目录或后台服务。初始化过程不应
创建 Git 仓库，也不应复制任何用户资料。

### 6. 带用户开始

报告 vault 路径和规则文件名，提醒用户先阅读 `START-HERE.md`。如果用户尚未提供第一
份资料，只问：

> 现在要提供第一份资料，完成一次 `raw → wiki → index`，还是稍后再开始？

用户选择稍后开始时，给出一个可复制的摄入提示词后结束搭建。用户已经提供资料或选择
现在开始时，获取一份资料路径或网址，先说明将进行的复制和整理动作，再按 vault 规则
完成第一次 `raw → wiki → index`，让用户看到完整闭环。
