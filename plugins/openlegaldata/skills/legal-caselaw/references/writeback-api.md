# Related-precedent write-back API (spec)

Extends the CourtListener island's existing **write-through D1 (index) + R2 (bodies)**
cache with a persistent **precedent-edge graph**. Discovery (`_lib/related_precedents.py`)
reads this graph first (cache hit) and writes derived edges back, so the graph — and the
treatment/good-law signal accumulated on it — improves with every run. This is the
home-grown citator the free sources don't provide.

Base: `https://courtlistener.openlegaldata.net`  ·  Auth: `X-API-Key` header (writes
require a key with `edges:write`; verification requires `edges:verify`).

## Edge object

A directed precedent relationship between two clusters.

```jsonc
{
  "id": "string",                 // stable; server hash of (fromCluster,toCluster,edgeType)
  "fromCluster": 4510032,         // seed cluster id
  "toCluster": 4625260,           // related cluster id
  "fromCite": "138 S. Ct. 2206",  // canonical reporter cites
  "toCite":   "442 U.S. 735",
  "edgeType": "authority|citing|co-citation",
      // authority  : from CITES to        (to is a foundation of from)
      // citing     : to CITES from        (to is later; it treats/applies from)
      // co-citation: from & to frequently cited together (sibling on an issue)
  "reliance": 3,                  // # times from's opinion cites to (authority strength)
  "treatment": "followed|applied|explained|distinguished|limited|criticized|questioned|declined_to_extend|superseded|abrogated|overruled|cited_neutral|unknown|null",
      // good-law signal; meaningful only for `citing` edges; null for authority/co-citation
  "treatmentQuote": "string|null",// verbatim passage supporting `treatment`
  "relevanceScore": 0.0,          // 0..1 ranking weight
  "confidence": 0.0,              // 0..1 classifier confidence (set by the LLM classifier)
  "provenance": "derived|auto_verified|human_verified",
  "status": "pending|verified|rejected",
  "method": "citation-parse|citing-search|co-citation",
  "discoveredBy": "string",       // run id / agent id
  "verifiedBy": "string|null",    // user id
  "discoveredAt": "ISO8601",
  "updatedAt": "ISO8601",
  "schemaVersion": 1
}
```

**Provenance precedence (conflict rule):** `human_verified > auto_verified > derived`.
A `derived` write MUST NOT overwrite the `treatment`/`status` of a `human_verified`
edge — it may only update non-authoritative fields (e.g. `relevanceScore`).

## Endpoints

### `POST /edges` — upsert a batch (discovery write-back)
Body: `{ "runId": "string", "edges": [Edge, ...] }`. Upsert key:
`(fromCluster, toCluster, edgeType)` — idempotent. New edges default `status:"pending"`,
`provenance:"derived"`. If a matching active auto-accept policy applies and
`confidence ≥ policy.minConfidence`, the server may set `auto_verified` (see HITL doc).
Returns `{ created, updated, autoVerified, ids: [...] }`.

### `GET /edges?cluster=<id>&direction=out|in|both&type=&minConfidence=&status=`
The discovery cache-read. Returns
`{ edges: [...], complete: bool, lastDiscoveredAt: ISO8601 }`. `complete:true` means a
prior full discovery ran for this seed → the client can skip live derivation.

### `GET /treatment?cluster=<id>` — aggregated good-law readout (the citator)
Rolls up all **verified** `citing` edges into a treatment summary:
```jsonc
{
  "cluster": 4510032,
  "isGoodLaw": true,            // true | false | "unknown"
  "worstTreatment": "distinguished",
  "overruledBy":   [{ "cluster": ..., "cite": ..., "date": ... }],
  "abrogatedBy":   [...],
  "distinguishedBy":[...],
  "counts": { "followed": 12, "distinguished": 3, "overruled": 0 },
  "asOf": "ISO8601"            // supports as-of-date queries via ?asOf=YYYY-MM-DD
}
```
`?asOf=` filters to edges whose citing case predates the date — powering the
"good law *as of* the conduct/trial date" reasoning the consuming system needs.

### `GET /edges/pending?type=&minConfidence=&highRiskOnly=&limit=` — HITL queue
Derived/auto edges awaiting human review, newest-or-riskiest first.

### `POST /edges/{id}/verify` — HITL action
Body: `{ "action": "approve|reject|reclassify", "treatment": "?", "note": "?", "userId": "..." }`.
`approve` → `status:verified, provenance:human_verified`. `reclassify` also sets
`treatment`. `reject` → `status:rejected` (kept for audit, never re-derived).

### `POST /policies` — auto-accept policy (the semi-autonomous gate)
Body:
```jsonc
{
  "name": "string",
  "predicate": { "edgeType": ["authority"], "minConfidence": 0.85,
                 "treatmentIn": ["followed","cited_neutral","distinguished"],
                 "courtRankMin": 3, "scope": { "issueArea": "fourth_amendment" } },
  "scope": "user|org", "createdBy": "userId", "enabled": true
}
```
Matching **derived** edges auto-verify on write. **High-risk treatments
(`overruled|abrogated|superseded`) can NEVER be covered by a policy** — they always
route to a human. Policies are listable (`GET /policies`), revocable
(`DELETE /policies/{id}`); revoking optionally re-queues edges it auto-verified.

## Invariants
- Idempotent upserts; `(fromCluster,toCluster,edgeType)` is the natural key.
- The verifier (LLM classifier) is never bypassed — auto-accept skips the *human*, not
  the machine refute-check.
- Every edge is auditable to a `human_verified` signature or a named policy.
- `treatment:"unknown"` is a legitimate terminal value — do not coerce to a guess.
