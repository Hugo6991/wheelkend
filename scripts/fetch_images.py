#!/usr/bin/env python3
"""Refresh landmark photos from Wikimedia (zh.wikipedia pageimages).

Downloads one freely-licensed photo per city into assets/img/<key>.jpg and
records file / license / artist in assets/credits.json. Skips cities whose
image already exists; delete a jpg (or run with --force) to refetch it.
Rate-limit friendly: 4s between cities, backoff on HTTP 429."""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "assets", "img")
CREDITS = os.path.join(ROOT, "assets", "credits.json")
os.makedirs(IMGDIR, exist_ok=True)

UA = {"User-Agent": "wheelkend/1.0 (personal project)"}
FORCE = "--force" in sys.argv

# key -> zh.wikipedia article whose lead image represents the city
CITIES = [
    ("suzhou",    "拙政园"),
    ("hangzhou",  "西湖"),
    ("wuxi",      "鼋头渚"),
    ("nanjing",   "中山陵"),
    ("jiaxing",   "南湖 (嘉兴)"),
    ("wuzhen",    "乌镇"),
    ("shaoxing",  "沈园"),
    ("ningbo",    "天一阁"),
    ("changzhou", "南山竹海"),
    ("nantong",   "南通博物苑"),
    ("yangzhou",  "瘦西湖"),
    ("moganshan", "莫干山"),
    ("qiandaohu", "千岛湖"),
    ("huangshan", "黄山"),
]

def get(url, timeout=30):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = 8 * (attempt + 1)
                print(f"    429, backing off {wait}s...", flush=True)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")

def api(host, params):
    return json.loads(get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(params)))

def fetch_city(key, title):
    q = api("zh.wikipedia.org", {
        "action": "query", "titles": title, "prop": "pageimages",
        "piprop": "thumbnail|name", "pithumbsize": "800",
        "format": "json", "redirects": "1", "converttitles": "1",
    })
    page = next(iter(q.get("query", {}).get("pages", {}).values()), {})
    thumb = page.get("thumbnail", {}).get("source")
    filename = page.get("pageimage")
    if not thumb or not filename:
        return {"key": key, "title": title, "error": "no pageimage"}
    mi = api("commons.wikimedia.org", {
        "action": "query", "titles": f"File:{filename}", "prop": "imageinfo",
        "iiprop": "extmetadata", "iiextmetadatafilter": "LicenseShortName|Artist",
        "format": "json",
    })
    mp = next(iter(mi.get("query", {}).get("pages", {}).values()), {})
    ext = (mp.get("imageinfo") or [{}])[0].get("extmetadata", {})
    dest = os.path.join(IMGDIR, f"{key}.jpg")
    with open(dest, "wb") as f:
        f.write(get(thumb, timeout=60))
    return {"key": key, "title": title, "file": filename, "thumb": thumb,
            "saved": dest, "bytes": os.path.getsize(dest),
            "license": ext.get("LicenseShortName", {}).get("value", "?"),
            "artist": ext.get("Artist", {}).get("value", "?")[:200]}

prev = {}
if os.path.exists(CREDITS):
    for r in json.load(open(CREDITS, encoding="utf-8")):
        prev[r["key"]] = r

results = []
for key, title in CITIES:
    dest = os.path.join(IMGDIR, f"{key}.jpg")
    if not FORCE and key in prev and os.path.exists(dest):
        results.append(prev[key])
        print(f"[SKIP] {key} already fetched", flush=True)
        continue
    try:
        res = fetch_city(key, title)
    except Exception as e:
        res = {"key": key, "title": title, "error": repr(e)}
    results.append(res)
    status = "OK" if "saved" in res else "FAIL"
    print(f"[{status}] {key} {title} -> {res.get('license', res.get('error'))}", flush=True)
    time.sleep(4)

with open(CREDITS, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

fails = [r["key"] for r in results if "error" in r]
print(f"\nDone. {len(results)-len(fails)}/{len(results)} ok. FAILS: {fails or 'none'}")
if fails:
    sys.exit(1)
