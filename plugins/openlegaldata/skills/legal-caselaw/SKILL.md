---
name: legal-caselaw
description: Research US case law — find precedent on a legal issue, read full opinions, and rank cases by importance. Use when the user asks about court decisions, holdings, precedent, "what cases say about X", or wants to read an opinion. NOT for citation verification (use legal-citations), contract clauses (legal-contracts), or statutes (legal-statutes).
---

> **Calling the islands (works in any runtime).** Every endpoint below is a plain
> public HTTPS **GET that returns JSON** — call it with whatever fetch/HTTP tool you
> have (e.g. web-fetch). The bundled `_lib/legal_search.py` only *parallelizes* these
> same calls and needs a shell + outbound network: it works in Claude Code, but
> sandboxed runtimes (e.g. the claude.ai Skills container) may block egress. **If the
> script is blocked, just fetch the URL directly instead.**
>
> **Honesty rule:** only data returned from these `*.openlegaldata.net` endpoints is an
> authoritative OpenLegalData result. If you cannot reach them, say so plainly — do
> NOT present a general web-search answer as an OpenLegalData verification.
>
> **Access:** the data endpoints (`/search`, `/verify`, `/case`) now require an API key.
> Get one at https://openlegaldata.net/account (sign in with LinkedIn) and set
> `OPENLEGALDATA_API_KEY` — `legal_search.py` sends it automatically; for direct fetches
> add header `X-API-Key: <key>` (or `?key=<key>`). The `/` info route stays public.


# Legal Case Law Research

Each island is a different tool — **they do NOT search the same way.** Use the right one:

| Island | URL | What it's for | Search type |
|---|---|---|---|
| **CourtListener** | courtlistener.openlegaldata.net | **Discovery** — find cases on a topic across all US case law (incl. post-2020). | **Full-text**, and can rank by citation count |
| **CAP** | cap.openlegaldata.net | **Reading** — full opinion bodies (through 2020) + pagerank importance. | **Case NAME / citation only — NOT topical** |
| SCOTUS | scotus.openlegaldata.net | Supreme Court opinion **passages** (good for quotes). | Full-text passages |
| CaseHOLD | casehold.openlegaldata.net | Holding statements. | Full-text passages |

> ⚠️ **Do not topic-search CAP.** CAP's `/search` matches case *names* only, so
> `"qualified immunity"` returns nothing. Topical discovery is CourtListener's job.

## The flow

**1. Find the leading cases on a topic** — CourtListener full-text ranked by citation
count (most-cited matches = the leading/precedent-setting cases):

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" leading "qualified immunity" --limit 10
```
Returns clean records: `name`, `citation`, `citeCount`, `court`, `dateFiled`. The top
rows are the canonical cases (e.g. Harlow v. Fitzgerald for QI). Use `citeCount` as the
importance signal. (Plain relevance search: drop `--limit`'s sibling and call
`search "<topic>" --islands https://courtlistener.openlegaldata.net`.)

**2. Read the top opinion** — resolve its citation to CAP, then fetch the full body:

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" verify "457 U.S. 800"   # -> caseId
curl "https://cap.openlegaldata.net/case/<caseId>"                                     # full opinion text
```
CAP bodies are write-through from the free static.case.law host (first hit live, then
cached). For cases after 2020 (not in CAP), use the CourtListener result's `url`.

**3. Quotes / specific holdings** — for passage-level text, also search the passage
islands in parallel:
```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "<exact phrase>" --category caselaw --limit 10
```
(Here CAP contributes name-matches only; SCOTUS/CaseHOLD give the passages.)

**4. Verifying a specific citation** is the **legal-citations** skill, not this one.

## Strategy summary
1. Topic → `leading "<topic>"` (CourtListener, ranked by citeCount). **This is the default for "leading/important cases on X".**
2. Read the winner → `verify "<cite>"` → CAP `/case/<id>`.
3. Post-2020 → CourtListener `url`.  Passages/quotes → `search --category caselaw`.

## Endpoints
- CourtListener `GET /search?q=<terms>&order=citeCount&limit=N` — full-text, leading-first.
- CAP `GET /case/<id>` — full opinion; `GET /verify?cite=<cite>` — citation → case.
- CAP/SCOTUS/CaseHOLD `GET /search?q=<terms>&limit=N` — (CAP = names only).

```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import leading, verify
cases = leading("dormant commerce clause", limit=10)   # ranked by citation count
```
