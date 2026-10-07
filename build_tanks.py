import html
import json
import re
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

    # BlitzHangar currently uses both:
    #   "Sheridan — Tier X American light tank"
    #   "Edelweiss — Tier VII medium tank of Hybrid nation"
    # The nation suffix is metadata and is not part of the tank class.
    pattern = re.compile(
        r"(.+?)\s+—\s+Tier\s+([IVX]+)\s+"
        r"(?:.+?\s+)?(light|medium|heavy)\s+tank"
        r"(?:\s+of\s+.+?\s+nation)?\s*$",
        re.I,
    )
    m = pattern.match(h1)
    if m:
        return {
            "name": m.group(1).strip(),
            "tier": m.group(2),
            "type": m.group(3).capitalize(),
        }

    td_pattern = re.compile(
        r"(.+?)\s+—\s+Tier\s+([IVX]+)\s+"
        r"(?:.+?\s+)?tank destroyer"
        r"(?:\s+of\s+.+?\s+nation)?\s*$",
        re.I,
    )
    m = td_pattern.match(h1)
    if m:
        return {
            "name": m.group(1).strip(),
            "tier": m.group(2),
            "type": "Tank Destroyer",
        }

    raise ValueError("Could not parse: " + h1)


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

    unique = {}
    for r in records:
        key = (r["name"].casefold(), r["tier"], r["type"])
        unique[key] = r
    records = sorted(unique.values(), key=lambda x: x["name"].casefold())

    # BlitzHangar currently exposes this tank with the wrong name.
    # Keep the source-driven database, but correct the displayed tank name.
    for r in records:
        if r["name"] == "HWK 30":
            r["name"] = "HWK 12"

    if len(records) < 590:
        raise RuntimeError(f"Parsed tank database unexpectedly low: {len(records)}")

    with open("tank_data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Generated tank_data.json with {len(records)} tanks")
    print(
        "Types:",
        {
            t: sum(1 for r in records if r["type"] == t)
            for t in ["Light", "Medium", "Heavy", "Tank Destroyer"]
        },
    )


if __name__ == "__main__":
    main()
