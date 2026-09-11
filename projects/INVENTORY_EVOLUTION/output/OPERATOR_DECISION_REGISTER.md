# INVENTORY_EVOLUTION — Operator Decision Register

## Purpose

This file records business/operations policies that implementation must expose and validate rather than guess. A story may prototype a safe default only when it is clearly labeled and reversible; production authority requires explicit policy or documented fallback.

## Decision states

```text
OPEN
PROVISIONAL
APPROVED
SUPERSEDED
NOT_NEEDED
```

Each approved decision should record owner/date/effective scope and the implementation stories it unlocks.

## D01 — Production RPO / RTO / off-host backup target

Status: `OPEN`

Need decisions:

- acceptable data-loss window (RPO);
- acceptable restore time (RTO);
- off-host/off-disk destination type;
- artifact/config retention duration;
- backup encryption/access policy;
- restore-drill cadence.

Safe implementation default before approval:

- never claim off-host success unless target exists and carries expected marker;
- backup/recovery failure blocks production cutover;
- local verified backup remains distinct from disaster recovery.

Unlocks/affects: E00, E07 raw RF artifacts, E05 controlled docs, E14 retained AI evidence.

## D02 — Production cutover authority

Status: `OPEN`

Need decisions:

- who may authorize maintenance window;
- who reviews preflight evidence;
- who chooses rollback vs repair after failed cutover;
- maximum acceptable maintenance duration before rollback decision.

Safe default: fail closed after writer quiescence; do not auto-resume unknown mixed state.

## D03 — Stock status taxonomy

Status: `OPEN`

Need final business labels/policies for at least:

```text
saleable/available
reserved
in_transit
receiving_staging
quarantine
rework
scrap
engineering/prototype
WO WIP
subcontract/external WIP
service/RMA
non-saleable reference/golden sample
```

Important: status semantics must define ATP/MRP eligibility, not merely screen color.

Unlocks: E02/E03/E06/E07/E08/E10.

## D04 — Legacy stock/bin migration policy

Status: `OPEN`

Choices may include:

- retain unknown location as `LEGACY/UNASSIGNED`;
- require count/putaway before location becomes authoritative;
- prohibit fabricated historical bin assignment.

Recommended safe principle: unknown remains unknown until physical observation.

Unlocks: E02/E03 cutover.

## D05 — Base UOM and conversion authority

Status: `OPEN`

Need policy for:

- canonical material UOM;
- purchase-pack/order-pack conversions;
- reel/tray/panel versus each/piece;
- decimal quantity policy;
- who may create/change conversion factors;
- historical snapshot behavior.

Unlocks: E02/E04/E08/costing.

## D06 — Internal part numbering convention

Status: `OPEN`

Need decision whether internal codes encode family/category or remain opaque identifiers.

Recommendation: keep code stable and avoid embedding volatile supplier/MPN attributes.

Unlocks: E04 migration/UI.

## D07 — Manufacturer / MPN normalization rules

Status: `OPEN`

Need policy for:

- case/punctuation normalization;
- packaging suffix distinctions;
- manufacturer aliases/mergers;
- base device vs orderable MPN identity.

Safe rule: exact engineering distinctions are preserved even when search normalization is permissive.

Unlocks: E04.

## D08 — AVL/AML approval authority

Status: `OPEN`

Need definitions for:

- Approved vs Preferred vs Conditional vs Rejected;
- who may approve each state;
- scope by product/BOM/customer/site;
- evidence required for conditional substitutes;
- expiration/review policy.

Hard invariant: similarity, supplier availability or AI confidence never creates approval.

Unlocks: E04/E05/E06/E08.

## D09 — Product / Part revision naming

Status: `OPEN`

Examples:

```text
A/B/C
A1/A2
1.0/1.1
```

Need policy for hardware revision, document revision and firmware version relation. Avoid forcing them into one version field.

Unlocks: E05.

## D10 — EBOM / MBOM release authority and effectivity

