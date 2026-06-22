#!/usr/bin/env python3
"""Parallel multi-island search over OpenLegalData (stdlib only).

The skills call this to fan a query across every island in a category AT ONCE
(not one-by-one), merge, and rank. Islands are independent Workers, so parallel
is strictly faster and gives broader recall.

CLI:
  python legal_search.py search "qualified immunity" --category caselaw [--limit 10]
  python legal_search.py verify "467 U.S. 837"
  python legal_search.py case <island_url> <id>
  python legal_search.py list                      # show categories + islands

Import:
  from legal_search import search, verify, REGISTRY
  hits = search("force majeure", category="contracts", limit=10)
"""
import sys, os, json, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Force UTF-8 stdout so non-Latin results (German, Arabic, Cyrillic, Greek ...)
# print on Windows consoles (default cp1252) instead of crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REGISTRY = json.load(open(os.path.join(os.path.dirname(__file__), "islands.json")))
UA = {"User-Agent": "OpenLegalData-skill/1.0"}
TIMEOUT = 20


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def _islands(category=None, islands=None):
    """Resolve a target list of {slug,url} dicts."""
    if islands:
        return [{"slug": u.rstrip("/").split("//")[-1].split(".")[0], "url": u} for u in islands]
    if category:
        return [i for i in REGISTRY.get(category, []) if i.get("url")]
    # default: everything searchable
    seen, out = set(), []
    for cat in ("caselaw", "contracts", "statutes", "world"):
        for i in REGISTRY.get(cat, []):
            if i.get("url") and i["url"] not in seen:
                seen.add(i["url"]); out.append(i)
    return out


def _search_one(island, query, limit):
    url = f"{island['url']}/search?q={urllib.parse.quote(query)}&limit={limit}"
    try:
        d = _get(url)
        for r in d.get("results", []):
            r["_island"] = island["slug"]
        return d.get("results", [])
    except Exception as e:
        return [{"_island": island["slug"], "_error": str(e)[:120]}]


def search(query, category=None, islands=None, limit=10, max_workers=16):
    """Fan `query` across islands in PARALLEL; return a merged, ranked list.

    Ranking: each island already returns its own best matches (BM25, or pagerank
    for CAP). We interleave by per-island rank so no single big island drowns the
    others, and surface an island's `importance`/pagerank when present.
    """
    targets = _islands(category, islands)
    per_island = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_search_one, i, query, limit): i["slug"] for i in targets}
        for f in as_completed(futs):
            per_island[futs[f]] = [r for r in f.result() if "_error" not in r]
    # interleave: round-robin by within-island rank, but let CAP/pagerank float up
    merged = []
    rank = 0
    while any(per_island.values()):
        for slug in list(per_island):
            if per_island[slug]:
                row = per_island[slug].pop(0)
                row["_rank_in_island"] = rank
                merged.append(row)
        rank += 1
    merged.sort(key=lambda r: (r.get("_rank_in_island", 0), -(r.get("importance") or 0)))
    return merged


def verify(cite, max_workers=4):
    """Resolve a citation against every /verify-capable island in parallel.
    Returns the first authoritative hit (prefers a result that includes a body)."""
    targets = REGISTRY.get("verify", [])
    hits = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {}
        for i in targets:
            url = f"{i['url']}/verify?cite={urllib.parse.quote(cite)}"
            futs[ex.submit(_get, url)] = i["slug"]
        for f in as_completed(futs):
            try:
                d = f.result()
                if d.get("status") == "ok":
                    d["_island"] = futs[f]
                    hits.append(d)
            except Exception:
                pass
    # prefer a hit that can serve a body (cap), else any ok hit
    hits.sort(key=lambda h: 0 if h.get("_island") == "cap" else 1)
    return hits[0] if hits else {"cite": cite, "status": "not_found"}


def _main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "list":
        for cat, items in REGISTRY.items():
            print(f"{cat} ({len(items)}): " + ", ".join(i.get("slug", "?") for i in items[:12]) + (" ..." if len(items) > 12 else ""))
    elif a[0] == "search":
        q = a[1]
        cat = a[a.index("--category") + 1] if "--category" in a else None
        lim = int(a[a.index("--limit") + 1]) if "--limit" in a else 10
        isl = None
        if "--islands" in a:
            isl = [x for x in a[a.index("--islands") + 1:] if x.startswith("http")]
        res = search(q, category=cat, islands=isl, limit=lim)
        print(json.dumps(res[:lim], indent=2, ensure_ascii=False))
    elif a[0] == "verify":
        print(json.dumps(verify(a[1]), indent=2, ensure_ascii=False))
    elif a[0] == "case":
        print(json.dumps(_get(f"{a[1].rstrip('/')}/case/{a[2]}"), indent=2, ensure_ascii=False)[:4000])
    else:
        print(__doc__)


if __name__ == "__main__":
    _main()
