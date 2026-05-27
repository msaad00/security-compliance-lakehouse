# Framework Coverage Matrix

TrustOps tracks framework support as source-linked controls, evidence
requirements, versioned evaluation rules, and reviewed mappings. This page is
the detailed coverage ledger. The README and product visuals should link here
instead of repeating long caveats in the hero.

## Current Coverage

| Framework                     | Official source                                                                                                                                                                                     | Seeded controls | Reviewed mappings | Mapping coverage | Current scope                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------: | ----------------: | ---------------: | ----------------------------------------------------------------------------------------- |
| SOC 2 Trust Services Criteria | [AICPA & CIMA TSC](https://www.aicpa.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022)                                                                         |               2 |                 2 |             100% | security access and monitoring seed controls                                              |
| NIST AI RMF 1.0               | [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)                                                                                    |               6 |                 6 |             100% | AI governance, inventory, measurement, monitoring, and incident-response controls         |
| ISO/IEC 27001:2022            | [ISO/IEC 27001:2022](https://www.iso.org/standard/27001)                                                                                                                                            |               3 |                 3 |             100% | access, monitoring, and ICT readiness seed controls                                       |
| HIPAA Security Rule           | [HHS Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html), [45 CFR Part 164 Subpart C](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C) |               6 |                 6 |             100% | administrative and technical safeguards for ePHI evidence                                 |
| PCI DSS v4.0                  | [PCI SSC Document Library](https://www.pcisecuritystandards.org/document_library/?category=pcidss)                                                                                                  |               3 |                 3 |             100% | access, logging, and testing seed requirements                                            |
| GDPR 2016/679                 | [EUR-Lex Regulation 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj)                                                                                                                        |               6 |                 6 |             100% | security, processing records, breach notification, privacy design, processors, DPIA       |
| EU AI Act 2024/1689           | [EUR-Lex Regulation 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)                                                                                                                      |               6 |                 6 |             100% | high-risk AI risk management, data governance, logging, transparency, oversight, security |
| ISO/IEC 42001:2023            | [ISO/IEC 42001:2023](https://www.iso.org/standard/42001)                                                                                                                                            |               2 |                 2 |             100% | AI management-system risk treatment and operations seed controls                          |

## Readiness Gates

A framework tile is considered operationally trustworthy only when each gate is
true:

| Gate              | Evidence in repo                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| Source linked     | `frameworks/registry.json` has official source URL, version, effective date, and sync cadence    |
| Control modeled   | `controls/catalog.json` has control ID, owner, evidence requirement, frequency, and rule         |
| Mapping reviewed  | `mappings/control_articles.json` links each control to official article/requirement references   |
| Rule versioned    | `evaluation_rule` points to a linted controls-as-code rule in `src/security_lakehouse/policy.py` |
| Coverage guarded  | `tests/test_mappings.py` enforces coverage floors for public-source frameworks                   |
| Runtime evaluated | pipeline emits gold `control_posture.jsonl` with rule reasons and evidence counts                |

## Official Marks And Logos

Framework names and product marks are not the same thing as certification
badges. TrustOps does not bundle official marks unless usage rights are
documented in [Third-Party Asset Policy](THIRD_PARTY_ASSETS.md). Product
screens and README visuals should use neutral text labels for framework scope
unless an approved asset entry exists with source URL, permitted-use terms,
attribution, owner, and review date.

This avoids three risks:

- implying TrustOps or a demo company is certified when it is not
- embedding protected certification seals in an open-source repo
- creating lookalike logos that appear official but are not

## Expansion Roadmap

| Track                    | Next target                                                                              | Notes                                              |
| ------------------------ | ---------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Public-source frameworks | Increase NIST AI RMF, HIPAA, GDPR, and EU AI Act to 10+ controls each                    | Uses public official sources and reviewed mappings |
| Licensed frameworks      | Expand SOC 2, ISO, and PCI only from allowed identifiers and internal titles             | Do not reproduce licensed standard text            |
| Evidence requirements    | Add expected source types and freshness SLAs per control                                 | Feeds connector planning and confidence scoring    |
| Crosswalks               | Add reviewed shared-control mappings across frameworks                                   | Avoid heuristic-only equivalence claims            |
| UI                       | Show coverage percent, source freshness, and mapped-control count in the Frameworks page | Keep hero visuals clean; detailed truth lives here |
