# TASK_INV_IMPL_E04_S02 — Manufacturer and Manufacturer-Part Identity

## Status

`DESIGN_READY_BLOCKED_BY_E04_S01`

## Objective

Introduce canonical manufacturer + MPN identity without making existence equal approval.

## Suggested objects

```text
manufacturers
manufacturer_aliases
manufacturer_parts
```

### manufacturers

Required concepts:

```text
id
manufacturer_name
normalized_name
website
status
created_at
updated_at
```

### manufacturer_aliases

For spelling/search normalization only:

```text
manufacturer_id
alias_name
normalized_alias
source
```

Aliases do not merge two manufacturers automatically without review.

### manufacturer_parts

```text
id
manufacturer_id
mpn
normalized_mpn
package_id
lifecycle_status
status
created_at
updated_at
```

Canonical uniqueness:

```text
UNIQUE(manufacturer_id, normalized_mpn)
```

The same MPN text may exist under different manufacturers.

## MPN normalization

Normalization may support search equivalence such as case/whitespace/punctuation where safe, but canonical display MPN remains unchanged.

Do not apply one destructive normalization to every manufacturer.

Store:

```text
mpn            canonical/display
normalized_mpn comparison/search key
```

Manufacturer-specific normalization exceptions may be introduced only when justified by real data.

## Duplicate handling

When a candidate conflicts with an existing normalized identity:

- never silently merge;
- show both evidence/source records;
- require explicit master-data resolution;
- preserve old identifiers as aliases only after confirmation.

## Approval boundary

A `manufacturer_parts` row means:

```text
this manufacturer part identity exists
```

It does **not** mean:

```text
approved for internal material X
```

That authority belongs to E04-S06 AML/AVL relationships.

## Lifecycle

Manufacturer-part lifecycle field may carry current known state but must support evidence/provenance from E04-S07.

Unknown is a valid state. Do not guess `active` because a part appears in a catalogue.

## Tests

- manufacturer name normalized uniqueness rules deterministic;
- alias lookup finds canonical manufacturer without changing identity;
- same normalized MPN under same manufacturer rejected as duplicate;
- same MPN text under different manufacturers allowed;
- canonical display MPN preserved;
- existence does not make it approved for procurement/production;
- ambiguous legacy model import remains staging only.

## Acceptance

Manufacturer + MPN becomes a first-class exact identity usable by search, sourcing, AVL, BOM and lifecycle workflows without overloading `materials.model`.