Status: `OPEN`

Need decisions:

- release approver(s);
- date/serial/lot/WO based effectivity;
- emergency deviation authority;
- whether two-person approval is required for selected products;
- obsolete/superseded behavior.

Unlocks: E05/E06/E08.

## D11 — Controlled document classes and retention

Status: `OPEN`

Candidate classes:

```text
drawing
assembly instruction
inspection instruction
test specification
limit set
firmware binary/source reference
calibration/tuning procedure
certificate/report template
```

Need retention and release requirements per class.

Unlocks: E05/E07.

## D12 — Traceability policy by family

Status: `OPEN`

Choose per material/product family:

```text
NONE
LOT
SERIAL
LOT_AND_SERIAL
```

Need risk policy for:

- high-value RF modules;
- active IC/MMIC/SAW/filter components;
- connectors/mechanical parts;
- passives;
- customer-specific/certification products.

Recommendation: risk-based, not universal serialization.

Unlocks: E07.

## D13 — RF test raw-data retention policy

Status: `OPEN`

Need policy for:

- which products must retain `.s2p`, spectrum/sweep/raw CSV;
- retention duration;
- file naming/object key;
- required metadata/hash;
- screenshots vs raw data minimum;
- retest retention;
- customer report retention.

Unlocks: E07/E00 backup extension.

## D14 — Test equipment calibration policy

Status: `OPEN`

Need rules for:

- calibration expiry handling;
- grace/exception authority;
- external certificate storage;
- internal verification checks;
- invalidation/review of tests executed while calibration status uncertain.

Unlocks: E07.

## D15 — Quality state / disposition authority

Status: `OPEN`

Need authorization matrix for:

- ACCEPTED;
- QUARANTINE;
- REJECTED;
- REWORK;
- SCRAP;
- USE_AS_IS / deviation where allowed.

Need two-person or manager approval thresholds for high-value scrap/exception release.

Unlocks: E07/E10.

## D16 — MRP planning policy

Status: `OPEN`

Need policy by material/site for:

- Buy/Make/Transfer/Mixed;
- safety stock;
- lead time;
- MOQ/order multiple;
- planning horizon;
- firm/frozen window;
- whether planned/firm WO supply is nettable;
- approved source selection rules.

MRP remains advisory until explicitly approved otherwise.

Unlocks: E08.

## D17 — Subcontract ownership / loss tolerance

Status: `OPEN`

Need policy for:

- company-consigned vs supplier-owned input;
- accepted process loss/scrap;
- reconciliation tolerance;
- responsibility/approval for unresolved variance;
- expected return quality gate.

Unlocks: E08/E11.

## D18 — Channel ATP publication policy

Status: `OPEN`

Need per account/channel:

- safety buffer/holdback;
- maximum published quantity;
- channel priority;
- low-stock freeze;
- made-to-order policy;
- serialized/high-value product policy;
- publication/reconciliation cadence.

Hard invariant: channel connector never derives its own stock from raw balance.

Unlocks: E09.

## D19 — CRM customer identity / matching policy

Status: `OPEN`

Need policy for when marketplace buyers/contact names are linked to durable CRM customers.

Recommended: no automatic durable merge on receiver name/phone alone; use explicit or reviewed matching.

Unlocks: E10.

## D20 — Quote approval / commercial floor policy

Status: `OPEN`

Need:

- floor source/precedence;
- margin thresholds;
- dedicated below-floor override roles;
- quote validity defaults;
- approval thresholds by amount/margin/customer/channel;
- currency/FX policy where applicable.

Early implementation already reserves separate authority for floor override.

Unlocks: E11 early/E10.

## D21 — Warranty policy

Status: `OPEN`

Need policy by product/customer/channel/jurisdiction where relevant:

- warranty term;
- exclusions;
- goodwill/partial coverage authority;
- advance replacement policy;
- diagnosis evidence;
- customer-damage decision authority.

System should preserve evidence, not invent legal rules.

Unlocks: E10.

