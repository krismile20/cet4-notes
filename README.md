# 讲义库

四级写作/翻译速通笔记、翻译深挖讲义与 Anki 卡片，另含学习方法、精力管理与考研英语精读。

**在线阅读（GitHub Pages）**：<https://krismile20.github.io/cet4-notes/>

## 页面

- [首页](index.html)

四级速通：

- 作文：[桌面版](writing.html) · [手机版](writing-mobile.html)
- 翻译速通：[桌面版](translation.html) · [手机版](translation-mobile.html)
- 翻译深挖：
  - [19 大句法结构精讲](CET4翻译19大结构精讲.html) · [md](CET4翻译19大结构精讲.md)
  - [主题词汇库](CET4翻译主题词汇库.html) · [md](CET4翻译主题词汇库.md)
  - [词汇句型宝典](CET4翻译词汇句型宝典.md)（md）
- Anki 卡片：[anki_build/](anki_build/) —— `CET4翻译_全量.apkg`（454 条笔记 / 908 张卡）

方法与状态：

- [这可能是全网最好的学习方法](learning-method.html)
- [可持续休息 & 奖励系统](rest-and-reward.html)

考研英语精读：

- [2025 英一 Text 2 · 一石五鸟复盘模式](kaoyan2025-text2-review.html)
- [2025 英一 Text 2 · 做题模式](kaoyan2025-text2-practice.html)
## 本地重新生成

```bash
python3 build_html.py               # md → html（深挖笔记两份）
python3 anki_build/build_all.py     # 全部 Anki 包
```

依赖 Python 3 与 genanki（`pip install genanki`）。

内容根据公开视频与备考资料整理，仅供个人备考参考。
