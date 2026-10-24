#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CET-4 翻译 Anki 卡片构建脚本。

数据源：
  ../CET4翻译19大结构精讲.md   -> 19 个结构知识点 + 61 条例句
  ../CET4翻译主题词汇库.md     -> 6 大类 / 205 条词汇

产物：
  CET4翻译.apkg                可导入 Anki 的牌组包
  校验报告.md                   抽取清单与条数比对

用法：
  python3 build_anki.py            # 生成全部
  python3 build_anki.py --sample   # 只生成抽样预览包 CET4翻译_抽样.apkg
"""
import sys, os, re, html, argparse, unicodedata

# genanki 装在 user site-packages，脚本可能以 -I 启动
sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.14/site-packages"))
import genanki  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_STRUCT = os.path.join(HERE, os.pardir, "CET4翻译19大结构精讲.md")
SRC_WORD = os.path.join(HERE, os.pardir, "CET4翻译主题词汇库.md")

DECK_ROOT = "CET4 翻译"
TAG_ROOT = "CET4::翻译"

# ---------------------------------------------------------------- 解析

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def parse_structures(md):
    """-> [{no, name, method(list[str]), examples:[(zh,en)]}]

    每个结构 以 '## N．标题' 开头。
    '**处理方法**：' 行给方法导语；其后到第一个空行为止的 '- ' 行是
    类型/规则行，归入处理方法；空行之后的 '- ' 行是例句，两种排布：
      甲（多行）  '- 中文\\n  → 英文'
      乙（单行）  '- 中文 → 英文'

    注意：不能用行首关键词区分规则行与例句——'山东/海南/公元前 3000 年'
    等例句会撞上 山/海/公元前 等规则前缀（2026-10-24 修：旧版因此丢 3 条
    例句，又把 S16 的 归属感/飞跃/总部/通道/羊圈 误抽成例句）。
    """
    chunks = re.split(r"\n## ", "\n" + md)
    out = []
    for ch in chunks:
        m = re.match(r"(\d+)．(.+)", ch.split("\n", 1)[0])
        if not m:
            continue
        no, name = int(m.group(1)), m.group(2).strip()
        rest = ch.split("\n", 1)[1]
        rest = rest.split("\n> ")[0]              # 去掉尾注
        lines = rest.split("\n")

        method, scan = [], lines
        mi = next((i for i, ln in enumerate(lines)
                   if re.match(r"\*\*处理方法\*\*[：:]", ln)), None)
        if mi is not None:
            intro = re.match(r"\*\*处理方法\*\*[：:](.*)", lines[mi]).group(1).strip()
            if intro:
                method.append(intro)
            j = mi + 1
            while j < len(lines) and lines[j].strip():
                if lines[j].startswith("- "):
                    method.append(lines[j].strip())
                j += 1
            scan = lines[j:]

        examples, i = [], 0
        while i < len(scan):
            ln = scan[i]
            if ln.startswith("- "):
                zh = ln[2:].strip()
                nxt = scan[i + 1].lstrip() if i + 1 < len(scan) else ""
                if nxt.startswith("→"):
                    examples.append((zh, nxt[1:].strip()))
                    i += 2
                    continue
                if "→" in zh:
                    zh, _, en = zh.partition("→")
                    examples.append((zh.strip(), en.strip()))
            i += 1
        out.append(dict(no=no, name=name, method=method, examples=examples))
    return out


def parse_words(md):
    """-> [{cat, zh, en}]  表格行；cat 规范为 '一 历史文化类' 这样的带序号名"""
    sections = re.split(r"\n## ", "\n" + md)
    out = []
    for sec in sections:
        head = sec.split("\n", 1)[0].strip()
        m = re.match(r"([一二三四五六七八九十]+)、(.*)", head)
        if not m:
            continue
        cat = f"{m.group(1)} {m.group(2).strip()}"
        for line in sec.split("\n")[1:]:
            line = line.strip()
            if not line.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or cells[0] in ("中文",):
                continue
            out.append(dict(cat=cat, zh=cells[0], en=cells[1]))
    return out


# ---------------------------------------------------------------- 富文本

BOLD = re.compile(r"\*\*(.+?)\*\*")


def md_inline(s):
    """行内 Markdown -> HTML（先转义，再还原加粗）。"""
    s = html.escape(s, quote=False)
    s = BOLD.sub(r"<b>\1</b>", s)
    return s.strip()


def method_html(lines):
    """处理方法：'类型一（...）：xx' 缩进项；并列项各自成行。"""
    out = []
    for ln in lines:
        t = md_inline(ln)
        if re.match(r"^[-—•]", ln):
            t = re.sub(r"^[-—•]\s*", "", t)
            out.append(f'<div class="sub">{t}</div>')
        else:
            out.append(f'<p class="line">{t}</p>')
    return "\n".join(out)


def clean_zh(s):
    """去掉行内括注的英文提示，如 爆竹（firecrackers）是中国…"""
    return re.sub(r"（[A-Za-z][^）]*）", "", s).strip()


def split_note(en):
    """'原译；更地道：X' -> ('原译', '更地道：X')，更地道译法进词汇卡备注列。"""
    if "更地道：" in en:
        head, _, tail = en.partition("更地道：")
        return head.rstrip("；;，, "), "更地道：" + tail
    return en, ""


def load_hy3():
    """-> {中文原句: Hy3 译文}；以 Hy3_参考译文.md 为主，.hy3_cache.json 补齐缺失条目。"""
    import json
    hy3 = {}
    src_md = os.path.join(HERE, "Hy3_参考译文.md")
    if os.path.exists(src_md):
        hy3 = {
            zh: en
            for zh, en in re.findall(
                r"\*\*中文\*\*：(.+?)\n\n\*\*原译文\*\*：.+?\n\n\*\*Hy3 译文\*\*：(.+?)\n",
                read(src_md),
            )
        }
    src_cache = os.path.join(HERE, ".hy3_cache.json")
    if os.path.exists(src_cache):
        with open(src_cache, encoding="utf-8") as f:
            for k, v in json.load(f).items():
                hy3.setdefault(k, v)
    return hy3


# ---------------------------------------------------------------- 样式

CSS = """
.card{
  font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;
  font-size:20px; line-height:1.7; color:#1f2933; background:#f5f7fa;
  text-align:left; padding:0;
}
.wrap{max-width:680px;margin:0 auto;background:#fff;
      border-radius:14px;padding:28px 30px;min-height:100vh;
      box-sizing:border-box}
