# E04 Execution Packets Index — Electronics Component Master

## Status

`ALL_E04_EXECUTION_PACKETS_READY_BLOCKED_BY_E03_GATE`

## Entry gate

Runtime E04 starts only after:

```text
E00 complete
E01 complete
E11 early complete
E02 authoritative stock kernel complete
E03 warehouse execution gate complete
current-main Release Gate PASS
```

Each slice branches from then-current `main` and takes the next contiguous migration only when schema is needed.

## Slice A — Internal Part Contract

Packet: `E04_SLICE_A_EXECUTION_PACKET.md`  
Branch: `impl/e04-internal-part-contract`  
Migration: `NONE expected`

Invariant:

```text
materials.id/material_code = stable internal part identity
```

No second canonical internal-part master and no inferred MPN rewrite.

## Slice B — Manufacturer + MPN

Packet: `E04_SLICE_B_EXECUTION_PACKET.md`  
Branch: `impl/e04-manufacturer-mpn`

Schema:

```text
manufacturers
manufacturer_aliases
manufacturer_parts
```

Identity:

```text
manufacturer + normalized MPN
```

Existence is not approval.

## Slice C — Supplier Part

Packet: `E04_SLICE_C_EXECUTION_PACKET.md`  
Branch: `impl/e04-supplier-part`

Schema:

```text
supplier_parts
```

Identity:

```text
supplier + supplier SKU
```

Preferred/available supplier source does not grant engineering approval.

## Slice D — Package / Footprint

Packet: `E04_SLICE_D_EXECUTION_PACKET.md`  
Branch: `impl/e04-package-footprint`

Schema:

```text
packages
footprints
package_footprint_relations
```

Package and EDA Footprint remain separate controlled identities.

## Slice E — Typed Parametrics

Packet: `E04_SLICE_E_EXECUTION_PACKET.md`  
Branch: `impl/e04-parametrics`

Schema:

```text
part_attribute_definitions
part_attribute_values
```

Critical separation:

```text
internal material value = requirement/design intent
Manufacturer Part value = source/datasheet characteristic
```

Unit-aware search returns candidates only.

## Slice F — Engineering Evidence / Lifecycle / Compliance

Packet: `E04_SLICE_F_EXECUTION_PACKET.md`  
Branch: `impl/e04-engineering-evidence`

Schema:

```text
engineering_evidence
+ bounded lifecycle/compliance relations as needed
```

Provider refresh cannot silently overwrite VERIFIED canonical evidence. Supersede rather than erase.

## Slice G — AML / AVL / Approved Substitutes

Packet: `E04_SLICE_G_EXECUTION_PACKET.md`  
Branch: `impl/e04-avl-substitute`

Schema:

```text
material_manufacturer_approvals
material_substitutions
```

Three different concepts remain separate:

```text
Alias != AML/AVL != Internal Substitute
```

Substitution is directional. Supplier preference, availability, parametric similarity or AI/provider confidence never creates approval.

Global/internal-material scope may start here; BOM-revision/WO/deviation scope waits for E05/E06 authoritative identities.

## Slice H — Component Workspace / Search / Provider Staging

Packet: `E04_SLICE_H_EXECUTION_PACKET.md`  
Branch: `impl/e04-component-workspace`

Migration: `NONE expected` for first search/UI slice; use next contiguous migration only if provider staging tables are required.

Search ranking favors exact identities over fuzzy text and displays explicit approval/evidence/lifecycle badges.

Workspace references E02 stock, pricing and purchase domains rather than copying their current values into the component master.

## E04-wide invariants

```text
Internal Part != Manufacturer Part != Supplier Part != Channel SKU
Alias != Approval
Candidate similarity != Substitute authority
Package != Footprint
Requirement value != Datasheet value
Provider imported != Verified
Preferred supplier != Approved MPN
```

## Migration numbering

Do not pre-reserve numeric versions in E04.

For each schema slice:

```text
read latest merged migration
 -> next contiguous number
 -> immutable checksum
 -> E00 pre/post integrity
 -> full Release Gate
```

## Universal stop conditions

Stop if:

- a parallel canonical material master appears;
- legacy `model/spec` is mass-converted to exact MPN without review;
- MPN normalization collapses meaningful orderable suffixes;
- Supplier Part bypasses AML/AVL;
- Package/Footprint collapse into one free-text field;
- provider data overwrites verified facts silently;
- parametric search/AI similarity becomes substitute approval;
- historical PO/BOM/approval evidence is rewritten from current master data.

## Completion

E04 completes when one controlled component master can answer:

```text
What is our internal part?
Which exact Manufacturer Parts exist?
Which supplier sources sell them?
What package/footprint/parameters/evidence do we know?
Which sources/substitutes are actually approved?
```

without inferring approval from search or sourcing availability.

Then E05 revisioned EBOM/MBOM/ECN may begin.