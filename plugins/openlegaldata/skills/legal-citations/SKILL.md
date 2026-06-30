---
name: legal-citations
description: Check, resolve and fact-check legal citations across OpenLegalData (US, UK, EU, Ireland, Canada, Australia, NZ + world). Confirm a citation is real, resolve it to the source record/URL, find citations on a topic within a jurisdiction (cite_search), and verify that what a text CLAIMS about a cite is actually supported. HTTP-first: GET the citation gateway at resolver.openlegaldata.net (/resolve, /cite_search) with your web-fetch tool — it does the routing and parallel island fan-out server-side. Distinct from case-law discovery (legal-caselaw) — this is citations.
---

> **HTTP-first — just GET the gateway.** Everything is a plain HTTPS **GET that returns
> JSON**; call it with your native web-fetch/HTTP tool — no local code needed. The
> **citation gateway** at `resolver.openlegaldata.net` does all the routing and parallel
> island fan-out server-side. (`_lib/legal_search.py` is only an optional Claude-Code
> convenience that wraps these same URLs.)
>
> **Honesty rule:** only data returned from `*.openlegaldata.net` endpoints is an
> authoritative OpenLegalData result. If you cannot reach them, say so plainly — do NOT
> present a general web-search answer as an OpenLegalData verification.
>
> **Access:** data endpoints require an API key. Get one at
> https://openlegaldata.net/account (sign in with LinkedIn) and set
> `OPENLEGALDATA_API_KEY` — the script sends it automatically; for direct fetches add
> header `X-API-Key: <key>` (or `?key=<key>`). The `/` info route stays public.
>
> **No key set, and you can't set an env var (e.g. the claude.ai web sandbox)? ASK THE
> USER for their key**, then pass it inline every call: `--key <key>` on the script, or
> `?key=<key>` on each direct fetch. Don't silently fail or guess — request the key.

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

The **citation gateway** does the whole job server-side: parse the cite (split the
**core** lookup key from the **pinpoint** and any `see`/`cf` signal), route by citation
family, query the candidate islands **in parallel**, merge to a primary + confirmations,
and log the resolution. Just GET it:

```
GET https://resolver.openlegaldata.net/resolve?cite=<citation>&key=<key>
```

Pass the cite **exactly as written** — case name, pincite, year and all; the gateway
extracts the parts (no need to strip it down). Example:
`/resolve?cite=Strickland v. Washington, 466 U.S. 668, 687 (1984)&key=<key>`.
US reporter/neutral cites resolve via the indexed CAP/CourtListener path; other families
hit each island's `/cite`.

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

## Find citations on a topic (`/cite_search`)

To find authorities (with their citations) on a topic — not resolve a known cite — search a
**jurisdiction**'s case law in parallel:

```
GET https://resolver.openlegaldata.net/cite_search?q=<terms>&jurisdiction=<US|UK|EU|IE|CA|AU|NZ|COE|country-slug>&key=<key>
```

`jurisdiction` (or `country`) routes to that jurisdiction's caselaw islands; a world country
slug (`de`, `fr`, `es`, …) hits the island of that name. Each result carries the
**citation**, title, court, date and url — feed a returned citation straight back into
`/resolve` to pin it down, then read + fact-check. This gateway is **citations only**; for
general full-text discovery use the `legal-caselaw` skill.

Example: `/cite_search?q=qualified immunity&jurisdiction=US` → `533 U.S. 194` (Saucier v.
Katz), `483 U.S. 635` (Anderson v. Creighton), …

## Citation families & routing

Routing lives server-side in the gateway (`citations/routing.json` →
`src/core/citeParse.ts`) — you just GET `/resolve`. Families it covers:

- **US reporter** `347 U.S. 483` → CAP/CourtListener `/verify` (15M+ cites, all years).
- **US neutral** `2025 OK 74`, **statute** `42 U.S.C. § 1983`, **reg** `25 CFR 83.11`.
- **UK** `[2020] EWCA Civ 5`, **legislation** `2018 c. 12`; **Ireland** `[2019] IESC 6`.
- **EU** CELEX `32016R0679` / ELI; **ECLI** `ECLI:EU:C:2014:317` (EU, ECtHR, IE).
- **Commonwealth** `2026 SCC 8` (Canada), `Cap. 615` (Hong Kong), AU/NZ statutes.

The gateway picks the family and islands for you — you never classify a cite yourself.

## Caveats (when a real cite still misses)

- **Impoverished-metadata islands** (`uk`, `ie`, slices of others) were ingested before
  full metadata passthrough — exact-match can miss; you'll get `fts-candidate` instead.
  Don't report "not found" as fabrication for these; fall back to reading the FTS leads.
- **CAP ends at 2020** — newer US cites need CourtListener (the `verify` path tries both).
- **Anonymised corpora** (`ecthr`, NLP benchmarks) carry no resolvable citation — use
  `coe` for live ECtHR.

## Just GET it (any runtime)

```
# resolve a known cite (pass it exactly as written):
GET https://resolver.openlegaldata.net/resolve?cite=Roe v. Wade, 410 U.S. 113, 153 (1973)&key=<key>
#  -> { found, record:{title,url}, pinpoint, confirmations, ... }
#     found:false  => do NOT present the citation as established.

# find citations on a topic in a jurisdiction:
GET https://resolver.openlegaldata.net/cite_search?q=qualified immunity&jurisdiction=US&key=<key>

# then read the source and fact-check: open record.url, or the island's /doc?id= / CAP /case/<id>.
```

Optional Claude-Code wrapper (parallelises the same URLs):
`python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" cite "<cite>" [--key <key>]`.