/* 顶部小标签：结构序号 / 主题 */
.tagbar{display:flex;align-items:center;gap:8px;margin-bottom:18px}
.tagbar .no{font-size:13px;color:#5b6b7b;letter-spacing:.05em}
.tagbar .cat{font-size:12px;color:#9a5b00;background:#fff4e5;border-radius:999px;padding:3px 12px}
/* 主标题 */
.struct-name{font-size:28px;font-weight:700;color:#1f2933;line-height:1.3;margin-bottom:4px}
.zh{font-size:30px;font-weight:700;color:#1f2933;line-height:1.4}
.en{font-size:26px;font-weight:600;color:#0f766e;line-height:1.5;word-break:break-word}
.sent-zh{font-size:24px;font-weight:600;color:#1f2933;line-height:1.7}
.sent-en{font-size:24px;font-weight:600;color:#0f766e;line-height:1.7}
/* 分隔线 */
hr#answer{border:0;border-top:1px solid #e4e9f0;margin:22px 0}
/* 处理方法块 */
.lbl{font-size:13px;font-weight:700;color:#2563eb;letter-spacing:.08em;
     margin:0 0 10px;text-transform:uppercase}
.method p.line{margin:0 0 10px}
.method p.line:last-child{margin-bottom:0}
.method .sub{margin:0 0 10px;padding:6px 0 6px 16px;border-left:3px solid #dbe4f0}
.method .sub:last-child{margin-bottom:0}
.method b{color:#1d4ed8}
/* 例句清单：中文左、英文右，竖线分隔 */
.ex-list{margin-top:4px;border:1px solid #e4e9f0;border-radius:10px;overflow:hidden}
.ex-item{display:grid;grid-template-columns:1fr 1fr;gap:0;align-items:stretch}
.ex-item:not(:last-child) .ex-z,
.ex-item:not(:last-child) .ex-e{border-bottom:1px solid #e4e9f0}
.ex-z,.ex-e{padding:12px 14px;line-height:1.65}
.ex-z{font-size:18px;color:#475569;border-right:1px solid #e4e9f0;background:#f8fafc}
.ex-e{font-size:18px;color:#0f766e;font-weight:600}
/* 底部归属标签 */
.footnote{font-size:14px;color:#94a3b8;margin-top:18px;padding-top:12px;border-top:1px solid #f0f3f7}
/* 夜间模式 */
.night_mode .card,.nightMode .card{background:#0e1620;color:#e6edf3}
.night_mode .wrap,.nightMode .wrap{background:#19222e}
.night_mode .struct-name,.nightMode .struct-name,
.night_mode .zh,.nightMode .zh,
.night_mode .sent-zh,.nightMode .sent-zh{color:#e6edf3}
.night_mode .en,.nightMode .en,
.night_mode .sent-en,.nightMode .sent-en,
.night_mode .ex-item .ex-e,.nightMode .ex-item .ex-e{color:#5fd6c8}
.night_mode .tagbar .no,.nightMode .tagbar .no,
.night_mode .ex-item .ex-z,.nightMode .ex-item .ex-z{color:#93a1b3}
.night_mode .lbl,.nightMode .lbl{color:#8fa5ff}
.night_mode .method .sub,.nightMode .method .sub{border-left-color:#2a3543}
.night_mode .ex-item .ex-z,.nightMode .ex-item .ex-z{background:#1a2432}
.night_mode .ex-item .ex-z,.nightMode .ex-item .ex-z{border-right-color:#2a3543}
.night_mode .ex-item:not(:last-child) .ex-z,.nightMode .ex-item:not(:last-child) .ex-z,
.night_mode .ex-item:not(:last-child) .ex-e,.nightMode .ex-item:not(:last-child) .ex-e{border-bottom-color:#2a3543}
.night_mode .ex-list,.nightMode .ex-list{border-color:#2a3543}
.night_mode hr#answer,.nightMode hr#answer{border-top-color:#2a3543}
.night_mode .footnote,.nightMode .footnote{border-top-color:#2a3543;color:#5b6b7b}
"""

# ---------------------------------------------------------------- 笔记类型

MODEL_STRUCT = genanki.Model(
    1751001001,
    "CET4_翻译·结构",
    fields=[{"name": n} for n in ("结构序号", "结构名", "处理方法", "例句清单", "主题")],
    templates=[
        {
            "name": "中文结构 → 处理方法",
            "qfmt": """<div class="wrap">
  <div class="tagbar"><span class="no">{{结构序号}}</span></div>
  <div class="struct-name">{{结构名}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="tagbar"><span class="no">{{结构序号}}</span></div>
  <div class="struct-name">{{结构名}}</div>
  <hr id="answer">
  <div class="lbl">处理方法</div>
  <div class="method">{{处理方法}}</div>
  {{#例句清单}}<div class="lbl" style="margin-top:20px">例句</div>
  <div class="ex-list">{{例句清单}}</div>{{/例句清单}}
</div>""",
        },
        {
            "name": "处理方法 → 中文结构",
            "qfmt": """<div class="wrap">
  <div class="lbl">处理方法</div>
  <div class="method">{{处理方法}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="lbl">处理方法</div>
  <div class="method">{{处理方法}}</div>
  <hr id="answer">
  <div class="tagbar"><span class="no">{{结构序号}}</span></div>
  <div class="struct-name">{{结构名}}</div>
</div>""",
        },
    ],
    css=CSS,
)

MODEL_WORD = genanki.Model(
    1751001002,
    "CET4_翻译·词汇",
    fields=[{"name": n} for n in ("中文", "英文", "主题", "备注")],
    templates=[
        {
            "name": "中 → 英",
            "qfmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{主题}}</span></div>
  <div class="zh">{{中文}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{主题}}</span></div>
  <div class="zh">{{中文}}</div>
  <hr id="answer">
  <div class="en">{{英文}}</div>
  {{#备注}}<div class="footnote">{{备注}}</div>{{/备注}}
</div>""",
        },
        {
            "name": "英 → 中",
            "qfmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{主题}}</span></div>
  <div class="en">{{英文}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{主题}}</span></div>
  <div class="en">{{英文}}</div>
  <hr id="answer">
  <div class="zh">{{中文}}</div>
</div>""",
        },
    ],
    css=CSS,
)

MODEL_SENT = genanki.Model(
    1751001003,
    "CET4_翻译·例句",
    fields=[{"name": n} for n in ("中文句", "英文句", "所属结构", "Hy3译文")],
    templates=[
        {
            "name": "中 → 英",
            "qfmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{所属结构}}</span></div>
  <div class="sent-zh">{{中文句}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{所属结构}}</span></div>
  <div class="sent-zh">{{中文句}}</div>
  <hr id="answer">
  <div class="lbl">原译文</div>
  <div class="sent-en">{{英文句}}</div>
  {{#Hy3译文}}<div class="lbl" style="margin-top:16px">Hy3 参考译文</div>
  <div class="sent-en" style="color:#5b6b7b">{{Hy3译文}}</div>{{/Hy3译文}}
</div>""",
        },
        {
            "name": "英 → 中",
            "qfmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{所属结构}}</span></div>
  <div class="sent-en">{{英文句}}</div>
</div>""",
            "afmt": """<div class="wrap">
  <div class="tagbar"><span class="cat">{{所属结构}}</span></div>
  <div class="sent-en">{{英文句}}</div>
  <hr id="answer">
  <div class="sent-zh">{{中文句}}</div>
</div>""",
        },
    ],
    css=CSS,
)


def guid(tag, *parts):
    import hashlib
    h = hashlib.sha1(("|".join([tag] + list(parts))).encode("utf-8")).hexdigest()[:16]
    return genanki.guid_for("cet4tr", tag, h)


# ---------------------------------------------------------------- 构图

def build_notes(structs, words, hy3):
    notes = []
    # 结构卡 + 例句卡
    for st in structs:
        deck_st = DECK_ROOT + "::01 十九结构"
        notes.append((deck_st, genanki.Note(
            model=MODEL_STRUCT,
            fields=[
                f"结构 {st['no']} / 19",
                st["name"],
                method_html(st["method"]),
                "\n".join(
                    f'<div class="ex-item"><div class="ex-z">{md_inline(z)}</div><div class="ex-e">{md_inline(e)}</div></div>'
                    for z, e in st["examples"]
                ),
                f"第 {st['no']} 结构",
            ],
            tags=[TAG_ROOT, TAG_ROOT + "::结构", "来源::19大结构精讲", f"结构{st['no']:02d}"],
            guid=guid("struct", str(st["no"])),
        )))
        for i, (z, e) in enumerate(st["examples"], 1):
            notes.append((DECK_ROOT + "::03 例句精练", genanki.Note(
                model=MODEL_SENT,
                fields=[clean_zh(z), md_inline(e), f"{st['no']}．{st['name']}", md_inline(hy3.get(z, ""))],
                tags=[TAG_ROOT, TAG_ROOT + "::例句", "来源::19大结构精讲", f"结构{st['no']:02d}"],
                guid=guid("sent", str(st["no"]), str(i), z),
            )))
    # 词汇卡
    seen = set()
    for w in words:
        deck_w = DECK_ROOT + "::02 主题词汇::" + w["cat"]
        g = guid("word", w["cat"], w["zh"])  # 不含 en：改译法后 GUID 不变，重导可原地更新
        if g in seen:
            print("  ! 重复词条已跳过:", w["zh"], file=sys.stderr)
            continue
        seen.add(g)
        en, note = split_note(w["en"])
        notes.append((deck_w, genanki.Note(
            model=MODEL_WORD,
            fields=[md_inline(w["zh"]), md_inline(en), w["cat"], md_inline(note)],
            tags=[TAG_ROOT, TAG_ROOT + "::词汇", "来源::主题词汇库",
                  TAG_ROOT + "::词汇::" + w["cat"].replace(" ", "_")],
            guid=g,
        )))
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="只输出抽样预览包")
    args = ap.parse_args()

    structs = parse_structures(read(SRC_STRUCT))
    words = parse_words(read(SRC_WORD))

    print(f"解析：结构 {len(structs)} 个，例句 {sum(len(s['examples']) for s in structs)} 条，"
          f"词汇 {len(words)} 条")
    if args.sample:
        structs = [s for s in structs if s["no"] in (2, 4, 12, 17)]
        keep = {"一 历史文化类", "五 科技教育"}
        words = [w for w in words if w["cat"] in keep][:6]

    hy3 = load_hy3()
    n_hy3 = sum(1 for st in structs for z, _ in st["examples"] if z in hy3)
    n_sent = sum(len(s["examples"]) for s in structs)
    print(f"Hy3 参考译文覆盖 {n_hy3}/{n_sent} 条")
    notes = build_notes(structs, words, hy3)
    decks = {}
    for deck_name, note in notes:
        decks.setdefault(deck_name, []).append(note)

    out = "CET4翻译_抽样.apkg" if args.sample else "CET4翻译.apkg"
    outpath = os.path.join(HERE, out)
    pkg = []
    for i, deck_name in enumerate(sorted(decks), 1):
        d = genanki.Deck(1751001000 + i, deck_name)
        for n in decks[deck_name]:
            d.add_note(n)
        pkg.append(d)
    genanki.Package(pkg).write_to_file(outpath)

    print(f"牌组 {len(pkg)} 个，笔记 {len(notes)} 条，卡片约 {len(notes) * 2} 张")
    for deck_name in sorted(decks):
        print(f"   {deck_name:44s} {len(decks[deck_name]):4d} 条")
    print("已写出", outpath)


if __name__ == "__main__":
    main()