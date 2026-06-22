---
name: legal-statutes
description: Find statute and regulation text — US Code, federal regulations (CFR), the Federal Register, EU legislation, US state statutes, and bills. Use when the user asks "what does the statute/regulation say", cites a USC/CFR section, or needs legislative/regulatory text. NOT case law (legal-caselaw) and NOT contracts (legal-contracts).
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


# Statutes & Regulations

Primary legislative + regulatory text across jurisdictions.

| Island | URL | Body of law |
|---|---|---|
| **USC** | usc.openlegaldata.net | United States Code (federal statutes). |
| **eCFR** | ecfr.openlegaldata.net | Code of Federal Regulations (federal agency regs). |
| **Federal Register** | fedreg.openlegaldata.net | Rules/notices (recent) with effective dates. |
| **EUR-Lex** | eurlex.openlegaldata.net | EU legislation. |
| **Georgia O.C.G.A.** | us-ga.openlegaldata.net | US **state** statutes (Georgia; clean public domain). |
| **Bills / BillSum** | bills / billsum .openlegaldata.net | US federal bills + summaries. |

> Coverage note: USC and eCFR are currently **representative subsets**, not the full
> title set — say so if a specific section isn't found, and fall back to the official
> source. State coverage is currently Georgia only.

## How to use

**Parallel search across statutory/regulatory islands:**
```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "clean air act emissions" --category statutes --limit 10
```

## Strategy
1. Federal **statute** → USC; federal **regulation** → eCFR; **rule/notice + effective
   date** → Federal Register; **EU** → EUR-Lex; **US state** → us-ga (Georgia).
2. Parallel `/search --category statutes` when the jurisdiction/source is unknown.
3. For a specific citation (e.g. "42 U.S.C. § 7401"), search the section number/terms;
   confirm against the official source given the subset caveat.
4. For **foreign/national** legislation beyond the US/EU, use the **legal-world** skill.

## Endpoints
- `GET /search?q=<terms>&limit=N` per island; `GET /` for info.

```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import search
hits = search("securities exchange disclosure", category="statutes", limit=15)
```
