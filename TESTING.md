# Testing the OpenLegalData skills (Claude Code)

Follow top to bottom in a **fresh Claude Code session**. Each step says what to run
and what counts as a pass. Fill in the results table at the end.

Plugin version under test: **v0.1.5**.

---

## 1. Install
In the Claude Code prompt:
```
/plugin marketplace add Altien/OpenLegalDataSkills
/plugin install openlegaldata@openlegaldata
```
If you've added the marketplace before, refresh first: `/plugin marketplace update openlegaldata`.

**Pass:** install reports success, no errors.

## 2. Confirm the 5 skills registered
```
/plugin
```
**Pass:** under `openlegaldata` you see `legal-caselaw`, `legal-citations`,
`legal-contracts`, `legal-statutes`, `legal-world`.

## 3. Data-plane smoke (deterministic — isolates network/API from skill activation)
Run in the Claude Code terminal:
```bash
SEARCH=$(find ~/.claude -name legal_search.py 2>/dev/null | head -1); echo "$SEARCH"
python "$SEARCH" verify "347 U.S. 483"
python "$SEARCH" verify "999 U.S. 9999"
python "$SEARCH" leading "qualified immunity" --limit 6
python "$SEARCH" search "limitation of liability" --category contracts --limit 5
python "$SEARCH" search "clean air emissions" --category statutes --limit 5
python "$SEARCH" search "Datenschutz" --islands https://de.openlegaldata.net --limit 3
```
**Pass:**
- `347 U.S. 483` → `"status": "ok"`, **Brown v. Board of Education**
- `999 U.S. 9999` → `"status": "not_found"`
- `leading "qualified immunity"` → most-cited cases incl. **Harlow v. Fitzgerald**, with `citeCount`
- contracts → 5 hits tagged across **contractnli / maud / cuad ("Cap On Liability") / ledgar / acord**
- statutes → hits incl **`42 U.S.C. § 7651`** plus fedreg/us-ga/eurlex/bills
- `Datenschutz` → results all tagged `"_island": "de"` (German)

> If instead you get a JSON block with `"_network": "blocked"` + a `fetch` URL list,
> this runtime has no egress — note it; in Claude Code that shouldn't happen.

## 4. Skill activation (type each as a normal message)
| # | Prompt | Should fire | Pass condition |
|---|---|---|---|
| 4a | Verify the citation 467 U.S. 837 — what case is it? | `legal-citations` | **Chevron v. NRDC** (1984), and it says it used the skill/endpoint |
| 4b | Find leading US cases on qualified immunity and summarize the top one. | `legal-caselaw` | uses `leading` → most-cited cases (Harlow etc.); reads top opinion from CAP |
| 4c | How is a limitation-of-liability cap usually worded in commercial contracts? | `legal-contracts` | example clause language (CUAD/LEDGAR), not case law |
| 4d | What does US federal law say about clean-air emissions? | `legal-statutes` | USC/eCFR section hits |
| 4e | What does German law say about Datenschutz? | `legal-world` | German results from the `de` island |

**Key assertion:** 4b and 4c route to **different** skills (case law ≠ contracts).
Also watch that the answer comes **from the islands**, not a generic web search.

## 5. Negative / scoping
- "Verify 999 U.S. 9999" → `legal-citations` returns **not_found** (no invented hit).
- "What's the weather today?" → **no** legal skill activates.

## 6. (Optional) self-diagnosis check
```bash
python "$SEARCH" search "test" --islands https://blocked.invalid.openlegaldata.test
```
**Pass:** prints `"_network": "blocked"` with a `fetch` URL and the "do not substitute
a general web search" note (proves the skill fails honestly, not silently).

## 7. Cleanup (optional)
```
/plugin uninstall openlegaldata@openlegaldata
```

---

## Caveats while testing
- `legal-caselaw` / `legal-citations` hit **CourtListener live** (~5/min limit) — space out reruns.
- **CAP is still indexing** (full-text coverage growing); citation verify is unaffected (falls back to CourtListener for all years).

## Results — fill in
| Step | Pass/Fail | Notes |
|---|---|---|
| 1 install | | |
| 2 registered | | |
| 3 smoke (5) | | |
| 4a citations | | |
| 4b caselaw | | |
| 4c contracts | | |
| 4d statutes | | |
| 4e world | | |
| 5 negative | | |
| 6 self-diagnosis | | |
