#!/usr/bin/env python3
"""Fetch landmark photos for one city from Wikimedia (zh.wikipedia pageimages).

Usage: python3 scripts/fetch_images.py <city-id> [--force]

Reads data/cities/<city-id>.json (each dest needs "key" and "wiki"), downloads
one freely-licensed photo per dest into assets/img/<city-id>/<key>.jpg and
records file / license / artist in assets/img/<city-id>/credits.json.
Skips dests whose image already exists unless --force. Rate-limit friendly:
4s between dests, backoff on HTTP 429. Exits 1 if any dest failed."""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "wheelkend/1.0 (personal project)"}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FORCE = "--force" in sys.argv
if len(args) != 1:
    sys.exit("usage: fetch_images.py <city-id> [--force]")
CITY = args[0]

CITY_JSON = os.path.join(ROOT, "data", "cities", f"{CITY}.json")
IMGDIR = os.path.join(ROOT, "assets", "img", CITY)
CREDITS = os.path.join(IMGDIR, "credits.json")
os.makedirs(IMGDIR, exist_ok=True)

cfg = json.load(open(CITY_JSON, encoding="utf-8"))

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

def fetch_dest(key, title):
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
for d in cfg["dests"]:
    key, title = d["key"], d.get("wiki")
    if not title:
        results.append({"key": key, "error": "no wiki title in city json"})
        print(f"[FAIL] {key}: no wiki title", flush=True)
        continue
    dest = os.path.join(IMGDIR, f"{key}.jpg")
    if not FORCE and key in prev and os.path.exists(dest):
        results.append(prev[key])
        print(f"[SKIP] {key} already fetched", flush=True)
        continue
    try:
        res = fetch_dest(key, title)
    except Exception as e:
        res = {"key": key, "title": title, "error": repr(e)}
    results.append(res)
    status = "OK" if "saved" in res else "FAIL"
    print(f"[{status}] {key} {title} -> {res.get('license', res.get('error'))}", flush=True)
    time.sleep(4)

with open(CREDITS, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

fails = [r["key"] for r in results if "error" in r]
print(f"\n{CITY}: {len(results)-len(fails)}/{len(results)} ok. FAILS: {fails or 'none'}")
sys.exit(1 if fails else 0)
