---
name: legal-contracts
description: Reference real contract clause language and benchmark deal points for DRAFTING and review. Use when the user is writing/reviewing a contract, asks "how is X clause usually worded", wants standard indemnification/limitation-of-liability/MAC language, or wants market-standard M&A deal terms. This is transactional reference — NOT litigation/case-law research (use legal-caselaw).
---

# Contract Clauses & Deal Points

Reference corpora of real, expert-annotated contract language. Use these to find
example clause wording, clause-type coverage, and market-standard terms — a drafting
and review aid, fundamentally different from case-law research.

| Island | URL | What it gives you |
|---|---|---|
| **CUAD** | cuad.openlegaldata.net | 41 clause types across commercial contracts (e.g. uncapped liability, non-compete, exclusivity). |
| **MAUD** | maud.openlegaldata.net | M&A merger-agreement **deal points** (what's market-standard in deals). |
| **LEDGAR** | ledgar.openlegaldata.net | SEC contract **provisions** labelled by type (indemnification, governing law, ...). |
| **ACORD** | acord.openlegaldata.net | Clause retrieval set. |
| **ContractNLI** | contractnli.openlegaldata.net | NDA clauses + entailment (what an NDA does/does not permit). |

## How to use

**Parallel search across all clause corpora:**
```bash
python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" search "limitation of liability cap" --category contracts --limit 10
```
Results interleave the islands so you see how the same concept appears across
commercial contracts (CUAD), SEC filings (LEDGAR), M&A deals (MAUD), and NDAs
(ContractNLI). Each result's `heading` is the clause type/label; the body is the
actual language.

## Strategy
1. Identify the clause concept (indemnification, MAC, assignment, governing law...).
2. Parallel `/search --category contracts` for example language + which corpus treats it.
3. For **M&A market standards**, weight MAUD; for **SEC-filed contract provisions**,
   weight LEDGAR; for **general commercial clause types**, CUAD; for **NDAs**, ContractNLI.
4. Quote/adapt the example language — cite the source corpus, not as legal advice.

## Endpoints
- `GET /search?q=<terms>&limit=N` per island; `GET /` for info.
- Metadata per chunk (clause type, source) supports filtering.

```python
import os, sys; sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT","."), "skills/_lib"))
from legal_search import search
clauses = search("force majeure pandemic", category="contracts", limit=15)
```
