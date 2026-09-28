---
name: legal-drafting
description: Draft a NEW legal document (engagement letter, board resolution, legal opinion, officer's certificate, complaint, discovery requests, term sheet, memo, letter, agreement …) from the facts and evidence in a matter, shaped by document blueprints (customary sections and order) and real example documents (exemplars). Also answers "what documents does this kind of matter need next". Use when the user asks to draft, prepare or produce a document. Not for clause-wording lookups alone (legal-contracts) or negotiation positions (legal-playbook).
---

> **Calling the islands (works in any runtime).** Every endpoint below is an HTTPS **GET**.
> Call it with any fetch tool, or with
> `python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" get "<url>"`, which adds the key.
> If the script is blocked (sandboxed runtimes), fetch the URL directly.
>
> **Honesty rule:** structure and example wording come only from what these endpoints return;
> the facts come only from the user's matter. If you cannot reach the islands, say so.
>
> **Access:** set `OPENLEGALDATA_API_KEY` (https://openlegaldata.net/account). Direct fetches take
> header `X-API-Key: <key>` or `?key=<key>`.

# Matter evidence → new document

| Island | What it gives you |
|---|---|
| **blueprint-bank.openlegaldata.net** | **Document blueprints**: the customary and optional sections of a document type, in canonical order, with how often each appears, where and how long. **Matter blueprints**: a matter type's folders, phases, milestones and the documents each phase produces. |
| **exemplar-bank.openlegaldata.net** | 12.5k whole example documents (memos, letters, agreements, opinions, certificates, pleadings, emails …) to model tone, structure and wording on. |
| **playbook-bank** / **legal-contracts** | Positions for our side (legal-playbook) and real clause wording (CUAD, LEDGAR …) for agreements. |

**Source caveat — say it once.** The blueprints and exemplars are built from Harvey LAB
(synthetic, lawyer-reviewed, MIT): the exemplars are illustrative, labelled `synthetic`, never
real precedent. Blueprints show what is customary in that corpus.

## Steps

1. **Gather the matter facts** the document needs from the user's files and messages: parties
   and roles, dates, amounts, governing law, what happened, what is being asked. List any gap
   and ask for it (or leave a bracketed placeholder `[●]`) — never invent a fact.
2. **Get the blueprint** for the document type:
   ```
   GET https://blueprint-bank.openlegaldata.net/blueprint?doc_type=<type>[&kind=<kind>][&practice_area=<area>]&format=md
   ```
   - `doc_type`: engagement_letter, legal_opinion, resolution, board_minutes, certificate,
     pleading, discovery, term_sheet, notice, expert_report, offering_document, policy, plan,
     regulatory_filing, statement, arbitration_document, estate_document,
     constitutional_document, disclosure_schedule (live list: `GET /facets` → `doc_type`).
   - `kind` narrows a type: complaint, answer, motion, brief (pleading); officer_s_certificate,
     good_standing_certificate, charter, firpta_certificate, solvency_certificate
     (certificate); discovery_requests, subpoena; term_sheet, letter_of_intent;
     litigation_hold_notice; registration_statement_prospectus, offering_memorandum.
   - It falls back kind → practice area → type. `404 no blueprint` = the type is not
     formulaic enough to have one (memos, letters, agreements): skip to step 3 and take the
     structure from the exemplars.
3. **Read 2–3 exemplars** of the same type:
   ```
   GET https://exemplar-bank.openlegaldata.net/search?q=<topic terms>&f.doc_type=<type>&limit=10
   GET https://exemplar-bank.openlegaldata.net/doc/<documentId>
   ```
   Useful filters: `f.practice_area=`, `f.is_template=True`, `f.governing_law=`. Exemplar types
   include memo, agreement, letter, email, pleading, court_decision, playbook, certificate,
   report, engagement_letter, term_sheet, form, resolution, legal_opinion (`GET /facets`).
   Hits are per chunk, so dedupe on `documentId`.
4. **Draft.** Use the blueprint's sections in its order: every **customary** section, and an
   **optional** one only where the matter calls for it. Model tone and phrasing on the
   exemplars but write for this matter — do not copy an exemplar's facts, names or numbers.
   For agreement clauses, take wording from legal-contracts and positions from legal-playbook.
5. **Report coverage** after the draft: a short table of blueprint sections → included /
   omitted (why) / placeholder, the exemplar ids you modelled on, and the open `[●]` facts.

## What should this matter produce next?
```
GET https://blueprint-bank.openlegaldata.net/matter-blueprint?type=<matter type>&format=md
```
Matter types are practice areas or sub-practices ("M&A Buy-Side", "Commercial Litigation",
"Privacy & Data Security", … — `GET /facets` → `matter_type`). The blueprint lists folders,
phases with their milestones, and the documents each phase typically produces; compare with
what the matter already holds and propose the next documents.

## Rules
- Facts only from the matter; placeholders for gaps.
- Cite the blueprint id and exemplar ids you used; exemplars are synthetic examples.
- The draft is a first draft for a lawyer to review; say so once.
