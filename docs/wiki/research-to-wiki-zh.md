[English](research-to-wiki.md) · [한국어](research-to-wiki-ko.md) · [日本語](research-to-wiki-ja.md) · **中文** · [Español](research-to-wiki-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# research-to-wiki

把一个调研请求变成一个 wiki 页面，显示每个论断被证实到了什么程度。

## 在 Claude 中使用

说“调研一下 X 是否会导致 Y”或“查一下支持 X 的证据”。对于调研请求，`skill-match` 会指出这个技能。

## 它做什么

1. 先搜索 wiki；更新已有页面，而不是新建一页。
2. 检索文献，覆盖问题的正反两方面以及混杂因素。
3. 每条来源的末尾都加上两个标签：它属于哪种研究（`메타분석` 荟萃分析、`무작위시험` 随机试验、`추적관찰` 队列研究、`유전분석` 孟德尔随机化、`단면비교` 横断面研究、`동물실험` 动物实验、`세포실험` 细胞实验、`리뷰` 综述、`의견` 观点），以及读了多少（`본문` 全文、`초록` 摘要、`검색요약` 搜索结果摘要）。检查程序读取数据文件里的这些韩文名称，所以要原样写上。
4. 撰写页面时把结论放在最前面，用你自己的话写，数字旁边写上它所比较的对象。
5. 检查页面，然后在 wiki 的索引和日志中登记。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `check_research.py <page>` | 标出缺失的结论、没有链接或标签的来源，以及没有来源的引用 |

标签名称是数据文件（`data/evidence-levels.tsv`、`data/reading-levels.txt`）；页面模板是 `assets/research-page-template.md`。

## 局限

检查只看标签有没有，不看标签对不对。这仍然需要去读论文。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
