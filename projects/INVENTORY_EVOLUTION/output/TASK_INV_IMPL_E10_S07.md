# TASK_INV_IMPL_E10_S07 — Diagnosis, Repair, Retest, Exchange & Refund Execution

## Status
`DESIGN_READY_BLOCKED_BY_E07_E09_FOUNDATIONS`

## Objective
Preserve the complete technical/commercial after-sales history of each returned unit without overwriting its original build/test evidence.

## Diagnosis / repair
RMA diagnosis links to E07 test runs, defect/root-cause codes and NCR where appropriate. Repair order may record assigned user, controlled work instruction, components replaced, firmware/configuration changes, tuning/calibration actions and external repair reference.

## Retest
Never replace a failed diagnostic test with the final pass:

```text
FAIL test -> repair/rework -> PASS retest
```

Both remain in serial history; final release references the accepted evidence.

## Exchange
Track returned original and replacement sides independently:

```text
RMA -> replacement order/shipment -> replacement serial
```

Advance replacement can ship before original return; original remains an open asset/exception until received or formally written off.

## Refund
Refund has its own lifecycle and remote/payment identity. Refund completion never implies physical stock return. Physical receipt does not wait for refund to update quarantine evidence.

## Final dispositions
Support explicit outcomes such as restock-after-verification, repaired-return-to-customer, exchange, scrap, no-fault-found return, hold-for-engineering and supplier return.

## Tests
- original failed test remains after passing retest;
- replacement serial and original serial both remain traceable;
- advance exchange stays open until original accounted for;
- refund completion changes no stock by itself;
- repaired unit cannot become saleable without required E07 release;
- repair component/firmware changes append history rather than rewrite original configuration.

## Done
A serialized product's complete after-sales technical and commercial history can be reconstructed from original shipment through final resolution.