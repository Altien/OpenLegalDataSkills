---
name: legal-caselaw
description: Research US case law — find precedent on a legal issue, read full opinions, and rank cases by importance. Use when the user asks about court decisions, holdings, precedent, "what cases say about X", or wants to read an opinion. NOT for citation verification (use legal-citations), contract clauses (legal-contracts), or statutes (legal-statutes).
---

# Legal Case Law Research

Searches the OpenLegalData case-law islands (independent Cloudflare Workers) and
retrieves full opinion text. Coverage:

| Island | URL | Role |
|---|---|---|
| **CAP** | cap.openlegaldata.net | Full published US case law **through 2020** (~6.7M cases). Best for reading opinions + importance ranking (`pagerank`). |
| **CourtListener** | courtlistener.openlegaldata.net | Citation index for **all** US cases incl. **post-2020**; live search fallback. |
| SCOTUS | scotus.openlegaldata.net | Curated Supreme Court opinion passages. |
| CaseHOLD | casehold.openlegaldata.net | Case holdings (holding-statement retrieval / QA). |

## How to search — order matters

**1. Always search in PARALLEL, never island-by-island.** Use the bundled utility:

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "qualified immunity police" --category caselaw --limit 10
```

It fans the query across all case-law islands at once, merges, and interleaves by
each island's own rank so no single big island drowns the others. CAP results carry
an `importance` (pagerank percentile, 0–1) — **a high `importance` means a heavily-cited,
leading case.** Prefer those.

**2. To read an opinion, fetch the body from CAP** (write-through from the free
static.case.law host — first hit is live, then cached):

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" case https://cap.openlegaldata.net <caseId>
# or: curl "https://cap.openlegaldata.net/case/<caseId>"
```

**3. For recent cases (decided after 2020),** CAP won't have them — rely on the
CourtListener results in the merged list (it indexes all years), then follow its
`url` to courtlistener.com for the body, or use the live CL search.

**4. Resolving a specific citation** ("467 U.S. 837") is a different task — use the
**legal-citations** skill.

## Strategy summary
1. Broad parallel `/search --category caselaw`.
2. Rank: prefer high `importance` (CAP pagerank); these are the precedent-setting cases.
3. Read top opinions via CAP `/case/<id>`.
4. Recent (>2020) → CourtListener entries in the same result set.

## Endpoints (per island)
- `GET /search?q=<terms>&jurisdiction=<name>&limit=N` — FTS; CAP adds pagerank ranking.
- `GET /case/<id>` (CAP) / `GET /cluster/<id>` (CourtListener) — opinion body.
- `GET /` — island info + counts.

Import the utility directly for richer flows:
```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import search
hits = search("commerce clause dormant", category="caselaw", limit=20)
```
