# workspaces.md — 工作区登记表

> 环境配置层（机器相关）。登记 vault **外**的项目工作区，让 brain 知晓其存在、路径与权限。
> 绝对路径不进 CLAUDE.md（保持宪法可迁移）。换机器只改本文件。
> 规范见 `CLAUDE.md` §16。**所有项目（个人、公司）都在此登记；vault 内不建 projects/ 目录。**
> 工作区放 vault 外，是为了在其中启动 claude 时天然不加载 vault 的 Schema，得到干净的项目模式。

## 字段说明

每个工作区一个 `##` 小节：

- **path**：vault 外绝对路径
- **type**：`personal` | `company` | `other`
- **purpose**：一句话——这是什么、brain 该怎么用它
- **wiki**：`[[对应的 wiki 索引卡]]`——brain 在 wiki 里的入口页面
- **access**：`read-only` | `read-write`——brain 对该目录的权限意图

每个工作区内部建议套 IPOF（inputs/process/outputs/feedback）+ 项目级 CLAUDE.md。

---

<!-- 登记示例（删除本注释，按下面格式填真实条目）

## 某公司项目
- path: /Users/return/work/some-company-project
- type: company
- purpose: XX 系统需求与设计，brain 读取产出摘要、保持 wiki 索引卡最新
- wiki: [[某公司项目]]
- access: read-only

## 某个人项目
- path: /Users/return/dev/some-personal-project
- type: personal
- purpose: 个人 side project，brain 在此协助开发与产出
- wiki: [[某个人项目]]
- access: read-write

-->
