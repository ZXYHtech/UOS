# TASK_INV_IMPL_E04_S06 — AML / AVL Approval and Internal-part Substitutes

## Status

`DESIGN_READY_BLOCKED_BY_E04_S02_S03_S05`

## Objective

Introduce controlled engineering approval for manufacturer parts and internal-part substitutes without confusing aliases, search similarity, supplier availability or parametric resemblance with substitution authority.

## Three distinct concepts

```text
Alias
  search/name equivalence only

AML / approved manufacturer part
  manufacturer part approved to fulfil one internal material

Internal substitute
  different internal material approved to replace another under explicit conditions
```

These must remain separate tables/contracts.

## AML object

Suggested:

```text
material_manufacturer_approvals
  id
  material_id
  manufacturer_part_id
  approval_status
  approval_class
  qualification_reference
  valid_from
  valid_to
  approved_by
  approved_at
  suspended_by
  suspended_at
  suspended_reason
  remark
```

Suggested status:

```text
draft
under_review
approved
suspended
rejected
expired
```

## Eligibility rule

A manufacturer part is eligible only when:

- identity exists;
- approval status is approved;
- effectivity dates permit current use;
- it is not suspended/expired;
- relevant scope/policy permits it.

Supplier availability does not override this.

## Internal substitute object

Suggested:

```text
material_substitutions
  id
  source_material_id
  target_material_id
  substitution_class
  scope_type
  scope_id
  condition_text
  approval_status
  valid_from
  valid_to
  priority
  engineering_reference
  approved_by
  approved_at
```

Initial classes:

```text
form_fit_function
conditional
purchasing_only
engineering_deviation
```

## Directionality

Substitution is directional by default.

```text
A -> B approved
```

does not imply:

```text
B -> A approved
```

unless separately authorized.

## Scope

E04 may safely implement `global` engineering approval.

BOM-revision/work-order/deviation effectivity belongs primarily to E05/E06 and should be integrated when those authoritative entities exist.

Do not invent fake BOM revision IDs now.

## Candidate discovery

Parametric search can suggest possible candidates and show differences, but the command must label them clearly as:

```text
candidate only
not approved
```

until an engineering approval exists.

## RF comparison evidence

For RF components, approval review may compare:

- operating frequency;
- gain;
- NF;
- P1dB/OIP3;
- insertion loss/isolation;
- supply/control interface;
- temperature;
- package/footprint;
- matching/calibration/firmware impact.

A numeric threshold match alone is never sufficient authority.

## Lifecycle interaction

EOL/obsolete/supply shortage can create a review task but must not auto-approve or auto-replace.

## Procurement interaction

Procurement source selection uses:

```text
supplier part
 -> manufacturer part
 -> current AML approval
 -> internal material demand
```

When only an internal-material-only commodity source exists, the explicit commodity exception policy applies.

## Tests

- alias cannot grant AML/substitute eligibility;
- unapproved MPN blocked where approval required;
- suspended/expired approval blocked;
- same MPN can be approved for one internal part and not another;
- A->B does not imply B->A;
- parametric match alone cannot create approval;
- supplier preferred flag cannot bypass AML;
- approval/suspension history remains auditable;
- future BOM-scoped relationship cannot be faked as global approval.

## Acceptance

Production/procurement decisions can distinguish exact identity, approved source and engineering substitute, with explicit approval/effectivity evidence and no inference from aliases or similarity.
