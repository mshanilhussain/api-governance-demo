\# API Governance Demo



\## Overview



This project demonstrates a lightweight, vendor-neutral API governance workflow using OpenAPI specifications, Postman, GitHub, and GitHub Actions.



The objective is to apply API design standards, maintain a governance catalogue, and validate publication approval metadata through automated checks.



\## Architecture



1\. \*\*API specification:\*\* OpenAPI definitions are maintained in the Git repository.

2\. \*\*Governance catalogue:\*\* `governance/catalogue.json` records API ownership, business domain, specification path, lifecycle status, dependencies, and Postman specification reference.

3\. \*\*Design-time policy enforcement:\*\* Postman specification linting runs in GitHub Actions to validate API specifications against configured governance rules.

4\. \*\*Lifecycle metadata validation:\*\* `scripts/validate-governance.py` checks catalogue completeness, lifecycle values, specification paths, dependencies, and publication approval metadata.

5\. \*\*Pull-request governance:\*\* Changes are reviewed through pull requests, with automated checks providing evidence of successful validation or policy rejection.

6\. \*\*API management integration:\*\* Layer7 API Management is a potential runtime enforcement and API publication integration point. A live Layer7 integration is outside the scope of this demonstration.



\## Repository Components



| Path | Purpose |

|---|---|

| `specs/` | OpenAPI specifications |

| `templates/` | Reusable API specification template |

| `scripts/create-api.sh` | Creates an API specification from the template |

| `scripts/validate-governance.py` | Validates governance catalogue rules |

| `governance/catalogue.json` | API governance catalogue |

| `.postman/api-mappings.yaml` | Maps API names to Postman specification IDs |

| `.github/workflows/api-governance.yml` | Automates governance validation and Postman operations |



\## Governance Lifecycle



The catalogue supports these lifecycle labels:



`Draft → Review → Approved → Published → Deprecated`



The current implementation validates lifecycle labels and requires a Published API to have `approval\_status: Approved`, an `approved\_by` value, and an `approval\_reference`.



These fields are demonstration metadata. The current validator does not authenticate approvers, enforce role-based access control, or validate every lifecycle transition.



\## Demonstration



\### 1. Successful validation



Run:



```bash

python scripts/validate-governance.py

```



Expected result:



```text

GOVERNANCE VALIDATION PASSED

Validated 1 API(s).

```



\### 2. Rejected publication



Temporarily set the Customer API's `approval\_status` to `Pending` while its lifecycle remains `Published`.



Run:



```bash

python scripts/validate-governance.py

```



Expected result: `GOVERNANCE VALIDATION FAILED`, with a message that publication is blocked because approval must be `Approved`.



Restore the approval status to `Approved` after the test.



\### 3. Automated API design validation



Open a pull request that changes an API specification. Review the GitHub Actions result to see whether the configured Postman governance rules pass or reject the change.



The demonstration also retains an intentionally failing pull request that introduces an HTTP security violation. Keep that change unmerged as evidence of policy enforcement.



\## Scope and Limitations



This is a governance prototype, not a complete enterprise governance control plane. It demonstrates catalogue metadata, design-time policy validation, and a basic publication approval metadata gate.



It does not yet implement a dedicated governance API or UI, authenticated approval workflows, full lifecycle transition enforcement, dependency analysis beyond catalogue references, runtime service discovery, or a live Layer7 integration.



