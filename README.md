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

## Commercial licence

Version 1.0.0 and later are proprietary software owned by Altien Limited. Installing
or using the skills requires an active OpenLegalData subscription and acceptance of
the [Altien OpenLegalData Commercial Software Licence](plugins/openlegaldata/LICENSE)
and [Hosted Service Terms](terms.html). Earlier versions remain governed by the
licence supplied with those versions.

> Generated. **Do not edit here** — develop and test in
> [OpenLegalDataDev](https://github.com/Altien/OpenLegalDataDev), then run
> `scripts/publish-skills.sh`. Version: 1.0.0.
