#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量合并构建：一次生成 CET4翻译_全量.apkg（9 个子牌组）。

= build_anki.py（01 十九结构 + 02 主题词汇 + 03 例句精练，含 Hy3 参考译文）
+ build_anki_extra.py（04 汉英翻译语料）

牌组 ID 与两个分包保持一致（04 沿用 1751002001，其余按排序顺延），
已导入分包的 Anki 重导时 01/03/04 可原地更新，不产生重复牌组。
词汇卡 GUID 方案在 2026-10-24 有变更（不再含英文），
若导入过旧版词汇卡，需先删除「CET4 翻译::02 主题词汇」各子牌组。

用法：python3 build_all.py
"""
import os
import sys

# genanki 装在 user site-packages，脚本可能以 -I 启动
sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.14/site-packages"))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genanki  # noqa: E402
import build_anki as A  # noqa: E402
import build_anki_extra as B  # noqa: E402

OUT = os.path.join(HERE, "CET4翻译_全量.apkg")


def main():
    structs = A.parse_structures(A.read(A.SRC_STRUCT))
    words = A.parse_words(A.read(A.SRC_WORD))
    hy3 = A.load_hy3()
    n_sent = sum(len(s["examples"]) for s in structs)
    n_hy3 = sum(1 for st in structs for z, _ in st["examples"] if z in hy3)
    print(f"解析：结构 {len(structs)} 个，例句 {n_sent} 条，词汇 {len(words)} 条；"
          f"Hy3 覆盖 {n_hy3}/{n_sent}")

    notes = A.build_notes(structs, words, hy3) + B.build_notes()

    decks = {}
    for name, note in notes:
        decks.setdefault(name, []).append(note)

    # 04 语料牌组沿用 build_anki_extra 的 ID；其余按排序顺延（与 build_anki 一致）
    fixed_ids = {B.DECK_NAME: B.DECK_ID}
    pkg = []
    for i, name in enumerate(sorted(decks), 1):
        d = genanki.Deck(fixed_ids.get(name, 1751001000 + i), name)
        for n in decks[name]:
            d.add_note(n)
        pkg.append(d)
    genanki.Package(pkg).write_to_file(OUT)

    total = len(notes)
    print(f"牌组 {len(pkg)} 个，笔记 {total} 条，卡片约 {total * 2} 张")
    for name in sorted(decks):
        print(f"   {name:44s} {len(decks[name]):4d} 条")
    print("已写出", OUT)


if __name__ == "__main__":
    main()
