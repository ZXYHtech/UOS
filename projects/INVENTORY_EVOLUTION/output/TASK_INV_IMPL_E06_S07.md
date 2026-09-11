# TASK_INV_IMPL_E06_S07 — Controlled Work-order Substitution

## Status

`DESIGN_READY_BLOCKED_BY_E04_E05_E06_REQUIREMENTS`

## Objective

Allow production to use an approved alternate when authorized while preserving the original MBOM requirement, actual issued material and exact approval/deviation authority used.

## Principle

A work-order substitution never edits the released MBOM in place.

The WO requirement remains:

```text
required_material_id = original released MBOM material
```

Actual execution may additionally record:

```text
actual_material_id
substitution_authority_type
substitution_authority_id
approved_quantity/scope
actual_issued_quantity
```

## Accepted authority

Possible sources:

```text
E04 global approved internal substitute
E04 approved manufacturer-part/AML source where internal material remains same
E05 active engineering deviation/waiver
future E05 BOM-revision-scoped substitute authority
```

The system must validate scope/effectivity at issue time.

## Candidate vs authority

The following are **not authority**:

- similar parameter values;
- same package;
- supplier recommendation;
- available stock;
- alias match;
- AI/provider confidence;
- operator preference.

They may propose a candidate only.

## Reservation transition

If substitution changes internal material demand:

```text
release/move unused original reservation
 -> create substitute-material reservation
 -> preserve original requirement identity
 -> link substitute reservation to same requirement + authority
```

Do this atomically where possible.

No substitute issue is allowed while both original and substitute reservations incorrectly claim the same requirement quantity.

## Partial substitution

Allow controlled quantity split when authority permits:

```text
requirement 100 A
 -> issue 60 A
 -> approved substitute 40 B
```

Track actual quantities separately.

## Manufacturer-part choice within same internal material

When E04 AML allows multiple MPNs under one internal material, E06 records actual MPN/lot later through E07 genealogy where trace policy requires it.

This is different from substituting internal material A with B.

## Deviation limits

For E05 deviation/waiver validate:

- active status;
- product/BOM/WO scope;
- quantity limit if defined;
- date/effectivity;
- approved target material/configuration.

Consuming the allowed quantity must not exceed authority.

## Audit

Every substitute decision should answer:

```text
what MBOM required?
what was actually used?
why was it allowed?
who approved?
when?
how much?
```

## Tests

- similar unapproved part blocked;
- alias cannot authorize substitute;
- valid global substitute allowed;
- expired/suspended approval blocked;
- deviation scope/quantity enforced;
- A->B authority does not imply B->A;
- partial original/substitute issue aggregates correctly;
- reservation does not double-count original + substitute;
- later approval change does not rewrite historical WO execution;
- actual substitute remains linked to original requirement.

## Acceptance

Production can use authorized alternates without modifying engineering history, and every actual replacement remains explainable against the original released requirement and approval evidence.
