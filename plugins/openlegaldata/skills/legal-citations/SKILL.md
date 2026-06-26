---
name: legal-citations
description: Verify and resolve US legal citations. Use when you need to check that a citation (e.g. "467 U.S. 837") is real, resolve it to the case name/court/date, or ground citations in generated text against an authoritative source. Distinct from case-law research (legal-caselaw) — this is verification, not discovery.
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


# Legal Citation Verification

Resolves a reporter citation to the actual case, against two authoritative indexes
in parallel. **Use this to ground every case citation you output** — never assert a
citation is valid without checking it here.

| Island | URL | Coverage |
|---|---|---|
| **CourtListener** | courtlistener.openlegaldata.net | 15.0M citations, **all years incl. post-2020** |
| **CAP** | cap.openlegaldata.net | Through 2020, and **links straight to the full opinion body** |

## Verify a citation

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" verify "467 U.S. 837"
```

This fans the cite across both islands concurrently and returns the first
authoritative hit (CAP preferred — it can also serve the body):

```json
{ "cite": "467 U.S. 837", "status": "ok", "_island": "cap", "caseId": 1234,
  "case": { "name_abbr": "Chevron U.S.A. Inc. v. NRDC", "court": "...", "decision_date": "1984-06-25" },
  "body": "/case/1234" }
```

- `status: "ok"` → the citation is **real**; use the returned name/court/date.
- `status: "not_found"` → it does **not** resolve. Treat the citation as **unverified**
  — do not present it as established. (CAP ends at 2020; if CL also misses it, it may be
  a very recent, unpublished, or fabricated cite.)

## Resolve → read
After a CAP hit, fetch the opinion with the returned `body` path:
`curl "https://cap.openlegaldata.net/case/<caseId>"`.

## Citation format
`<volume> <reporter> <page>` — e.g. `347 U.S. 483`, `589 F.3d 1179`, `5 U.S. 137`.
Parallel/regional reporters work if they're in the index; if one form misses, try
another reporter for the same case.

## Programmatic
```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import verify
v = verify("410 U.S. 113")
assert v["status"] == "ok", "citation does not resolve — do not cite it"
```
