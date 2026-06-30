---
name: legal-citations
description: Check, resolve and fact-check legal citations against OpenLegalData islands across jurisdictions (US, UK, EU, Ireland, Canada, Australia, NZ + world). Use to confirm a citation is real, resolve it to the source record/URL, and verify that what a text CLAIMS about it is actually supported. US reporter cites resolve fastest via CAP/CourtListener; other jurisdictions route by citation family to the right island. Distinct from case-law discovery (legal-caselaw) — this is verification.
---

> **Calling the islands (works in any runtime).** Every endpoint below is a plain
> public HTTPS **GET that returns JSON** — call it with whatever fetch/HTTP tool you
> have. The bundled `_lib/legal_search.py` only *parallelizes/routes* these same calls
> and needs a shell + outbound network: it works in Claude Code, but sandboxed runtimes
> (e.g. the claude.ai Skills container) may block egress. **If the script is blocked, it
> prints the exact URLs to fetch directly instead.**
>
> **Honesty rule:** only data returned from `*.openlegaldata.net` endpoints is an
> authoritative OpenLegalData result. If you cannot reach them, say so plainly — do NOT
> present a general web-search answer as an OpenLegalData verification.
>
> **Access:** data endpoints require an API key. Get one at
> https://openlegaldata.net/account (sign in with LinkedIn) and set
> `OPENLEGALDATA_API_KEY` — the script sends it automatically; for direct fetches add
> header `X-API-Key: <key>` (or `?key=<key>`). The `/` info route stays public.

# Legal Citation Checking

Two jobs, in order: **resolve** the citation to the real record (does it exist, and
where does it point?), then **fact-check** the surrounding text against it (is what the
author *said* about it actually true?). **Ground every legal citation you output this
way — never assert a citation is valid, or that it stands for a proposition, without
checking it here.**

## The flow

```
citation ─▶ resolve ─▶ read the record ─▶ fact-check the claim ─▶ verdict
```

The `cite` command is a thin client of the **resolver service**
(`resolver.openlegaldata.net`), which does the whole job server-side: parse the cite
(split the **core** lookup key from the **pinpoint** and any `see`/`cf` signal), route by
citation family, query the candidate islands **in parallel**, merge to a primary +
confirmations, and log the resolution.

```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" cite "Strickland v. Washington, 466 U.S. 668, 687 (1984)"
```

Pass the cite **exactly as written** — case name, pincite, year and all; the resolver
extracts the parts (no need to strip it down yourself). US reporter/neutral cites take the
indexed `/verify` path (CAP + CourtListener); other families hit each island's `/cite`.

### What you get back

```json
{ "resolutionId": "…", "found": true, "confidence": "exact",
  "family": "us-reporter", "core": "466 U.S. 668", "island": "cap",
  "record": { "id": 1234, "title": "Strickland v. Washington", "url": "https://cap.openlegaldata.net/case/1234" },
  "pinpoint": { "scheme": "page", "value": "687" },
  "confirmations": [ { "island": "courtlistener", "id": 99 } ] }
```

- **`found: true`** (`confidence: "exact"` or `"verified"`) → the citation is **real**; use
  the returned `title`/`url`. `confirmations` = other islands that independently resolved
  the same authority — more confirmations, stronger evidence. Read the source next (below).
- **`confidence: "fts-candidate"`** → no exact match, but passages mention the cite. These
  are **leads, not a resolution** — open them and judge before relying on them.
- **`found: false`, `confidence: "none"`** (or `status: "not_found"`) → it does **not**
  resolve. Treat the citation as **unverified** — do not present it as established. (CAP
  ends at 2020; an impoverished-metadata island may also miss a real cite — see caveats.)

## Read the source, then fact-check the claim

Resolving only proves the cite is real. The fact-check is the point: pull the actual text
and test the author's assertion against it.

- **CAP hit:** `GET https://cap.openlegaldata.net/case/<caseId>` returns the opinion body.
- **`/cite` hit:** open `record.url`, or `GET https://<island>.openlegaldata.net/doc?id=<record.id>`
  for the stored full text, then jump to the `pinpoint` (page / paragraph / section /
  Article per the family).

Then classify the claim:

| Verdict | Meaning |
|---|---|
| **supported** | the source says what the text claims; cite + proposition both check out |
| **unsupported** | the cite is real but the source does **not** say what's claimed (wrong pinpoint, overstated holding, misattributed) |
| **contradicted** | the source says the opposite |
| **unresolvable** | the cite didn't resolve (`none`), or the island lacks the text to judge — say so, don't guess |

Report the verdict with the pinpoint you checked and a short quote. **A real citation
attached to a false claim is the failure this skill exists to catch.**

## Citation families & routing

Routing lives in the resolver (`citations/routing.json` → `src/core/citeParse.ts`), not in
the skill — `cite` just calls `/resolve`. Families it covers:

- **US reporter** `347 U.S. 483` → CAP/CourtListener `/verify` (15M+ cites, all years).
- **US neutral** `2025 OK 74`, **statute** `42 U.S.C. § 1983`, **reg** `25 CFR 83.11`.
- **UK** `[2020] EWCA Civ 5`, **legislation** `2018 c. 12`; **Ireland** `[2019] IESC 6`.
- **EU** CELEX `32016R0679` / ELI; **ECLI** `ECLI:EU:C:2014:317` (EU, ECtHR, IE).
- **Commonwealth** `2026 SCC 8` (Canada), `Cap. 615` (Hong Kong), AU/NZ statutes.

`python legal_search.py cite "<cite>"` routes and resolves for you (the resolver's parser
is covered by `tests/citeParse.test.ts` + `citations/routing.test.mjs`).

## Caveats (when a real cite still misses)

- **Impoverished-metadata islands** (`uk`, `ie`, slices of others) were ingested before
  full metadata passthrough — exact-match can miss; you'll get `fts-candidate` instead.
  Don't report "not found" as fabrication for these; fall back to reading the FTS leads.
- **CAP ends at 2020** — newer US cites need CourtListener (the `verify` path tries both).
- **Anonymised corpora** (`ecthr`, NLP benchmarks) carry no resolvable citation — use
  `coe` for live ECtHR.

## Programmatic

```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import cite, verify
r = cite("Roe v. Wade, 410 U.S. 113, 153 (1973)")
assert r.get("found"), "citation does not resolve — do not cite it"
# then GET r['record']['url'] (or CAP /case/<id>) and check the claim against the text
```
