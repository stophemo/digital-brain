# Yarchi Second Brain 实践研究笔记

> 来源：Yarchi，*How to Build an AI Second Brain With Claude and Obsidian That Gets Smarter Every Day*。
> 本文是项目维护者的概括，不是原文转载；canonical URL 与许可待核实。

## 可复用实践

- 知识资产使用本地纯文本，避免绑定单一模型或产品。
- 初始化时让 Agent 一次只问一个问题，建立用户画像、目标、沟通偏好和当前项目。
- 项目执行采用 Inputs / Process / Outputs / Feedback 的聚焦结构，并在工作时只打开
  当前项目，减少无关上下文。
- 重复工作整理成 Skill，明确触发条件和固定流程。
- 对日历、邮箱、Slack 等实时数据使用最小权限，能只读就只读。
- 定时自动化应在人工跑通流程后再启用。
- “靠权限，不靠提示词”：Prompt 不能替代文件系统、密钥或连接器权限。

## 与 LLM Wiki 的边界

Yarchi 的项目目录是可变工作区；Karpathy 的 Raw 是不可变证据。两者不能混在同一个
`raw/project/` 中，否则来源层会失去可信边界。

本项目的标准 Skill 采用以下组合：

- 核心 vault 保持 Schema / Raw / Wiki 三个语义层。
- 采用逐题访谈、用户画像、纯文本可移植性和最小权限原则。
- 不把 IPOF 工作区强塞进 Raw 或 Wiki。需要项目执行空间时，应建立独立工作区并由
  其自身规则管理；只有经过选择的外部快照进入 Raw，值得复用的结论进入 Wiki。
- 自动化不属于初始安装的默认行为，必须先验证、再由用户明确启用。
