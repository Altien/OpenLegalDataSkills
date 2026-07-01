# Related-precedent HITL verification & classification workflow

How a *derived* edge becomes a *trusted* one. Discovery is cheap and high-recall but
loose; promotion to the citator graph is gated so that auto-derived treatment never
masquerades as authoritative. Semi-autonomous: a human approves a *class* once (a
policy), not every edge forever.

```
 discover()                 classify (LLM)              gate                    store
 ──────────         ───────────────────────────   ─────────────────────   ───────────────
 parse cites    →   edge-classification.prompt  →  policy match? ─yes─→    auto_verified
 + citing srch      (adversarial; treatment,      │  + conf ≥ thresh        (audit: policy id)
 = derived edges    quote, confidence, verdict)   │
 status=pending                                    └─no / high-risk ──→     pending  →  HITL
                                                                            queue       approve /
                                                                                        reclassify /
                                                                                        reject
                                                                                          │
                                                                            human_verified ↘
                                                                                          citator graph
                                                                            (GET /treatment, as-of-date)
```

## Stages

1. **Derive** (`related_precedents.py`) → edges with `provenance:derived`,
   `status:pending`, a cheap regex `treatment` pre-tag, `confidence:null`.
2. **Classify** — run `references/edge-classification.prompt.md` on each edge that needs
   a treatment call (the `citing` edges). It fetches the citing passage around the seed
   mention, classifies `treatment`, extracts the verbatim `treatmentQuote`, assigns
   `confidence`, and — adversarially — tries to *refute* the classification before
   asserting it. Output overwrites the pre-tag.
3. **Gate** (server, on `POST /edges`):
   - **High-risk treatment** (`overruled | abrogated | superseded`) → **always
     `pending` → human.** Killing a precedent's good-law status is never automated.
   - **Policy match** + `confidence ≥ policy.minConfidence` → `auto_verified`
     (audit-tagged with the policy id).
   - Otherwise → `pending` → HITL queue.
4. **Review** — a human works `GET /edges/pending` (riskiest first):
   `approve | reclassify | reject` via `POST /edges/{id}/verify`. On approve/reclassify
   the edge becomes `human_verified` and enters the citator graph.
5. **Learn** — when approving, the reviewer may **"accept all like this"** → the server
   generalises the edge into a candidate **auto-accept policy** (predicate over
   `edgeType / treatment / courtRankMin / minConfidence / issueArea`), shows the
   plain-English description + a dry-run preview of what it would capture, and stores it
   on explicit confirm (scope: `user` or `org`). Future like edges auto-verify.

## Rules (non-negotiable)
- **Verifier is never skipped.** Auto-accept removes the *human* sign-off for a
  described class; the LLM refute-check still runs on every edge.
- **High-risk is human-only**, no policy can cover it.
- **`unknown` is allowed.** If the classifier cannot ground a treatment in the text, it
  returns `unknown` — never a guess. The consuming legal-reasoning system treats
  `unknown` as a surfaced open question, not a value.
- **Everything is auditable** to a human signature or a named policy, and revocable
  (revoking a policy can re-queue what it auto-verified).
- **Provenance precedence**: a later `derived` run never overwrites a `human_verified`
  treatment.

## Confidence → action (default thresholds; tune per org policy)
| confidence | non-high-risk treatment | high-risk treatment |
|---|---|---|
| ≥ 0.85 + policy | auto_verified | **pending (human)** |
| 0.6 – 0.85 | pending (human) | pending (human) |
| < 0.6 | pending (human), flagged low-confidence | pending (human) |
