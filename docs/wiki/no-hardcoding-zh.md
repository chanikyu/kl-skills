[English](no-hardcoding.md) · [한국어](no-hardcoding-ko.md) · [日本語](no-hardcoding-ja.md) · **中文** · [Español](no-hardcoding-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# no-hardcoding

不让值、列表、映射、路径和阈值写死在代码里。

## 在 Claude 中使用

什么都不用说：每当代码要带上一个值时都会生效。

## 它做什么

1. 已经存在于某个文件里的值，从那个文件读取，绝不复制到代码里。
2. 映射表、别名列表和目标列表放进数据文件（`.tsv`、`.json`）。
3. 路径根据脚本所在的位置计算、作为参数传入，或从环境变量读取。
4. 阈值、随机种子和数量都作为命令行参数。
5. 只有永远不变的常量才留在代码里，并且要有名字和出处。

## 局限

这是给模型遵守的规则；没有脚本直接检查它。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
