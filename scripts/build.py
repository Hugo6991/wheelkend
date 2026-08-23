#!/usr/bin/env python3
"""Assemble dist/ for the multi-city site.

- copies src/index.html, src/app.js, vendor/leaflet → dist/
- for each data/cities/<id>.json (except index.json):
    * merges photo credits from assets/img/<id>/credits.json into the city json
    * writes dist/data/cities/<id>.json
    * recompresses assets/img/<id>/<key>.jpg → dist/img/<id>/<key>.jpg (sips, 640px q55)
- fails loudly on missing files; reports every dest without a photo."""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
DATA = os.path.join(ROOT, "data", "cities")
ASSETS = os.path.join(ROOT, "assets", "img")
DIST = os.path.join(ROOT, "dist")

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

if os.path.isdir(DIST):
    shutil.rmtree(DIST)
os.makedirs(os.path.join(DIST, "data", "cities"))

shutil.copy2(os.path.join(SRC, "index.html"), os.path.join(DIST, "index.html"))
shutil.copy2(os.path.join(SRC, "app.js"), os.path.join(DIST, "app.js"))
shutil.copytree(os.path.join(ROOT, "vendor"), os.path.join(DIST, "vendor"))

manifest = os.path.join(DATA, "index.json")
shutil.copy2(manifest, os.path.join(DIST, "data", "cities", "index.json"))

missing = []
total_img = 0
for fn in sorted(os.listdir(DATA)):
    if not fn.endswith(".json") or fn == "index.json":
        continue
    cid = fn[:-5]
    cfg = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))

    creds_path = os.path.join(ASSETS, cid, "credits.json")
    lines = []
    if os.path.exists(creds_path):
        creds = {c["key"]: c for c in json.load(open(creds_path, encoding="utf-8"))}
        names = {d["key"]: d["name"] for d in cfg["dests"]}
        for key, c in creds.items():
            if "error" in c:
                continue
            artist = strip_tags(c.get("artist", ""))[:60] or "見 Commons 檔案頁"
            lines.append(f"{names.get(key, key)}（{c.get('file', '')}）：{artist}，"
                         f"{c.get('license', '?')}，via Wikimedia Commons")
    cfg["credits"] = lines

    out_img = os.path.join(DIST, "img", cid)
    os.makedirs(out_img, exist_ok=True)
    n_ok = 0
    for d in cfg["dests"]:
        src_img = os.path.join(ASSETS, cid, f"{d['key']}.jpg")
        if not os.path.exists(src_img):
            missing.append(f"{cid}/{d['key']}")
            continue
        dst_img = os.path.join(out_img, f"{d['key']}.jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "55",
                        "-Z", "640", src_img, "--out", dst_img],
                       check=True, capture_output=True)
        total_img += os.path.getsize(dst_img)
        n_ok += 1

    json.dump(cfg, open(os.path.join(DIST, "data", "cities", fn), "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"[OK] {cid}: {n_ok}/{len(cfg['dests'])} photos, {len(lines)} credits")

print(f"\ndist ready: images {total_img//1024} KB total")
if missing:
    print(f"[WARN] missing photos (text fallback will show): {missing}")
