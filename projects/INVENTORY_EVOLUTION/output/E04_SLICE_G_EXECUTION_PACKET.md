# E04 Slice G Execution Packet — AML / AVL / Approved Substitutes

## Status

`READY_AFTER_E04_B_C_E_F`

## Entry gate

Requires exact Manufacturer Part identity, supplier source identity, typed parametrics/evidence and current-main Release Gate PASS.

Branch:

```text
impl/e04-avl-substitute
```

Migration:

```text
NEXT_CONTIGUOUS
= material_manufacturer_approvals + material_substitutions + indexes
```

## Purpose

Separate three concepts that must never collapse:

```text
Alias = search/name equivalence only
AML/AVL = Manufacturer Part approved for one Internal Material
Internal Substitute = one Internal Material approved to replace another
```

## AML / AVL schema

```text
material_manufacturer_approvals
  id
  material_id
  manufacturer_part_id
  approval_status
  approval_class
  qualification_reference
  valid_from NULL
  valid_to NULL
  approved_by NULL
  approved_at NULL
  suspended_by NULL
  suspended_at NULL
  suspended_reason NULL
  remark
  created_at
  updated_at
UNIQUE(material_id, manufacturer_part_id)
```

Suggested states:

```text
DRAFT
UNDER_REVIEW
APPROVED
SUSPENDED
REJECTED
EXPIRED
```

Eligibility requires APPROVED + effective dates + not suspended/expired.

Manufacturer Part existence, supplier availability and provider confidence do not change this rule.

## Internal substitution schema

```text
material_substitutions
  id
  source_material_id
  target_material_id
  substitution_class
  scope_type
  scope_id NULL
  condition_text
  approval_status
  valid_from NULL
  valid_to NULL
  priority
  engineering_reference
  approved_by NULL
  approved_at NULL
  created_at
  updated_at
```

Initial classes:

```text
FORM_FIT_FUNCTION
CONDITIONAL
PURCHASING_ONLY
ENGINEERING_DEVIATION
```

Substitution is directional:

```text
A -> B approved
!=
B -> A approved
```

## Scope boundary

E04 safely supports GLOBAL/internal-material-level approval.

Do not invent BOM revision / Work Order scope before E05/E06 identities exist.

Later E05/E06 may extend scope/effectivity with released revision/deviation/WO authority.

## Approval authority

Approval/suspension/rejection are consequential engineering master-data actions.

Use E01 Action Policy + explicit engineering/master-data permission. If existing permission model lacks a suitable narrow capability, add a separately reviewed permission migration rather than reusing generic `material.manage` for all approval authority.

Every decision records actor/time/evidence.

## Candidate discovery

Typed parametrics and provider search may generate:

```text
CANDIDATE_ONLY
```

with comparison evidence.

No candidate becomes approved via score/threshold alone.

RF review may compare frequency, gain, NF, P1dB/OIP3, supply/control, package/footprint, matching/calibration impact and conditions, but the human/approved workflow owns authority.

## Procurement integration contract

Preferred source path:

```text
Internal Material demand
 -> current AML/AVL approval
 -> exact Manufacturer Part
 -> enabled Supplier Part source
```

`Supplier Part.preferred = true` does not bypass AVL.

Commodity exception with internal-material-only source remains explicit and policy-controlled.

## Lifecycle interaction

NRND/EOL/shortage can create warning/review work later, but never auto-approves a replacement.

Suspension prevents future sourcing/production selection while preserving historical use evidence.

## Tests

1. alias cannot grant approval;
2. existing Manufacturer Part without AML is ineligible where approval required;
3. APPROVED effective relation is eligible;
4. suspended/expired relation blocked;
5. same MPN can be approved for one material and not another;
6. supplier preferred source cannot bypass AML;
7. parametric match cannot create approval;
8. A->B does not imply B->A;
9. approval/suspension history remains auditable;
10. BOM-scoped authority is not faked as global before E05;
11. full Release Gate passes.

## Rollback

Approval history remains. Feature use can be disabled but do not delete decisions/evidence.

## Stop conditions

Stop if procurement can select an unapproved MPN through supplier preference, or if candidate similarity creates substitute authority.

## Exit / unlock

Production/procurement can distinguish identity, approved Manufacturer Part and approved internal substitution with explicit effectivity/evidence. Unlocks E05 controlled BOM and E08 sourcing logic.