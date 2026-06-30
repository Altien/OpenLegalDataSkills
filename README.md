# OpenLegalData Skills

Installable Claude skills for legal research over [OpenLegalData](https://openlegaldata.net)
(70+ public datasets as independent search APIs). **Install from this repo:**

```
/plugin marketplace add Altien/OpenLegalDataSkills
/plugin install openlegaldata@openlegaldata
```

| Skill | Use it for |
|---|---|
| `legal-caselaw` | Researching US case law / precedent; reading opinions. |
| `legal-citations` | Verifying / resolving a citation. |
| `legal-contracts` | Clause language & deal-point reference (drafting). |
| `legal-statutes` | US/EU statutes & regulations. |
| `legal-world` | Foreign / comparative law (~55 jurisdictions). |

Skills share `skills/_lib/legal_search.py` — a parallel multi-island search utility
(stdlib Python; needs outbound HTTPS to `*.openlegaldata.net`).

> Generated. **Do not edit here** — develop and test in
> [OpenLegalDataDev](https://github.com/Altien/OpenLegalDataDev), then run
> `scripts/publish-skills.sh`. Version: 0.3.0.
