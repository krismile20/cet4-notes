#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把两份 md 讲义渲染成 HTML（沿用既有版式：暗色模式 / 侧边目录 / 阅读进度条）。

数据源（与本脚本同目录）：
  CET4翻译19大结构精讲.md -> CET4翻译19大结构精讲.html
  CET4翻译主题词汇库.md   -> CET4翻译主题词汇库.html

渲染规则：
  - 词汇库：表格照排；英文格中的「更地道：X」渲染为高亮 chip，原译保留在前
  - 19 结构：**处理方法** 行及其后、空行前的「类型」行渲染进方法块；
    空行后的例句渲染为中英对照卡，英文末尾的（或…）/（…=…）括注提取为 note
  - 可反复执行，覆盖输出

用法： python3 build_html.py
"""
import os
import re
import html as html_mod

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_STRUCT = os.path.join(HERE, "CET4翻译19大结构精讲.md")
SRC_WORD = os.path.join(HERE, "CET4翻译主题词汇库.md")
OUT_STRUCT = os.path.join(HERE, "CET4翻译19大结构精讲.html")
OUT_WORD = os.path.join(HERE, "CET4翻译主题词汇库.html")

# 侧边目录短标签（没有的用 md 全名）
SHORT = {
    1: "“是”字结构", 2: "“的”字结构", 3: "“有”字结构", 4: "“随着”结构",
    5: "“之一”结构", 6: "句中无动词", 7: "句中无主语", 8: "长名词处理",
    9: "两大必考时态", 10: "隐藏被动关系", 11: "双动词处理", 12: "定语从句",
    13: "语序原则", 14: "三动词提后", 15: "删减无效信息", 16: "难词写对",
    17: "数字翻译", 18: "时间朝代", 19: "河流山脉",
}

H1_WORD = "大学英语四级（CET-4）翻译 · 主题词汇库（6 大类）"
H1_STRUCT = "大学英语四级（CET-4）翻译 · 19 大句法结构精讲"

CSS = """
  :root{
    --bg:#f5f7fa; --card:#ffffff; --ink:#1f2933; --muted:#5b6b7b;
    --accent:#2563eb; --accent-bg:#eef4ff; --accent-solid:#2563eb; --en:#0f766e; --line:#e4e9f0;
    --th-bg:#f1f5fb; --chip:#fff4e5; --note-ink:#9a5b00;
  }
  body.dark{
    --bg:#0e1620; --card:#19222e; --ink:#e6edf3; --muted:#93a1b3;
    --accent:#8fa5ff; --accent-bg:#16273d; --accent-solid:#3d6fe3; --en:#5fd6c8; --line:#2a3543;
    --th-bg:#16202d; --chip:#3a2f16; --note-ink:#f0c274;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,Roboto,Helvetica,Arial,sans-serif;
    background:var(--bg);color:var(--ink);line-height:1.75;font-size:16px}
  #progress{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:40}
  .topbar{position:sticky;top:0;z-index:20;background:#0f2747;color:#fff;padding:14px 28px;
    display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;box-shadow:0 2px 10px rgba(0,0,0,.15)}
  body.dark .topbar{background:#0a1019}
  .topbar h1{font-size:18px;font-weight:600;letter-spacing:.5px}
  .topbar .meta{font-size:13px;opacity:.72}
  .theme-btn{background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.25);
    padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px;transition:.15s}
  .theme-btn:hover{background:rgba(255,255,255,.22)}
  .layout{display:flex;align-items:flex-start;max-width:1180px;margin:0 auto;padding:22px}
  nav{position:sticky;top:74px;width:212px;flex:0 0 212px;align-self:flex-start;
    background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 10px;max-height:calc(100vh - 100px);overflow:auto}
  nav h2{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin:6px 8px 10px}
  nav a{display:block;padding:7px 10px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:13.5px;margin-bottom:2px;transition:.15s}
  nav a:hover{background:var(--accent-bg);color:var(--accent)}
  nav a.active{background:var(--accent-bg);color:var(--accent);font-weight:600}
  nav a .num{color:var(--accent);font-weight:700;margin-right:7px}
  main{flex:1;margin-left:22px;min-width:0}
  section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-bottom:20px;scroll-margin-top:80px}
  section h3{font-size:19px;margin-bottom:16px;display:flex;align-items:center;gap:10px}
  section h3 .badge{background:var(--accent-solid);color:#fff;font-size:13px;width:28px;height:28px;border-radius:8px;
    display:inline-flex;align-items:center;justify-content:center;flex:0 0 28px}
  section h3 .count{font-size:12.5px;color:var(--muted);font-weight:400}
  table{width:100%;border-collapse:collapse;font-size:15px}
  thead th{background:var(--th-bg);color:var(--muted);font-size:12.5px;font-weight:700;letter-spacing:1px;
    text-align:left;padding:9px 14px;border-bottom:2px solid var(--line)}
  tbody td{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
  tbody tr:last-child td{border-bottom:none}
  tbody tr:hover{background:var(--accent-bg)}
  td.zh{width:38%;font-weight:500}
  td.en{color:var(--en);line-height:1.6}
  .better{display:inline-block;margin-left:8px;background:var(--chip);color:var(--note-ink);
    font-size:12px;font-weight:600;padding:1px 8px;border-radius:6px;line-height:1.6}
  .tip{margin-top:14px;background:var(--chip);color:var(--note-ink);font-size:13px;padding:8px 12px;border-radius:8px}
  .method{background:var(--accent-bg);border-left:4px solid var(--accent);border-radius:0 10px 10px 0;
    padding:12px 16px;margin-bottom:18px;font-size:14.5px;color:#1e3a5f}
  body.dark .method{color:#bcd4f0}
  .method b{color:var(--accent)}
  .method ul{margin:7px 0 0;list-style:none}
  .method li{font-size:14px;margin-top:5px;padding-left:15px;position:relative}
  .method li:before{content:"▪";position:absolute;left:0;color:var(--accent)}
  .ex{border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin-bottom:9px;background:#fcfdff;transition:.15s}
  body.dark .ex{background:#141c27}
  .ex:hover{border-color:var(--accent)}
  .ex .zh{font-size:15.5px;font-weight:500}
  .ex .en{font-size:15px;color:var(--en);margin-top:5px;padding-left:18px;position:relative;line-height:1.6}
  .ex .en:before{content:"→";position:absolute;left:0;color:#94a3b8;font-weight:700}
  .ex .note{display:block;background:var(--chip);color:var(--note-ink);font-size:12.5px;
    padding:3px 10px;border-radius:6px;margin-top:8px;margin-left:18px;width:max-content;max-width:100%}
  footer{max-width:1180px;margin:0 auto;padding:8px 28px 44px;color:var(--muted);font-size:13px;line-height:1.8}
  @media(max-width:780px){.layout{flex-direction:column}nav{position:static;width:100%;margin-bottom:16px;max-height:none}main{margin-left:0}td.zh{width:42%}}
"""

JS = """
  var btn=document.getElementById('themeBtn');
  var bar=document.getElementById('progress');
  var links=[].slice.call(document.querySelectorAll('nav a'));
  var secs=links.map(function(a){return document.querySelector(a.getAttribute('href'));});
  function apply(dark){
    document.body.classList.toggle('dark',dark);
    btn.textContent=dark?'切换亮色':'切换暗色';
    try{localStorage.setItem('cet4-theme',dark?'dark':'light');}catch(e){}
  }
  try{apply(localStorage.getItem('cet4-theme')!=='light');}catch(e){apply(true);}
  btn.addEventListener('click',function(){apply(!document.body.classList.contains('dark'));});
  function onScroll(){
    var h=document.documentElement;
    var p=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;
    bar.style.width=(p>100?100:p)+'%';
    var pos=window.scrollY+100,cur=secs[0];
    for(var i=0;i<secs.length;i++){if(secs[i]&&secs[i].offsetTop<=pos)cur=secs[i];}
    links.forEach(function(a){a.classList.toggle('active',cur&&a.getAttribute('href')==='#'+cur.id);});
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);
  onScroll();
"""


# ---------------------------------------------------------------- 基础

def esc(s):
    return html_mod.escape(s, quote=False)


def md_inline(s):
    """转义后把 **加粗** 还原为 <b>。"""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def find_date(md):
    m = re.search(r"整理时间：(\d{4}-\d{2}-\d{2})", md)
    return m.group(1) if m else ""


def find_h1(md):
    m = re.search(r"^# (.+)$", md, re.M)
    return m.group(1).strip() if m else ""


def split_better(en):
    """'原译；更地道：X' -> ('原译', 'X')"""
    if "更地道：" in en:
        head, _, tail = en.partition("更地道：")
        return head.rstrip("；;，, "), tail
    return en, None


def split_note(en):
    """英文末尾的（或…）/（…=…）括注提取为 note。"""
    m = re.match(r"^(.*?)\s*（([^（）]*)）\s*$", en)
    if m and m.group(2):
        return m.group(1).strip(), m.group(2).strip()
    return en, ""


# ---------------------------------------------------------------- 解析

def parse_vocab(md):
    """-> [{num, name, rows:[(zh, en)], tip}]"""
    cats = []
    for ch in re.split(r"\n## ", "\n" + md)[1:]:
        head = ch.split("\n", 1)[0].strip()
        m = re.match(r"([一二三四五六七八九十]+)、(.*)", head)
        if not m:
            continue
        rows, tip = [], ""
        for line in ch.split("\n")[1:]:
            line = line.strip()
            if line.startswith("|"):
                if re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 2 or cells[0] == "中文":
                    continue
                rows.append((cells[0], cells[1]))
            elif line.startswith(">"):
                tip = line.lstrip(">").strip()
        cats.append(dict(num=m.group(1), name=m.group(2).strip(), rows=rows, tip=tip))
    return cats


def parse_struct(md):
    """-> [{no, name, intro, method_lines, examples:[(zh, en)]}]"""
    sections = []
    for ch in re.split(r"\n## ", "\n" + md)[1:]:
        head = ch.split("\n", 1)[0]
        m = re.match(r"(\d+)．(.+)", head)
        if not m:
            continue
        no, name = int(m.group(1)), m.group(2).strip()
        lines = ch.split("\n", 1)[1].split("\n")

        intro, mi = "", None
        for i, ln in enumerate(lines):
            mm = re.match(r"\*\*处理方法\*\*[：:](.*)", ln)
            if mm:
                intro, mi = mm.group(1).strip(), i
                break

        method_lines, examples = [], []
        if mi is not None:
            # 空行前的 "- " 行是类型/规则行，进方法块
            j = mi + 1
            while j < len(lines) and lines[j].strip():
                ln = lines[j].strip()
                if ln.startswith("- "):
                    method_lines.append(ln[2:].strip())
                j += 1
            scan = lines[j:]
        else:
            scan = lines

        i = 0
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
        sections.append(dict(no=no, name=name, intro=intro,
                             method_lines=method_lines, examples=examples))
    return sections


# ---------------------------------------------------------------- 渲染

def shell(title, h1, meta, nav_html, main_html, footer):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div id="progress"></div>
<div class="topbar">
  <h1>{esc(h1)}</h1>
  <span class="meta">{esc(meta)}</span>
  <button id="themeBtn" class="theme-btn">切换亮色</button>
</div>

<div class="layout">
  <nav>
    <h2>目录</h2>
{nav_html}
  </nav>

  <main>
{main_html}
  </main>
</div>

<footer>
  {footer}
</footer>
<script>{JS}</script>
</body>
</html>
"""


def render_vocab(cats, date):
    nav, main, total = [], [], 0
    for i, c in enumerate(cats, 1):
        nav.append(f'    <a href="#c{i}"><span class="num">{i}</span>{esc(c["name"])}</a>')
        rows = []
        for zh, en in c["rows"]:
            base, better = split_better(en)
            chip = f'<span class="better">更地道：{esc(better)}</span>' if better else ""
            rows.append(f'          <tr><td class="zh">{esc(zh)}</td>'
                        f'<td class="en">{md_inline(base)}{chip}</td></tr>')
        tip = f'      <div class="tip">{esc(c["tip"])}</div>' if c["tip"] else ""
        total += len(c["rows"])
        main.append(f"""    <section id="c{i}">
      <h3><span class="badge">{i}</span>{esc(c["name"])} <span class="count">{len(c["rows"])} 词</span></h3>
      <table>
        <thead><tr><th>中文</th><th>英文表达</th></tr></thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
{tip}
    </section>""")

    meta = " · ".join(c["name"].rstrip("类") for c in cats) + f" · {date}"
    footer = (f"共 {len(cats)} 大类 {total} 词。建议用法：遮住英文列，看中文默译，再对照检查；"
              f"「更地道」chip 为更优表达，与原译对照记忆。"
              f"可配合《CET4翻译词汇句型宝典.md》《CET4翻译19大结构精讲.html》一起使用。")
    return shell(H1_WORD, H1_WORD, meta,
                 "\n".join(nav), "\n".join(main), footer), total


def render_struct(sections, date, md):
    nav, main, n_ex = [], [], 0
    for s in sections:
        no = s["no"]
        nav.append(f'    <a href="#s{no}"><span class="num">{no}</span>{esc(SHORT.get(no, s["name"]))}</a>')
        lis = "".join(f"<li>{md_inline(l)}</li>" for l in s["method_lines"])
        method = (f'      <div class="method"><b>处理：</b>{md_inline(s["intro"])}'
                  + (f"<ul>{lis}</ul>" if lis else "") + "</div>")
        exs = []
        for zh, en in s["examples"]:
            en2, note = split_note(en)
            n = f'<span class="note">{esc(note)}</span>' if note else ""
            exs.append(f'      <div class="ex"><div class="zh">{esc(zh)}</div>'
                       f'<div class="en">{md_inline(en2)}</div>{n}</div>')
            n_ex += 1
        main.append(f"""    <section id="s{no}">
      <h3><span class="badge">{no}</span>{esc(s["name"])}</h3>
{method}
{chr(10).join(exs)}
    </section>""")

    foot_m = re.search(r"^>\s*整理时间：\d{4}-\d{2}-\d{2}｜(.+)$", md, re.M)
    footer = foot_m.group(1).strip() if foot_m else ""
    meta = f"每个结构 = 处理方法 + 例句中英对照 · {date}"
    return shell(H1_STRUCT, H1_STRUCT, meta,
                 "\n".join(nav), "\n".join(main), footer), n_ex


# ---------------------------------------------------------------- 主流程

def main():
    md_s, md_w = read(SRC_STRUCT), read(SRC_WORD)
    secs = parse_struct(md_s)
    cats = parse_vocab(md_w)

    doc_s, n_ex = render_struct(secs, find_date(md_s), md_s)
    doc_w, n_word = render_vocab(cats, find_date(md_w))

    for path, doc in ((OUT_STRUCT, doc_s), (OUT_WORD, doc_w)):
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"写出 {path}（{os.path.getsize(path) // 1024} KB）")

    print(f"19 大结构：{len(secs)} 节 / {n_ex} 条例句")
    print(f"主题词汇：{len(cats)} 大类 / {n_word} 词"
          f"（其中 {sum(1 for c in cats for _, e in c['rows'] if '更地道：' in e)} 条带「更地道」）")


if __name__ == "__main__":
    main()
