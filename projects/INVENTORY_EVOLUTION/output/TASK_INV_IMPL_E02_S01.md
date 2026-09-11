# TASK_INV_IMPL_E02_S01 — Canonical Stock Identity & Quantity/UOM Contract

## Status

`DESIGN_READY_BLOCKED_BY_E02_ENTRY_GATE`

## Objective

Define the exact dimensions that identify a stock position before introducing the movement ledger or reservations.

This story exists to prevent the current ambiguity where `location_id` is stored on a balance row but is not part of its unique identity and nullable `platform_account_id` weakens uniqueness.

## Current baseline problem

Current `inventory` uniqueness:

```text
UNIQUE(material_id, warehouse_id, platform_account_id)
```

Current row also contains:

```text
location_id
quantity_available
quantity_locked
quantity_on_transfer
safety_stock
```

Problems:

1. same material cannot naturally hold independent balances in multiple bins under one warehouse/account;
2. nullable account scope allows duplicate logical “no account” rows under SQL NULL uniqueness semantics;
3. stock status is not a first-class identity dimension;
4. integer-only assumptions will not fit every future electronics material/UOM.

## Canonical position dimensions

E02 v1 position identity should be conceptually:

```text
material_id
+ warehouse_id
+ location_scope
+ owner/account_scope
+ stock_status
```

Lot/serial are deliberately not authoritative E02 v1 dimensions yet; E07 will add traceability without inventing legacy history.

## Normalized optional dimensions

Do not depend on NULL equality for uniqueness.

Choose and document one deterministic strategy, such as:

```text
owner_scope_type + owner_scope_id_normalized
location_scope_type + location_scope_id_normalized
```

or a canonical `position_key` derived from validated dimensions.

Example conceptual key:

```text
material:123|warehouse:4|location:unassigned|owner:company|status:available
```

The key is not a security boundary; it is a stable identity/projection key.

## Legacy unassigned location

If historical stock has no trustworthy bin/location, represent it explicitly as **unassigned/legacy aggregate scope**.

Do not invent a physical rack/bin name.

E03 may later move stock from unassigned/staging into real bin identities through explicit movements/count reconciliation.

## Owner/account scope

Clarify whether current `platform_account_id` represents physical ownership, reservation/publication scope, or only marketplace reporting.

Physical stock must not be fragmented by channel account unless business reality requires ownership separation.

If platform account is only a commercial publication dimension, migrate it out of physical position identity and retain it in channel ATP/publication logic later.

This decision must be made from current business usage before schema finalization.

## Minimal stock status vocabulary

E02 v1 should use a small controlled set, e.g.:

```text
available
hold
```

Only if current operations require it.

Do not prematurely introduce a large quality taxonomy; E07 owns quarantine/reject/inspection genealogy.

ATP eligibility for each status must be explicit.

## Quantity representation

Define an application-level decimal quantity type/policy for new authoritative stock math.

Requirements:

- deterministic serialization;
- no binary-floating accumulation as authoritative truth;
- explicit UOM code;
- defined precision/rounding by UOM family;
- existing integer piece quantities remain exactly representable.

Suggested first UOM categories:

```text
EA / piece
LENGTH
MASS
VOLUME
```

Do not create a full unit-conversion ERP in this story.

## Schema output

S01 may create reference/identity tables or helpers needed by later E02 stories, but must not make them production-authoritative yet.

Possible additive objects:

```text
stock_position_definitions / stock_position_keys
stock_uoms / unit policy metadata (only if needed)
```

Alternatively, S01 can be code-contract-only if S02/S03 own the concrete ledger/balance tables.

## Migration / legacy mapping report

Create a deterministic report over current `inventory` rows showing:

```text
legacy inventory row id
material
warehouse
platform account
location
proposed normalized position identity
ambiguity flags
```

Block later cutover if:

- duplicate legacy rows collapse to one proposed identity with conflicting quantities;
- location belongs to the wrong warehouse;
- material/warehouse references are invalid;
- owner/account semantics cannot be resolved safely.

## Tests

- same dimensions produce exactly one canonical key;
- null/unassigned dimensions normalize deterministically;
- two real locations produce different position identity;
- no-account rows cannot bypass uniqueness through NULL semantics;
- invalid cross-warehouse location is rejected;
- decimal quantity serialization round-trips exactly;
- piece quantity stays integer-exact;
- unsupported UOM/precision is rejected;
- legacy mapping report is deterministic;
- no legacy row is silently dropped/merged.

## Rollback

Pure/additive identity work. No production balance ownership changes in S01.

## Acceptance

S01 is complete when the team can answer “what exact dimensions identify one stock balance?” with a schema/testable contract and can map every current legacy inventory row to that identity or an explicit review exception.

## Dependencies

E02 master entry gate; E01 common primitives.

## Non-goals

- no reservations yet;
- no stock posting yet;
- no lot/serial;
- no advanced bins/putaway;
- no channel ATP publication.