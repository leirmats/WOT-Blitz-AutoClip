import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "https://blitzhangar.com"
INDEX = BASE + "/en/"
UA = "WoT-Blitz-AutoClip/27 tank database builder"

def get(url):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def parse_links(page):
    links = re.findall(r'href=["\'](/en/tank/[^"\']+)["\']', page)
    out = []
    seen = set()
    for x in links:
        if x not in seen:
            seen.add(x)
            out.append(BASE + x)
    return out

def parse_tank(page, url):
    m = re.search(r'<h1[^>]*>\s*(.*?)\s*</h1>', page, re.I | re.S)
    if not m:
        raise ValueError("No h1: " + url)
    h1 = re.sub(r"<[^>]+>", "", m.group(1))
    h1 = html.unescape(h1).strip()
    # Example: Sheridan — Tier X American light tank
    m = re.match(r"(.+?)\s+—\s+Tier\s+([IVX]+)\s+(.+?)\s+(light|medium|heavy) tank\s*$", h1, re.I)
    if not m:
        m = re.match(r"(.+?)\s+—\s+Tier\s+([IVX]+)\s+(.+?)\s+tank destroyer\s*$", h1, re.I)
        if m:
            return {"name": m.group(1).strip(), "tier": m.group(2), "type": "Tank Destroyer"}
        raise ValueError("Could not parse: " + h1)
    cls = m.group(4).capitalize()
    return {"name": m.group(1).strip(), "tier": m.group(2), "type": cls}

def main():
    page = get(INDEX)
    urls = parse_links(page)
    if len(urls) < 590:
        raise RuntimeError(f"BlitzHangar tank links unexpectedly low: {len(urls)}")

    records = []
    errors = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(get, u): u for u in urls}
        for i, future in enumerate(as_completed(futures), 1):
            u = futures[future]
            try:
                records.append(parse_tank(future.result(), u))
            except Exception as e:
                errors.append(f"{u}: {e}")
            if i % 50 == 0:
                print(f"Fetched {i}/{len(urls)}")

    if errors:
        print(f"Warnings: {len(errors)} tank pages failed")
        for e in errors[:10]:
            print(e)

    # Remove exact duplicate display entries while retaining different variants.
    unique = {}
    for r in records:
        key = (r["name"].casefold(), r["tier"], r["type"])
        unique[key] = r
    records = sorted(unique.values(), key=lambda x: x["name"].casefold())

    if len(records) < 590:
        raise RuntimeError(f"Parsed tank database unexpectedly low: {len(records)}")

    with open("tank_data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Generated tank_data.json with {len(records)} tanks")
    print("Types:", {t: sum(1 for r in records if r["type"] == t) for t in ["Light","Medium","Heavy","Tank Destroyer"]})

if __name__ == "__main__":
    main()
