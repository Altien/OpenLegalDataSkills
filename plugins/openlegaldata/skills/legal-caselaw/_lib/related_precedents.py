#!/usr/bin/env python3
"""Related-precedent discovery via citation-graph expansion over OpenLegalData.

Walks the citation network around a seed case to surface related precedents,
classifies how later cases treat the seed (the good-law signal), and (optionally)
writes the discovered edges BACK to the island so the next run is a cache hit and
the treatment graph accumulates into a home-grown citator.

CLI:
  python related_precedents.py discover "138 S. Ct. 2206" --name "Carpenter v. United States" \
        --date 2018-06-22 --mode full [--writeback] [--no-cache]
  python related_precedents.py treatment 4510032        # aggregated good-law readout (cache)

Modes:
  authorities  high precision — only the seed's own out-citations (its foundations)
  full         authorities + citing references + treatment tags (higher recall)

Transport: stdlib urllib (skill convention); falls back to `curl` if urllib egress
is blocked (e.g. proxied runtimes), per SKILL.md's "fetch directly" note.
"""
import os, re, json, sys, time, subprocess, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

CL  = "https://courtlistener.openlegaldata.net"          # discovery + opinion bodies
KEY = os.environ.get("OPENLEGALDATA_API_KEY", "")
UA  = {"User-Agent": "OpenLegalData-skill/related-precedents/1.0",
       **({"X-API-Key": KEY} if KEY else {})}
TIMEOUT = 30

# US reporter citation patterns (volume REPORTER page)
_REP = r"(?:U\.\s?S\.|S\.\s?Ct\.|L\.\s?Ed\.\s?2d|L\.\s?Ed\.|F\.\s?Supp\.\s?\d?d?|F\.\s?2d|F\.\s?3d|F\.\s?4th)"
CITE_RE = re.compile(r"\b(\d{1,3})\s+(" + _REP + r")\s+(\d{1,4})\b")

# Cheap pre-tags only — the AUTHORITATIVE treatment call is the LLM classifier
# (see references/edge-classification.prompt.md). These just prioritise the queue.
_TREAT_HINTS = [("overrul", "overruled"), ("abrogat", "abrogated"),
                ("supersed", "superseded"), ("declined to extend", "declined_to_extend"),
                ("distinguish", "distinguished"), ("limited to", "limited"),
                ("called into question", "questioned"), ("criticiz", "criticized"),
                ("reaffirm", "followed"), ("we follow", "followed")]
# treatments that KILL good-law status — never auto-verify, always human (see HITL doc)
HIGH_RISK = {"overruled", "abrogated", "superseded"}


def _get(path_or_url):
    url = path_or_url if path_or_url.startswith("http") else CL + path_or_url
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.load(r)
    except Exception:
        # fall back to curl (configured for proxy/CA in some runtimes)
        hdr = ["-H", f"X-API-Key: {KEY}"] if KEY else []
        out = subprocess.run(["curl", "-sS", "--max-time", str(TIMEOUT), *hdr, url],
                             capture_output=True, text=True, timeout=TIMEOUT + 15).stdout
        return json.loads(out)


def _post(path, body):
    data = json.dumps(body).encode()
    url = CL + path
    try:
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.load(r)
    except Exception:
        hdr = ["-H", f"X-API-Key: {KEY}"] if KEY else []
        out = subprocess.run(["curl", "-sS", "--max-time", str(TIMEOUT), "-X", "POST",
                              *hdr, "-H", "Content-Type: application/json",
                              "--data", json.dumps(body), url],
                             capture_output=True, text=True, timeout=TIMEOUT + 15).stdout
        return json.loads(out) if out.strip() else {}


def canon(vol, rep, page):
    rep = re.sub(r"U\.\s*S\.", "U.S.", rep)       # "U. S." -> "U.S." (verify needs canonical)
    rep = re.sub(r"F\.\s*(\d)", r"F.\1", rep)     # "F. 3d" -> "F.3d"
    rep = re.sub(r"\s+", " ", rep).strip()
    return f"{vol} {rep} {page}"


def verify(cite):
    d = _get("/verify?cite=" + urllib.parse.quote(cite))
    if d.get("status") == "ok":
        c = d.get("cluster") or {}
        return {"clusterId": d.get("clusterId"), "name": c.get("case_name"),
                "date": c.get("date_filed"), "citeCount": c.get("citation_count"),
                "status": c.get("precedential_status"), "cite": cite}
    return None


def search(q, n=8):
    d = _get(f"/search?q={urllib.parse.quote(q)}&page_size={n}&limit={n}")
    return d.get("results", []) or []


def opinion_text(cid):
    d = _get(f"/cluster/{cid}")
    ops = d.get("opinions") or []
    return ops[0].get("text", "") if ops else ""


def pretag_treatment(text, seed_name):
    key = seed_name.split(" v.")[0]
    i = text.find(key)
    if i < 0:
        return "cited_neutral"
    window = text[max(0, i - 220):i + 220].lower()
    for needle, label in _TREAT_HINTS:
        if needle in window:
            return label
    return "cited_neutral"


