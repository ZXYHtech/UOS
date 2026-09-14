> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E04 Slice B Execution Packet — Manufacturer + MPN Identity

## Status

`READY_AFTER_E04_A`

## Entry gate

Requires E04-A internal-part contract merged and current-main Release Gate PASS.

Branch:

```text
impl/e04-manufacturer-mpn
```

Migration:

```text
NEXT_CONTIGUOUS
= manufacturers + manufacturer_aliases + manufacturer_parts + indexes
```

## Purpose

Create exact Manufacturer+MPN identity without conflating identity with approval.

```text
Manufacturer Part exists
!=
Manufacturer Part approved for internal material
```

Approval belongs to E04-G AML/AVL.

## Schema contract

### manufacturers

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

```text
id
manufacturer_id
alias_name
normalized_alias
source
created_at
```

Alias is search/normalization evidence, not an automatic merge rule.

### manufacturer_parts

```text
id
manufacturer_id
mpn
normalized_mpn
package_id NULL
lifecycle_status
status
created_at
updated_at
UNIQUE(manufacturer_id, normalized_mpn)
```

The same MPN text is allowed under different manufacturers.

## Normalization

Store both:

```text
mpn = canonical display/orderable identifier
normalized_mpn = deterministic comparison/search key
```

Normalization may safely handle case/outer whitespace and explicitly approved punctuation rules, but must not destroy meaningful orderable suffix/package distinctions.

Manufacturer-specific exceptions require tests/evidence; do not invent a universal aggressive normalizer.

Manufacturer name normalization similarly supports lookup while preserving canonical display name.

## Duplicate handling

A candidate collision never silently merges records.

Conflict output should show:

```text
existing manufacturer/manufacturer_part
candidate source
canonical + normalized values
source/evidence
recommended review action
```

Master-data review decides whether to attach alias, reject candidate, or create a distinct exact identity.

## Legacy import boundary

E04-A audit candidates from `materials.model/spec/name` may be staged for review.

No bulk canonical MPN creation from ambiguous legacy text.

A staged candidate only becomes a `manufacturer_parts` row after deterministic exact evidence or explicit review.

## Lifecycle boundary

`lifecycle_status` may initially be:

```text
UNKNOWN
ACTIVE
NRND
EOL
OBSOLETE
```

but the source/effective evidence is not trusted until E04-F provenance is implemented. `UNKNOWN` is preferred over guessing ACTIVE.

## Expected code touchpoints

Suggested domain modules:

```text
inventory_app/domains/components/manufacturers.py
inventory_app/domains/components/manufacturer_parts.py
```

Material CRUD may display/link manufacturer-part candidates later but does not replace internal part identity.

## Tests

1. same manufacturer + normalized MPN cannot duplicate;
2. same MPN text under different manufacturers is allowed;
3. canonical display MPN preserved;
4. normalization does not collapse meaningful suffix distinctions in fixtures;
5. manufacturer alias resolves canonical manufacturer but does not merge another manufacturer automatically;
6. ambiguous legacy model remains staging/review only;
7. newly created manufacturer part has no procurement/engineering approval by default;
8. UNKNOWN lifecycle remains valid;
9. migration repeat/no-op + integrity checks pass;
10. full Release Gate passes.

## Rollback

Additive identity tables can remain inert if feature is disabled. Do not delete manufacturer-part identities that have gained downstream references.

## Stop conditions

Stop if:

- normalization merges two real orderable MPNs;
- existence is treated as AVL approval;
- canonical MPN/display source is overwritten by provider normalization;
- legacy `model` rows are mass-converted without review evidence.

## Exit / unlock

Exact manufacturer-part identity exists independently from internal material and independently from approval. Unlocks Supplier Part, Package/Footprint, Parametrics and later AVL.