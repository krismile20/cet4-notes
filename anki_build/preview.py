#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 .apkg 渲染成可视预览 HTML（读真实产物，不是另写一份模板）。

用法： python3 preview.py CET4翻译_抽样.apkg 预览.html
"""
import sys, os, re, json, html, zipfile, sqlite3, tempfile

sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.14/site-packages"))

FIELD_SEP = "\x1f"


def render(apkg, out):
    z = zipfile.ZipFile(apkg)
    d = tempfile.mkdtemp()
    z.extract("collection.anki2", d)
    c = sqlite3.connect(os.path.join(d, "collection.anki2"))
    models = json.loads(c.execute("select models from col").fetchone()[0])
    decks = json.loads(c.execute("select decks from col").fetchone()[0])
    css = next(iter(models.values()))["css"]
    # genanki 的 css 里 .wrap{min-height:100vh} 在浏览器预览里会把每张卡撑满视口
    card_css = css.replace("min-height:100vh", "min-height:0")

    rows = c.execute("select id,mid,flds,tags from notes").fetchall()
    did_of = {}
    for nid, did in c.execute("select nid,did from cards"):
        did_of[nid] = did
    deck_name = {int(k): v["name"] for k, v in decks.items()}

    blocks = []
    for nid, mid, flds, tags in rows:
        m = models[str(mid)]
        fields = flds.split(FIELD_SEP)
        fmap = {f["name"]: v for f, v in zip(m["flds"], fields)}
        for t in m["tmpls"]:
            q, a = t["qfmt"], t["afmt"]

            def fill(s, skip_front=False):
                s = re.sub(r"\{\{FrontSide\}\}", "", s)
                def rep(mm):
                    name = mm.group(1) or mm.group(3)
                    return fmap.get(name, "")
                s = re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", lambda x: x.group(2) if fmap.get(x.group(1)) else "", s, flags=re.S)
                s = re.sub(r"\{\{(\w+)\}\}", rep, s)
                return s

            qh = fill(q)
            ah = fill(a)
            back = ah if ("CET4_翻译" in m["name"]) else qh + '<hr id="answer">' + ah
            title = f'{m["name"]} · {t["name"]}'
            blocks.append(f"""
<section class="pair">
  <div class="tag">{html.escape(title)} <span class="dk">{html.escape(deck_name.get(int(did_of.get(nid,1)),"?"))}</span></div>
  <div class="cols">
    <div><div class="cap">正面</div><div class="card">{qh}</div></div>
    <div><div class="cap">背面</div><div class="card">{back}</div></div>
  </div>
</section>""")

    doc = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Anki 卡片预览</title><style>{card_css}
body{{background:#eef1f6;padding:24px;font-family:system-ui,sans-serif}}
.pair{{margin:0 auto 26px;max-width:1100px}}
.tag{{font:600 12px/1.6 system-ui;color:#2563eb;letter-spacing:.06em;margin-bottom:6px}}
.dk{{color:#5b6b7b;font-weight:400;margin-left:8px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.cap{{font:600 11px/2 system-ui;color:#5b6b7b;letter-spacing:.16em;text-transform:uppercase}}
.card{{border:1px solid #d8dfe9;border-radius:14px;min-height:120px}}
</style></head><body>
<h2 style="max-width:1100px;margin:0 auto 18px;font:700 20px system-ui">共 {len(blocks)} 张卡 · {html.escape(os.path.basename(apkg))}</h2>
{''.join(blocks)}
</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"写出 {out}（{len(blocks)} 张卡）")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "CET4翻译_抽样.apkg",
           sys.argv[2] if len(sys.argv) > 2 else "预览.html")