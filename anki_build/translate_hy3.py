#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量调用 Hy3 翻译所有例句，存成 markdown。

用法：
  python3 translate_hy3.py                 # 全量
  python3 translate_hy3.py --sample        # 只翻前 5 条测试
  python3 translate_hy3.py --resume        # 跳过已翻译的，继续
"""
import sys, os, re, json, subprocess, tempfile, time, argparse
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, "Hy3_参考译文.md")
CACHE = os.path.join(HERE, ".hy3_cache.json")

# 复用 build_anki 的解析器
sys.path.insert(0, HERE)
from build_anki import parse_structures, read, SRC_STRUCT


def collect_sentences():
    """从结构文件里收集所有例句。"""
    structs = parse_structures(read(SRC_STRUCT))
    items = []
    for st in structs:
        for zh, en in st["examples"]:
            items.append({
                "struct_no": st["no"],
                "struct_name": st["name"],
                "zh": zh,
                "orig_en": en,
            })
    return items


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_one(zh):
    """调 Hy3 翻译一句，返回译文。"""
    prompt = (
        "你是大学英语四级（CET-4）翻译辅导老师。请把下面的中文句子翻译成英语，"
        "要求：词汇控制在 CET-4 大纲范围内，优先使用主谓宾/主系表/被动语态/"
        "定语从句等基础句式，避免生僻词和过长的从句嵌套。只输出译文，不要解释。\n\n"
        f"中文：{zh}\n\n英文："
    )
    try:
        r = subprocess.run(
            ["codebuddy", "-p", "--model", "hy3", prompt],
            capture_output=True, text=True, timeout=120, check=False,
        )
        out = r.stdout.strip()
        # 清理可能的 markdown 代码块包裹
        out = re.sub(r"^```(?:\w+)?\n?|```$", "", out, flags=re.M).strip()
        # 取最后一行（Hy3 有时会重复 prompt）
        lines = [ln.strip() for ln in out.split("\n") if ln.strip()]
        return lines[-1] if lines else ""
    except Exception as e:
        return f"[ERROR: {e}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="只翻前 5 条")
    ap.add_argument("--resume", action="store_true", help="跳过已翻译的")
    args = ap.parse_args()

    items = collect_sentences()
    if args.sample:
        items = items[:5]
    print(f"共 {len(items)} 条待翻译")

    cache = load_cache()
    if args.resume:
        items = [it for it in items if it["zh"] not in cache]
        print(f"跳过已翻译，剩 {len(items)} 条")

    md = ["# Hy3 AI 参考译文（CET-4 难度）", "",
          "> 由 Codebuddy Hy3 模型生成，与原译文对照使用", ""]

    done = 0
    for it in items:
        key = it["zh"]
        if key in cache:
            ai_en = cache[key]
        else:
            print(f"[{done+1}/{len(items)}] {key[:40]}...")
            ai_en = translate_one(key)
            cache[key] = ai_en
            if done % 5 == 0:
                save_cache(cache)
            time.sleep(0.5)  # 限速
        it["ai_en"] = ai_en
        done += 1

        md.append(f"## {it['struct_no']}．{it['struct_name']}")
        md.append("")
        md.append(f"**中文**：{it['zh']}")
        md.append("")
        md.append(f"**原译文**：{it['orig_en']}")
        md.append("")
        md.append(f"**Hy3 译文**：{it['ai_en']}")
        md.append("")
        md.append("---")
        md.append("")

    save_cache(cache)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"\n已写出 {OUT_MD}（{done} 条）")


if __name__ == "__main__":
    main()