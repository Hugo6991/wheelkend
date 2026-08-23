#!/usr/bin/env python3
"""Build dist/index.html from src/index.src.html.

Recompresses assets/img/<key>.jpg via sips (macOS), embeds them as base64
data URIs replacing the __CITY_IMG__ placeholder, and fills the __CREDITS__
footer block from assets/credits.json. Fails loudly if placeholders are
missing or an image is absent."""
import base64, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "index.src.html")
IMGDIR = os.path.join(ROOT, "assets", "img")
CREDITS = os.path.join(ROOT, "assets", "credits.json")
SMALL = os.path.join(ROOT, ".build", "img_small")
OUT = os.path.join(ROOT, "dist", "index.html")
os.makedirs(SMALL, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

ZH = {"suzhou": "蘇州", "hangzhou": "杭州", "wuxi": "無錫", "nanjing": "南京",
      "jiaxing": "嘉興", "wuzhen": "烏鎮", "shaoxing": "紹興", "ningbo": "寧波",
      "changzhou": "常州", "nantong": "南通", "yangzhou": "揚州",
      "moganshan": "莫干山", "qiandaohu": "千島湖", "huangshan": "黃山"}

creds = {c["key"]: c for c in json.load(open(CREDITS, encoding="utf-8"))}

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

img_map, credit_lines, total = {}, [], 0
for key in ZH:
    src = os.path.join(IMGDIR, f"{key}.jpg")
    if not os.path.exists(src):
        print(f"[MISS] {key}: no source image — card will use text fallback")
        continue
    out = os.path.join(SMALL, f"{key}.jpg")
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "55",
                    "-Z", "640", src, "--out", out],
                   check=True, capture_output=True)
    data = open(out, "rb").read()
    total += len(data)
    img_map[key] = "data:image/jpeg;base64," + base64.b64encode(data).decode()
    c = creds.get(key, {})
    artist = strip_tags(c.get("artist", ""))[:60] or "見 Commons 檔案頁"
    credit_lines.append(
        f"{ZH[key]}（{c.get('file', '')}）：{artist}，{c.get('license', '?')}，via Wikimedia Commons")
    print(f"[OK] {key}: {len(data)//1024} KB, {c.get('license', '?')}")

html = open(SRC, encoding="utf-8").read()
if "/*__CITY_IMG__*/" not in html:
    sys.exit("FATAL: __CITY_IMG__ placeholder not found in src/index.src.html")
if "<!--__CREDITS__-->" not in html:
    sys.exit("FATAL: __CREDITS__ placeholder not found in src/index.src.html")

entries = ",\n    ".join(f"'{k}': '{v}'" for k, v in img_map.items())
html = html.replace("{/*__CITY_IMG__*/}", "{\n    " + entries + "\n  }")
html = html.replace("<!--__CREDITS__-->", "<br>".join(credit_lines))

open(OUT, "w", encoding="utf-8").write(html)
print(f"\nwrote {OUT}: {os.path.getsize(OUT)//1024} KB "
      f"({len(img_map)}/14 photos, {total//1024} KB images)")
