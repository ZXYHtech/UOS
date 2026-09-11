# TASK_INV_AUDIT_OCR_AI_01 — OCR / AI Recognition & Human Confirmation Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `recognition.py`, `ocr_queue.py`, recognition task schema, correction/revision history, order confirmation and image derivative jobs.

## 1. Executive conclusion

The OCR subsystem is one of the more mature technical parts of Inventory Lite. It is not simply a synchronous OCR call in the web request. The pinned source includes a **database-backed worker**, atomic task claiming, isolated child processes, timeouts, memory backpressure, interrupted-task handling and image-derivative background work.

This architecture is a strong pattern to reuse for other expensive/non-critical background work.

The recognition *business* model is also appropriately human-in-the-loop: OCR/AI produces a candidate order, duplicate/missing-data checks run, and the user confirms before creating authoritative business objects.

The key gaps are provider maturity, evaluation governance and confidence policy. `online_ai` is still documented as reserved/unconfigured, so it must not be described as a production AI capability.

## 2. Confirmed provider architecture

The source defines `RecognitionProvider` with concrete providers including:

- `mock`
- `local_ocr`
- `online_ai`
- auto/provider-selection behavior elsewhere in the recognition path

Local OCR can use Tesseract and optional RapidOCR. It includes specialized handling for long screenshots, tiled processing, coordinate restoration and memory trimming.

This is significantly more robust than decoding arbitrary giant screenshots directly inside the HTTP process.

## 3. Worker architecture — strong positive finding

`ocr_queue.py` explicitly states that the database-backed OCR queue is isolated from the web process.

Observed controls:

### Atomic task claim

Worker executes `BEGIN IMMEDIATE`, selects one queued recognition task, and changes it to running only when the current status is still queued.

This is a useful SQLite-compatible claim pattern.

### Child-process isolation

Each OCR task runs in a new child Python process. A native OCR crash, memory leak or model state is therefore less likely to kill the web API.

### Timeout

Long-running child jobs are terminated and eventually killed if they exceed the configured task timeout.

### Memory backpressure

The daemon reads Linux available memory and yields if free memory falls below a configured threshold.

### Interrupted work policy

A recognition task left in `running` after service interruption is not blindly replayed. It is marked failed and requires explicit re-recognition. This is conservative and appropriate because OCR/confirmation may have side effects elsewhere.

### Derivative image jobs

Image overview/thumbnail generation has its own durable job records and process isolation.

## 4. Why this pattern should be reused

The existing OCR worker is a practical template for future jobs such as:

- marketplace synchronization;
- MRP calculation;
- report generation;
- large import processing;
- backup verification;
- RF test-file parsing;
- search indexing;
- AI assistant analysis.

Do not introduce five different queue frameworks. Extract a small common durable-job framework later while preserving domain-specific payloads/retry rules.

## 5. Human confirmation model

Recognition is correctly treated as **candidate data**, not authoritative inventory/order truth.

The source contains:

- `recognition_tasks`
- `recognition_revisions`
- `recognition_corrections`
- duplicate order checks
- missing/ambiguous item checks
- manual confirmation state
- existing-order/shipment reuse checks

This is the right design for AI/OCR in a business system:

```text
machine inference -> structured candidate -> validation -> human review when required -> canonical order service
```

not:

```text
OCR result -> immediately deduct inventory
```

## 6. Correction data is a valuable future asset

The system records structured differences between recognized and human-corrected data.

This can later support:

- field-level OCR accuracy statistics;
- SKU confusion matrices;
- merchant/platform-specific error patterns;
- confidence calibration;
- targeted rule/model improvement;
- regression datasets.

Important governance rule: correction records may contain personal/order data. Training/evaluation datasets should minimize or mask PII where it is not needed.

## 7. Provider truth boundary

Documentation explicitly describes `online_ai` as a reserved interface that is not configured with model/API key by default.

Therefore capability states should be:

- mock: test-only
- local OCR: implemented, environment-dependent
- online AI: adapter/reserved or experimental until a real configured provider is validated

UI should not display an available-looking provider that cannot execute successfully in the deployed environment without a clear status.

## 8. Missing evaluation framework

A production recognition system needs measurable acceptance criteria beyond “it looks better”.

Recommended evaluation dataset dimensions:

- platform/shop
- screenshot resolution
- long screenshot versus normal
- light/dark theme
- compressed/shared image
- Chinese/English SKU
- quantities containing commonly confused digits
- bundle/BOM product
- multi-line order
- missing logistics data
- already-shipped order

Metrics should include:

- exact order-number accuracy
- SKU match accuracy
- quantity accuracy
- receiver/address field accuracy where used
- false-auto-confirm rate
- manual-review rate
- duplicate-detection recall
- processing time
- worker failure/timeout rate

## 9. Confidence policy

Do not use one global model confidence as the only auto-confirm gate.

Use field/business-risk gates, for example:

- order number must meet exact structural validation;
- every inventory-affecting item must resolve to an unambiguous material;
- quantity must satisfy order-level consistency checks;
- suspicious duplicate blocks auto confirmation;
- high-value/large-quantity orders may require review regardless of OCR confidence;
- address confidence should not be allowed to override product/quantity uncertainty.

## 10. Reliability enhancements

### P0

1. keep OCR out of HTTP request process;
2. formalize provider availability/status contracts;
3. add deterministic evaluation command and fixed regression samples;
4. distinguish provider technical success from business-valid recognition;
5. protect correction/evaluation data containing PII.

### P1

1. extract reusable durable-job primitives from OCR worker without overengineering;
2. persist attempt/run metadata separately from final business state;
3. add queue latency/failure/timeout metrics;
4. introduce bounded retry rules by failure class;
5. add dead-letter/review path for repeated technical failures.

### P2

1. online multimodal provider adapter with explicit privacy/cost policy;
2. confidence calibration by field/platform;
3. active-learning workflow from correction data;
4. model/version provenance per recognition result.

## 11. No-Actions operating model

Recommended service ownership:

```text
inventory-web.service
inventory-worker.service or inventory-ocr.service
```

Worker health can be checked through systemd/process supervision plus application health records. GitHub Actions is neither scheduler nor supervisor.

Local regression command should resemble:

```text
python3 tools/evaluate_recognition_regression.py --dataset tests/recognition-fixtures
```

## 12. Preliminary maturity

- provider abstraction: 4/5
- local OCR engineering: 4/5
- background worker isolation: 4.5/5
- human confirmation/audit: 4/5
- online AI production readiness: 1/5
- quantitative evaluation governance: 2/5
- AI confidence/risk policy: 2.5/5
- reusable job framework: 2.5/5

## 13. Core recommendation

Do not replace the OCR subsystem with a generic AI call. Preserve the current durable worker and human-confirmation architecture. The highest-value next step is to turn correction history into a reproducible evaluation system and to reuse the worker pattern for other asynchronous business jobs.