## D22 — RMA restock / refurbished condition policy

Status: `OPEN`

Need allowed condition grades and quality/test requirements before return to ATP.

Possible grades:

```text
NEW
OPENED_VERIFIED
REFURBISHED
SERVICE_SPARE
NON_SALEABLE_REFERENCE
```

Unlocks: E10/E07/E11.

## D23 — Standard cost policy

Status: `OPEN`

Need decisions:

- standard cost cadence/effective date;
- acquisition cost basis;
- labor/overhead rates;
- subcontract/freight inclusion;
- who releases standard cost;
- relationship to formal accounting.

Keep separate from current/reference estimator.

Unlocks: E11 late.

## D24 — Inventory valuation/accounting boundary

Status: `OPEN`

Need accountant-approved choice eventually for moving average/FIFO/standard or integration boundary.

Do not let operational application silently invent statutory accounting policy.

Unlocks: E11 advanced/accounting integration.

## D25 — Contribution-profit formula policy

Status: `OPEN`

Need canonical inclusion/exclusion of:

- seller discounts;
- platform subsidy;
- commission;
- payment fee;
- outbound/return freight;
- fulfilment fee;
- actual/standard COGS;
- RMA/replacement/repair costs;
- ad spend attribution (possibly second-layer only).

Unlocks: E11/E12.

## D26 — KPI governance ownership

Status: `OPEN`

Need named business owners for key metrics such as:

- ATP;
- inventory value;
- on-time shipment;
- supplier OTIF;
- FPY;
- RMA rate;
- gross/contribution margin;
- quote conversion.

Metric owner approves formula/scope changes.

Unlocks: E12.

## D27 — Management review cadence

Status: `OPEN`

Need cadence/owners for:

- daily exception review;
- weekly operating review;
- monthly portfolio/economic review;
- product/supplier/quality actions.

Unlocks: E12 scheduled reports/action loop.

## D28 — Automation authority matrix

Status: `OPEN`

Need business approval for which E13 action types may be:

```text
A0 automatic insight
A1 automatic notify/draft
A2 automatic reversible mutation
A3 always human approved
```

Default until approved: A3 human approval, broad A2 disabled.

Unlocks: E13.

## D29 — AI provider / data boundary

Status: `OPEN`

Need explicit policy for which data classes may leave deployment boundary:

```text
public product data
internal engineering data
supplier commercial data
customer PII
controlled/NDA docs
order images
RF raw data
```

Secrets/credentials are always forbidden.

Need provider retention/training policy and approved models/tasks.

Unlocks: E14 online-provider features.

## D30 — AI action authority

Status: `OPEN`

Need policy for which C0-C3 actions AI may prepare/execute after explicit approval.

Default:

- C0/C1 read/extract allowed by role;
- C2 draft/recommend allowed with evidence;
- C3 execute only after visible approval and deterministic validation;
- C4 high-consequence autonomous actions disabled.

Unlocks: E14 write bridge.

## D31 — Scale SLO / PostgreSQL entry criteria

Status: `OPEN`

Need acceptable thresholds for:

- write lock wait/error;
- p95/p99 request/transaction latency;
- DB size/backup duration;
- restore RTO;
- reporting interference;
- multi-host/HA/PITR requirement.

Do not use arbitrary order counts as migration trigger.

Unlocks: E15 Decision Gate 1.

## D32 — Multi-host / artifact storage target

Status: `OPEN`

Only needed if E15 is triggered.

Need target for:

- PostgreSQL operation/backup/PITR;
- shared immutable artifact storage;
- web/worker topology;
- operational monitoring/on-call responsibility.

Do not introduce Kubernetes/Redis/object storage solely for architectural aesthetics.

## Decision discipline

When a decision is approved:

```text
Decision ID
Status = APPROVED
Owner
Approved date
Effective date/scope
Chosen policy
Reason
Affected stories
Migration/rollout note
```

Do not bury policy choices only in source code or chat history.
