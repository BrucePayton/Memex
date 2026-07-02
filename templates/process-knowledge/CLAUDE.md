# {{TOPIC}} · Process Knowledge Project

> {{PURPOSE}}

## Dimension System

This process knowledge has four standard dimensions:

- **Organization (org)**: Roles, departments, owners, reporting relationships
- **Rules (rules)**: Business constraints, judgment conditions, threshold rules
- **Metrics (metrics)**: KPIs, SLAs, measurement methods
- **Concepts (concepts)**: Terminology definitions, business concepts, related concepts

## Business Steps

Create sub-folders under `wiki/steps/` for each business step.
Each step's `index.md` declares `upstream_steps` and `downstream_steps`:

```yaml
---
title: "Order Validation"
type: process-step
upstream_steps: ["Order Receipt"]
downstream_steps: ["Payment Verification", "Inventory Check"]
step_order: 2
---
```

## Page Types

In addition to the standard 5 types, this template adds 4 card types with category tags:

- `process-card` — Process flows, approval workflows, SOPs, after-sales procedures.
  Use `process_category`: `approval` | `operations` | `after-sales` | `maintenance`.
  Include `exception_handling` array for known failure scenarios (phenomenon/root_cause/handling).
  For approvals, add `approval_link` and `approval_form_fields`.

- `metric-card` — KPIs, metrics with graded thresholds.
  `thresholds` is an array of {level, range, risk, action}.

- `org-card` — Departments, suppliers, brands, vendors.
  Use `org_category`: `internal-dept` | `supplier` | `brand` | `vendor` | `service-provider`.
  For brands/suppliers, add `regional_contacts` (array of {region, person, phone, wechat}),
  `support_hotline`, `product_categories`, `brand_name`.

- `rule-card` — Business rules, warranty terms, compliance constraints.
  Use `rule_category`: `business-rule` | `warranty` | `compliance` | `operational`.
  For warranty rules, add `warranty_period`, `brand`, `product_category`,
  `claim_conditions`, `exclusion_conditions`, `support_contact`.

## Key Rules

1. `wiki/` only allows org/rules/metrics/concepts four dimensions + steps/ business steps
2. Business steps only allow four-dimension pages; no other dimensions allowed
3. Cards must have complete required fields; missing fields recorded in `missing_sections`
4. `raw/` is immutable; all knowledge bound via `[^src-*]` citations
5. Step dependencies declared via frontmatter; auto-construct step graph
6. Each card's required fields are validated on creation; missing fields produce `missing_sections` entries
