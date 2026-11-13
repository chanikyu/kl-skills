[English](readable-code.md) · [한국어](readable-code-ko.md) · [日本語](readable-code-ja.md) · **中文** · [Español](readable-code-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# readable-code

让下一位读者能看懂的代码：名字说明它装的是什么，注释说明为什么。

## 在 Claude 中使用

什么都不用说：每当编写或修改代码时都会生效。

## 它做什么

1. 名字说明这个值是什么——用 `student_name`，而不是 `n`。
2. 注释解释代码为什么是这个样子，而不是每一行在做什么。
3. 值应该放在数据文件里，而不是代码里（见 [no-hardcoding](no-hardcoding-zh.md)）。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `check_code.py <files>` | 标出含糊的命名、缺失的 docstring，以及没有注释的长函数 |

允许使用的短名字和被视为含糊的名字都是 `data/` 中的数据文件。

## 背后的钩子检查

每写入一个 Python 文件，`code-check` 都会运行。它只报告，从不阻止。

## 局限

这项检查只读 Python。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
