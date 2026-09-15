# TASK_INV_AUDIT_EXCEPTION_AUDITLOG_01 — Exception Handling & Audit-Log Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `ExceptionService`, `operation_logs`, inventory movement logs, transfer exception handling, recognition correction/revision records, unified todos and representative mutation paths.

## 1. Executive conclusion

Inventory Lite already has unusually good attention to business history for a lightweight system. Inventory movements are recorded separately from general operation logs; recognition corrections/revisions have dedicated history; transfer exceptions preserve explicit state; many service mutations call `log_operation`.

The main gap is that exception and audit behavior is still **convention-driven**. There is no single machine-checkable policy proving that every high-risk mutation emits the correct durable business event/audit entry.

The long-term target should be:

```text
Business ledger/event = authoritative economic/stock change
Audit log = who/why/administrative context
Exception = unresolved business condition requiring ownership/action
```

These are related but should not be collapsed into one table.

## 2. Existing layers

### Inventory ledger

`inventory_logs` records inventory-changing movements with material, warehouse, platform account, movement type, delta, resulting quantity, reference object, reason, actor and timestamp.

This is stronger than relying on `operation_logs` alone because the stock ledger is queryable as business history.

### General audit log

`operation_logs` contains:

- actor/user
- action type
- target type/id
- before JSON
- after JSON
- IP/device
- created timestamp

This is useful for administrative traceability.

### Domain history

Additional domain-specific history exists, including:

- recognition corrections
- recognition revisions
- price revisions
- transfer receipt events
- shipment/archive records

This shows the architecture is already moving toward domain-specific event/history tables where generic audit JSON is insufficient.

## 3. Positive transfer pattern

Transfer handling is a good reference implementation.

The flow can distinguish:

- requested/draft state
- outbound confirmation
- actual transfer-out stock ledger entry
- reversal of transfer-out
- partial receiving
- transfer-in ledger entry
- exception state
- exception resolution information

This is much safer than simply editing a transfer status and recalculating stock later.

Use this philosophy for future production issue/return, quality disposition and RMA.

## 4. ExceptionService is currently an aggregation layer

`ExceptionService` builds actionable exception items from underlying domain state, for example recognition problems and transfer exceptions.

This is appropriate for a lightweight system because not every exception needs its own duplicate master record.

However, once exceptions require acknowledgement, assignment, SLA, comments or repeated detection across time, a persistent exception/incident record becomes useful.

## 5. Recommended exception lifecycle

For business-critical exceptions introduce a durable record with:

```text
exception_id
exception_type
object_type/object_id
severity
fingerprint/dedup_key
status: open | acknowledged | investigating | resolved | ignored
owner_user/team
first_detected_at
last_detected_at
acknowledged_at/by
resolved_at/by
resolution_code
resolution_note
source_event/job
```

Do not create a new exception every time the dashboard refreshes. Deduplicate by fingerprint.

## 6. Audit coverage problem

Today many mutations explicitly call `log_operation`, but this is a hand-maintained convention inside large service/router files.

Risk:

```text
new endpoint implemented correctly functionally
-> developer forgets audit call
-> feature works
-> history silently missing
```

Recommendation: each mutating action should declare audit policy:

- `LEDGER_EVENT_REQUIRED`
- `AUDIT_REQUIRED`
- `LEDGER_AND_AUDIT_REQUIRED`
- `NO_AUDIT_REQUIRED` with reason

A repository-local static/contract test should enumerate mutation endpoints/actions and fail if the declaration is missing.

## 7. Immutability and correction policy

Never “fix” historical business events by silently editing or deleting them.

Preferred patterns:

- wrong stock movement -> compensating movement/reversal;
- wrong shipment deduction -> shipment revoke/reversal;
- wrong recognized value -> correction/revision record;
- wrong price -> price revision;
- wrong quality disposition later -> new disposition event.

Generic audit logs can record the actor/reason, but the domain ledger must remain mathematically reconstructable.

## 8. Soft-delete risk

Some ledgers/history have evolved to include deletion fields. This can be operationally useful for hiding erroneous/imported records, but high-risk business history should not become invisible without a compensating record and privileged reason.

Recommendation:

- ordinary business users should never hard-delete stock/economic events;
- administrative suppression must retain immutable tombstone/reason;
- aggregate calculations must explicitly define whether suppressed records participate;
- integrity tests should reconcile current balance to effective ledger sum.

## 9. Audit-log tamper resistance

Full cryptographic event sourcing is unnecessary today, but improvements are possible:

### Near term

- restrict write/delete access to log tables to service code;
- no ordinary UI delete for audit records;
- periodic integrity/reconciliation checks;
- backup logs with database.

### Later if compliance/customer requirements increase

- append-only database permissions in PostgreSQL;
- hash chaining or signed daily audit manifests;
- off-host log copy;
- security-event stream separate from business operations.

Do not add complexity before there is a real requirement.

## 10. High-risk domains that need explicit audit guarantees

Current/future actions deserving strict coverage:

- manual stock adjustment
- inventory count approval
- shipment deduction/revoke
- transfer ship/receive/reversal
- PO approval/receive
- material delete/restore/permanent delete
- price/floor-price override
- credential/security changes
- backup restore
- platform reconciliation override
- BOM/revision release
- ECN/ECO approval
- production issue/return/scrap/completion
- quality disposition/MRB
- serial/lot relabel or genealogy correction
- RMA disposition

## 11. Operational alert versus audit event

Do not send human alerts for every audit event.

Example:

- successful shipment deduction -> ledger + audit, no alert;
- shipment deduction repeatedly fails -> exception/todo;
- low stock -> alert/todo, not necessarily audit;
- admin changes price -> audit;
- price below floor -> exception plus audit if overridden.

This separation avoids alert fatigue.

## 12. No-Actions validation model

Recommended local/server checks:

```text
python3 tools/test_ledger_reconciliation.py
python3 tools/test_mutation_audit_coverage.py
python3 tools/test_exception_dedup.py
```

Scheduled reconciliation can run via systemd timer/cron or the application worker.

GitHub Actions is not required and is not accepted as the sole proof that audit coverage exists.

## 13. Priorities

### P0

1. define explicit ledger/audit/exception responsibilities;
2. add mutation-audit coverage registry/test;
3. add stock balance-to-ledger reconciliation test;
4. preserve reversal rather than destructive rewrite for business events;
5. protect backup restore/security/credential changes with mandatory audit.

### P1

1. persistent exception lifecycle for high-value incidents;
2. exception deduplication/ownership/acknowledgement;
3. scheduled reconciliation job independent of GitHub;
4. audit reason codes for high-risk overrides;
5. dashboards linking exception -> underlying evidence -> resolution action.

### P2

1. append-only DB enforcement after PostgreSQL migration if needed;
2. hash/signed integrity manifests if regulatory/customer value justifies it;
3. centralized security/audit export.

## 14. Preliminary maturity

- inventory movement ledger: 4/5
- transfer reversal/history: 4/5
- generic operation logging: 3.5/5
- specialized revision history: 3.5/5
- audit coverage enforcement: 2/5
- exception aggregation: 3/5
- persistent incident lifecycle: 1.5/5
- automated reconciliation: 1.5/5
- tamper resistance: 1.5/5

## 15. Core recommendation

Keep the current layered history model. Do not replace it with one generic event table. The next step is to make audit/ledger requirements **machine-checkable**, then add persistent incident lifecycle only where unresolved exceptions need ownership and SLA.