# ---- writeback cache -------------------------------------------------------
def read_cached_edges(cluster_id):
    try:
        d = _get(f"/edges?cluster={cluster_id}&direction=both")
        return d.get("edges", []), d.get("complete", False)
    except Exception:
        return [], False


def write_edges(edges, run_id):
    if not edges:
        return {}
    return _post("/edges", {"runId": run_id, "edges": edges})


# ---- discovery -------------------------------------------------------------
def discover(seed_cite, seed_name, seed_date, mode="full", use_cache=True, writeback=False):
    seed = verify(seed_cite) or {"clusterId": None, "name": seed_name, "date": seed_date}
    sid = seed["clusterId"]

    if use_cache and sid:
        cached, complete = read_cached_edges(sid)
        if complete and cached:
            return seed, cached, "cache"

    found = {}
    # PHASE 2 — authorities (out-citations parsed from the seed opinion)
    txt = opinion_text(sid) if sid else ""
    raw = [canon(*m.groups()) for m in CITE_RE.finditer(txt)]
    freq = {}
    for c in raw:
        freq[c] = freq.get(c, 0) + 1
    cites = [c for c in freq if not c.startswith(seed_cite.split()[0] + " ")]
    top_auth = sorted(set(cites), key=lambda c: -freq.get(c, 0))[:12]
    with ThreadPoolExecutor(max_workers=5) as ex:
        for r in ex.map(verify, top_auth):
            if r and r["clusterId"] and r["clusterId"] != sid:
                found[r["clusterId"]] = {
                    "fromCluster": sid, "toCluster": r["clusterId"],
                    "fromCite": seed_cite, "toCite": r["cite"], "edgeType": "authority",
                    "reliance": freq.get(r["cite"], 1), "treatment": None,
                    "name": r["name"], "date": r["date"], "citeCount": r["citeCount"],
                    "method": "citation-parse"}

    if mode == "full":
        # PHASE 3 — citing references (in-citations) via unquoted citation/name search
        citing = {r.get("clusterId"): r for r in (search(seed_cite, 10) + search(seed_name, 8))}
        later = [r for r in citing.values()
                 if (r.get("dateFiled") or "") > (seed["date"] or seed_date) and r.get("clusterId") != sid]
        later = sorted(later, key=lambda r: -(r.get("citeCount") or 0))[:8]
        for idx, r in enumerate(later):
            cid = r.get("clusterId")
            tag = pretag_treatment(opinion_text(cid), seed_name) if idx < 4 else "cited_neutral"
            found[cid] = {
                "fromCluster": sid, "toCluster": cid, "fromCite": seed_cite,
                "toCite": (r.get("citation") or [None])[0], "edgeType": "citing",
                "reliance": 1, "treatment": tag, "name": r.get("caseName"),
                "date": r.get("dateFiled"), "citeCount": r.get("citeCount"),
                "method": "citing-search"}

    # score + provenance defaults
    def score(e):
        links = e.get("reliance", 1) * 3
        imp = len(str(e.get("citeCount") or 0))      # crude log10 importance
        risk = 4 if e.get("treatment") in HIGH_RISK else (2 if e.get("treatment") not in (None, "cited_neutral") else 0)
        return links + imp + risk
    edges = sorted(found.values(), key=score, reverse=True)
    for e in edges:
        e["relevanceScore"] = round(min(1.0, score(e) / 20.0), 3)
        e["provenance"] = "derived"
        e["status"] = "pending"
        e["confidence"] = None          # set by the LLM classifier, not here

    if writeback and sid:
        run_id = f"disc-{sid}-{int(time.time())}"
        write_edges(edges, run_id)
    return seed, edges, "derived"


def _fmt(seed, edges, source):
    print(f"SEED: {seed['name']} ({seed.get('date')})  cluster={seed['clusterId']}  [{source}]")
    print(f"\nDISCOVERED {len(edges)} related precedents:\n")
    print(f"{'type':<11}{'date':<12}{'treatment':<16}{'rel':>5}{'cites':>7}  case")
    for e in edges[:20]:
        print(f"{e.get('edgeType',''):<11}{str(e.get('date'))[:10]:<12}"
              f"{str(e.get('treatment') or ''):<16}{str(e.get('relevanceScore') or ''):>5}"
              f"{str(e.get('citeCount') or ''):>7}  {str(e.get('name'))[:50]}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "treatment":
        print(json.dumps(_get(f"/treatment?cluster={sys.argv[2]}"), indent=2))
        sys.exit(0)
    cite = sys.argv[2] if len(sys.argv) > 2 else "138 S. Ct. 2206"
    args = sys.argv[3:]
    name = args[args.index("--name") + 1] if "--name" in args else "Carpenter v. United States"
    date = args[args.index("--date") + 1] if "--date" in args else "2018-06-22"
    mode = args[args.index("--mode") + 1] if "--mode" in args else "full"
    seed, edges, source = discover(cite, name, date, mode=mode,
                                   use_cache="--no-cache" not in args,
                                   writeback="--writeback" in args)
    _fmt(seed, edges, source)
