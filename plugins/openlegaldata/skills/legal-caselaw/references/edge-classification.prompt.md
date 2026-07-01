# Edge classification & verification prompt

The automation behind the HITL gate. Run this on each **derived** precedent edge to
classify how one case treats another, ground it in verbatim text, score confidence, and
recommend `auto_verify` vs `needs_human`. It is **adversarial**: you must try to refute
a treatment before asserting it, and you must default to `unknown` rather than guess.

## Inputs (filled by the pipeline)

- `{{seedName}}` / `{{seedCite}}` — the seed case (the precedent being treated).
- `{{relatedName}}` / `{{relatedCite}}` — the other case on the edge.
- `{{edgeType}}` — `authority` (seed cites related) | `citing` (related cites seed) | `co-citation`.
- `{{passages}}` — the verbatim passage(s) from the **citing** opinion in which the seed
  is discussed (for `citing` edges), with pinpoints. For `authority` edges, the passage
  is from the seed opinion citing the related case.

## Your task

1. **Confirm the relationship is real.** Does `{{passages}}` actually show the stated
   `edgeType`? If the cite is incidental (a string-cite in a list, a "see also", an
   unrelated point), say so — relationship `incidental`.

2. **Classify treatment** (only for `citing` edges; for `authority`/`co-citation` set
   `treatment: null`). Choose exactly one, grounded in the passage:
   `followed | applied | explained | distinguished | limited | criticized | questioned |
   declined_to_extend | superseded | abrogated | overruled | cited_neutral | unknown`.

3. **Adversarial check (mandatory).** Before asserting any treatment — and *especially*
   `overruled / abrogated / superseded` (these kill good-law status) — argue the
   strongest case that it is WRONG:
   - Is the "overruling" language actually about a *different* holding of the seed?
   - Is it dictum, a dissent, or a lower court's prediction rather than a holding?
   - Does the citing court have authority over the seed (hierarchy/jurisdiction)?
   - Could it be merely `distinguished` (confined to its facts) rather than `overruled`?
   If you cannot defeat your own classification, it stands. If the refutation is at all
   plausible for a high-risk treatment, downgrade (e.g. `overruled` → `questioned`) or
   return `unknown`, and set `recommend: needs_human`.

4. **Extract the verbatim quote** that best supports the treatment (`treatmentQuote`),
   with its pinpoint. No quote you can point to → treatment is `unknown`.

5. **Score confidence** `0..1` and **recommend**:
   - `auto_verify` only if: relationship real, treatment grounded in a verbatim quote,
     adversarial check survived, **and treatment is NOT high-risk**.
   - `needs_human` otherwise — always for `overruled/abrogated/superseded`, for
     `unknown`, for `incidental`, or for confidence < 0.85.

## Honesty rules
- Use ONLY `{{passages}}` — do not import outside knowledge of how the case came out.
- `unknown` is a valid, often-correct answer. Never guess to fill the field.
- High-risk treatments are never your call to finalise — flag for a human.

## Output (strict JSON)

```json
{
  "relationshipReal": true,
  "edgeType": "citing",
  "treatment": "distinguished",
  "treatmentQuote": "We decline to extend Carpenter to ... (slip op., at 7).",
  "quotePinpoint": "slip op. at 7",
  "adversarialCheck": "Considered 'overruled' — rejected: the court confines Carpenter to 7+ days, it does not disturb the holding; this is distinguishing, not overruling.",
  "confidence": 0.88,
  "recommend": "auto_verify",
  "reasons": "Grounded verbatim; non-high-risk; survived refutation."
}
```

Return ONLY the JSON object.
