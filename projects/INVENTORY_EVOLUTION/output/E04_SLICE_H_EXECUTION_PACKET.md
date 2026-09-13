# E04 Slice H Execution Packet — Component Search / Workspace / Provider Staging

## Status

`READY_AFTER_E04_A_TO_G`

## Entry gate

Requires core E04 identities, parametrics, evidence and approval relationships merged.

Branch:

```text
impl/e04-component-workspace
```

Migration:

```text
NONE expected for first UI/search slice
NEXT_CONTIGUOUS only if provider staging/diff tables are required
```

## Purpose

Give engineering/sourcing users one explainable workspace/search surface across:

```text
internal part
manufacturer + MPN
supplier + supplier SKU
aliases/barcode/QR
package
footprint
typed parametrics
lifecycle/evidence
AVL/substitute status
```

without copying stock/pricing truth or weakening approval controls.

## Search ranking

Priority:

1. exact internal material code;
2. exact manufacturer + MPN;
3. exact supplier SKU within supplier namespace;
4. exact alias/barcode/QR;
5. exact package/footprint;
6. structured typed parametric match;
7. fuzzy text/description.

Every result returns `match_reason` and identity namespace.

Identical MPN text under different manufacturers remains disambiguated.

Supplier SKU without supplier context may return ambiguous candidates rather than guessing.

## Approval/status badges

Search/workspace must visibly distinguish:

```text
APPROVED_MPN
UNAPPROVED_MANUFACTURER_PART
APPROVED_INTERNAL_SUBSTITUTE
CANDIDATE_ONLY
LIFECYCLE_WARNING
STALE_EVIDENCE
UNRESOLVED_SUPPLIER_PART
```

A parametric hit is never visually presented as approved by default.

## Component workspace

For one internal material aggregate by reference, not duplication:

```text
internal identity
approved/unapproved Manufacturer Parts
Supplier Parts
package/footprint
internal requirement attributes
Manufacturer Part source attributes
resources/datasheets/evidence
lifecycle/compliance
AVL/substitution relationships
E02 stock by warehouse/location
purchase history/source context
pricing context
future E05 where-used/revisions
```

Stock, pricing and purchase transactions remain owned by their existing domains.

Do not copy current stock/prices into component-master columns merely for convenience.

## Provider staging

Provider adapter may return candidates for:

- manufacturer/MPN;
- supplier source;
- package;
- typed attribute;
- lifecycle/compliance;
- datasheet/resource.

Safe lifecycle:

```text
provider result
 -> normalized candidate
 -> identity match/conflict check
 -> diff against canonical data
 -> reviewer accepts selected fields
 -> canonical command + evidence
```

Provider may not directly:

- approve AML/AVL;
- approve substitute;
- overwrite VERIFIED attributes;
- modify released BOM;
- create/submit PO;
- change stock.

If staging persistence is needed, use bounded provider-candidate/diff tables with source hash/provider/time/status; never store credentials in payload.

## Scan/deep-link integration

Extend E03 resolver/search so exact MPN/Supplier SKU/barcode may open the component workspace.

Scan resolution remains read/identity only; no approval or purchasing action is implied.

## Search analytics

Useful bounded metrics:

```text
zero-result rate
ambiguous-result rate
exact MPN hit rate
supplier-SKU unresolved rate
manual candidate accept/reject rate
stale-evidence count
```

Avoid indefinite retention of sensitive arbitrary query text without policy.

## Tests

1. exact internal part outranks all fuzzy matches;
2. exact MPN outranks description;
3. manufacturer namespace disambiguates same MPN text;
4. supplier SKU ambiguity requires namespace/review;
5. parametric candidate displays unapproved unless approval exists;
6. provider identity conflict cannot auto-merge;
7. provider value cannot overwrite VERIFIED canonical data without review;
8. workspace queries E02 stock/pricing domains rather than storing duplicate truth;
9. scan/deep link performs no approval/master-data mutation;
10. approval/lifecycle/evidence badges reflect actual canonical relations;
11. full Release Gate passes.

## Rollback

Disable workspace/provider staging UI while retaining canonical identities/evidence already accepted. No stock/transaction rollback.

## Stop conditions

Stop if search/provider score is used as approval authority, if provider refresh bypasses review, or if workspace starts becoming a copied second source for inventory/pricing.

## Exit / completion

Users can locate a component from common identifiers, understand its exact identities/source/approval/evidence, and safely review provider candidates. E04 is complete and E05 controlled revision/BOM work may begin.