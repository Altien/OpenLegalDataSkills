---
name: legal-world
description: Comparative and foreign legal research across ~55 country/territory legal-source islands (case law + legislation, each in its native language). Use for non-US/non-EU jurisdictions, comparative-law questions, or "what does <country>'s law say". For US case law use legal-caselaw; for US/EU statutes use legal-statutes.
---

# World / Comparative Legal Sources

Each jurisdiction is its own island at `<cc>.openlegaldata.net` (ISO-ish country
code), built from official government legal sources (courts + legislation), with
**every scraped field preserved as metadata** (court, chamber, decision number,
ECLI, dates, etc.). Content is in each country's **native language** — search in
that language for best recall.

The full list lives in `skills/_lib/islands.json` under `world` (~55 entries:
`ad al am ar at au az ba be bg by ca ch coe cy cz de dk dz ee eg es fi fr ge gr hr hu ie is it li lt lu lv mc me mt nl no nz pl pt ro rs se si sk sm tr tw ua uk xk` …).

## How to use

**Target a specific jurisdiction** (preferred — precise + fast):
```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "Datenschutz" --islands https://de.openlegaldata.net --limit 10
```

**Broad comparative sweep** across ALL world islands in parallel (e.g. "how do
jurisdictions treat X"):
```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "data protection" --category world --limit 5
```
Results are tagged with `_island` (the country) so you can compare across systems.

## Strategy
1. Known jurisdiction → query just that island (`--islands https://<cc>.openlegaldata.net`).
2. Comparative question → parallel `--category world`, then group hits by `_island`.
3. **Search in the jurisdiction's language** (German for `de`, French for `fr`/`lu`/`mc`,
   Arabic for `eg`/`dz`, etc.) — these are native-language corpora.
4. Coverage is **sample corpora** per source (tens–hundreds of docs each), good for
   locating leading/representative texts; not exhaustive. Say so when relevant.

## Endpoints
- `GET /search?q=<terms>&limit=N` per island; `GET /` for info + counts.
- Each result carries rich per-document metadata (the original scraped fields).

```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import search, REGISTRY
fr = [i["url"] for i in REGISTRY["world"] if i["slug"] == "fr"]
hits = search("responsabilité du fait des produits", islands=fr, limit=10)
```
