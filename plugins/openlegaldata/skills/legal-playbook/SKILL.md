---
name: legal-playbook
description: Build a negotiation PLAYBOOK for a contract the user is looking at, from our side, and place the contract's current wording on it (preferred / fallback / walk-away / missing). Use when the user shares or describes a contract and asks for a playbook, negotiation positions, "what should we push for", a markup strategy, or a gap review against market positions for their side. Not for finding example clause wording (use legal-contracts) or drafting a new document (use legal-drafting).
---

> **Calling the islands (works in any runtime).** Every endpoint below is an HTTPS
> **GET** on `playbook-bank.openlegaldata.net`. Call it with any fetch tool, or with
> `python "${CLAUDE_PLUGIN_ROOT:-.}/skills/_lib/legal_search.py" get "<url>"`, which adds the key.
> If the script is blocked (sandboxed runtimes), fetch the URL directly.
>
> **Honesty rule:** positions come only from what these endpoints return, each cited to its
> source playbook ids. If you cannot reach them, say so; do not present your own view as a
> playbook-bank result.
>
> **Access:** set `OPENLEGALDATA_API_KEY` (https://openlegaldata.net/account). Direct fetches take
> header `X-API-Key: <key>` or `?key=<key>`.

# Contract → playbook for our side

The playbook bank holds position ladders from real-world-style negotiation playbooks: for each
issue, our **preferred** ask, the **fallback** we accept, the **walk-away** limit and who must
approve (**escalation**), plus the counterparty's likely ask. Every rung cites the playbooks it
came from.

**Source caveat — say it once in your answer.** Today every playbook is from Harvey LAB
(synthetic, lawyer-reviewed, MIT). Coverage is strongest for SaaS / commercial, credit and
account control, employment, M&A and data-processing agreements, and thin elsewhere.

## Steps

1. **Classify the contract** from its title, recitals and headings: the document ("SaaS
   subscription agreement", "account control agreement", "executive employment agreement") and
   the clause families it contains (limitation of liability, indemnity, termination, …).
2. **Settle our side.** Propose it from the parties and the user's context ("we act for the
   customer; counterparty is the vendor") and **confirm with the user before step 3**. Sides
   are single words from the bank's vocabulary. See what exists:
   `GET https://playbook-bank.openlegaldata.net/facets` → `side` and `counterparty` values
   (customer, vendor, buyer, seller, lender, borrower, employer, licensor, licensee, tenant,
   landlord, controller, processor, …). If the user's side is not listed, say so and pick
   the nearest with their agreement (collateral agent ≈ lender).
3. **Assemble the playbook:**
   ```
   GET https://playbook-bank.openlegaldata.net/assemble?document=<document>&side=<side>&counterparty=<counterparty>
   ```
   Optional: `family=<clause-bank family key>`, `tier=`, `law=`, `appetite=conservative|standard|commercial`.
   - Default (fast) returns the **pile**: `issues[]`, each with the candidate positions from
     same-side playbooks and their source ids, plus `merge_instructions`. **Merge each issue
     yourself under those instructions** — one rung per ladder step, sources only from the
     pile, no numbers that no cited source has, no rung that favours the counterparty.
   - `&merge=1` merges server-side instead (slow: several minutes). Add `&format=md` for a
     ready Markdown playbook. Use `--timeout 600` with the script.
   - 404 = no same-side playbook for that document. Retry with a broader document name
     ("services agreement" for a niche SaaS form), or tell the user the bank has no playbook
     for this side.
4. **Place the contract on each issue.** For every assembled issue, find the contract's
   clause and classify it: **meets preferred**, **at fallback**, **at/below walk-away**
   (escalate), or **missing**. Quote the contract wording and the rung it matches. Flag
   contract clauses that no issue covers (the bank has no position — say so, don't invent one).
5. **Answer** with a table per issue: issue · contract says (quote) · where it sits · our
   preferred ask · fallback · walk-away · their likely ask · sources. Then the top 5 asks for
   the markup, most important first.

## Drill-downs
- `GET /playbook/<id>` — one source playbook with all its positions (to show a rung in context).
- `GET /positions?issue_id=<id>&side=<side>` or `?clause_family=<key>&side=<side>` — every
  position on one issue across playbooks.
- `GET /search?q=<terms>&f.side=<side>` — full-text search over positions.

## Rules
- Never present a rung without its source playbook ids.
- Assembled playbooks are a first draft for a lawyer, not advice; say so once.
- Clause wording from real contracts (to redraft a clause to the preferred position) comes
  from **legal-contracts** (CUAD, LEDGAR, …) — combine the two.
