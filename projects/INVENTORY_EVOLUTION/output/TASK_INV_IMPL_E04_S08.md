# TASK_INV_IMPL_E04_S08 — Component Search, Workspace and Provider-enrichment Boundary

## Status

`DESIGN_READY_BLOCKED_BY_E04_CORE_IDENTITY`

## Objective

Give users one engineering component workspace and one explainable search surface across internal part, MPN, supplier source, package, footprint, aliases and parametric filters without allowing search/provider confidence to mutate master data or approve substitutions.

## Search scope

Exact/structured search should cover:

```text
internal material code
manufacturer + MPN
manufacturer alias
supplier + supplier SKU
legacy material alias
barcode / QR
package
footprint
selected typed parametric attributes
lifecycle / approval state filters
```

Channel SKU remains searchable through existing platform mappings but is clearly labeled as a sales/channel identity.

## Search ranking

Priority should favor exact identity over fuzzy text:

1. exact internal part number;
2. exact manufacturer + MPN;
3. exact supplier SKU within supplier namespace;
4. exact alias/barcode/QR;
5. structured parametric match;
6. fuzzy description/text.

Every result explains why it matched.

## Parametric search safety

Parametric filters return candidates, not substitutions.

Example:

```text
frequency covers 1.6 GHz
NF <= 1.0 dB
package = QFN...
```

Result badges must distinguish:

```text
approved MPN
unapproved candidate
approved internal substitute
candidate only
lifecycle warning
stale evidence
```

## Component workspace

One internal material workspace should aggregate:

```text
internal identity
approved/unapproved manufacturer parts
supplier sources
package / footprint
parametric requirement values
manufacturer-part source values
resources / datasheets
lifecycle / compliance evidence
AVL / substitute relationships
stock by warehouse/location
recent purchase/pricing context
future where-used / BOM revision links
```

Do not duplicate stock/pricing truth; query those domains.

## Provider boundary

External provider adapter may:

- search catalogues;
- return candidate manufacturer/MPN/supplier/package/parameter/document data;
- attach provenance and raw payload;
- stage diffs against canonical data.

It may not directly:

- create an approved AML relation;
- approve an internal substitute;
- overwrite verified parametric data;
- change lifecycle without evidence/review policy;
- modify BOM;
- create PO;
- place autonomous orders.

## Import/staging

Suggested staging lifecycle:

```text
provider result
 -> normalized candidate
 -> identity match / conflict check
 -> diff against canonical record
 -> reviewer accepts selected fields
 -> canonical update + evidence
```

Ambiguous identity blocks merge.

## Deep links / scan integration

E03 scan/global resolver should be extended so exact MPN/supplier SKU/barcode can deep-link to this workspace.

Scan still identifies; it does not approve or purchase.

## Search analytics

Track safe operational metrics:

- zero-result rate;
- ambiguous-result rate;
- exact MPN hit rate;
- supplier-SKU unresolved rate;
- manual identity merge/reject rate;
- stale-evidence count.

Do not retain arbitrary sensitive query text indefinitely without retention policy.

## Tests

- exact MPN outranks fuzzy description;
- manufacturer namespace disambiguates identical MPN text;
- supplier SKU requires supplier namespace/context where ambiguous;
- parameter candidate marked unapproved unless AVL/substitute relation exists;
- provider identity conflict cannot auto-merge;
- provider value cannot overwrite verified canonical value without review path;
- workspace reads stock/pricing rather than copying authoritative values;
- scan/deep link performs no approval/master-data mutation.

## Acceptance

Engineering and sourcing users can find and understand a component from any common identifier, compare approved and candidate sources with evidence, and review provider suggestions without weakening identity or engineering approval controls.
