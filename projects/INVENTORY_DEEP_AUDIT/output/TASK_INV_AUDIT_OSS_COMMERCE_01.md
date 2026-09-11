# TASK_INV_AUDIT_OSS_COMMERCE_01 — Headless Commerce / Omnichannel Deep Benchmark

## 0. Scope and freshness

Research date: **2026-09-11**.

Inventory Lite evidence remains pinned to `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Benchmarks:

- Saleor;
- Medusa;
- Sylius.

The purpose is not to rebuild a storefront platform inside Inventory Lite. It is to identify mature patterns for channel/product/order/inventory/pricing/returns/integration boundaries that can improve marketplace and website integration.

## 1. Current maintenance / license snapshot

| System | Current evidence as of 2026-09-11 | License | Character |
|---|---|---|---|
| Saleor | GitHub latest release observed `3.23.22` on 2026-07-27; core repo active through September 2026 | BSD-3-Clause | GraphQL-native API-first commerce platform with channels/apps/extensions |
| Medusa | Official docs currently show `v2.20.1`; v2.18 was announced 2026-07-23 and project remains actively updated | Core MIT; identified Enterprise materials use separate commercial license | Modular TypeScript commerce framework with workflows, module links, events and plugins |
| Sylius | GitHub latest release `v2.2.8` on 2026-07-31 | MIT | Symfony/API Platform commerce framework with strong customization/state-machine heritage |

### Edition/license boundary

Saleor and Medusa have commercial/cloud/enterprise offerings around open-source cores; Sylius offers Sylius Plus modules. This report treats only portable architectural ideas and explicitly avoids assuming all commercial features exist in the open-source core.

## 2. Core conclusion

The most important shared lesson is that modern commerce engines separate:

```text
Product/catalog identity
Sales channel context
Pricing/promotion context
Inventory/reservation
Order state/version
Fulfillment
Payment/transaction
Return/refund
External integrations
```

Inventory Lite currently combines several of these concerns more tightly inside order/platform services. W4 already proposed durable omnichannel, pricing and settlement boundaries; the benchmark confirms that separation.

## 3. Saleor — strongest lesson: API-first channel layer and app boundary

### Current evidence

Saleor describes itself as a high-performance composable headless commerce API. Its current documentation organizes core concepts around:

- Products;
- Checkout;
- Channels;
- Promotions;
- Payments;
- API modeling/extensions;
- Apps/integrations;
- GraphQL API.

Its official organization states Saleor provides standard commerce modules while allowing commerce functions to be delegated to apps.

### What Inventory Lite should learn

#### A. Channel is first-class business context

A sales channel should not be just free-text source metadata.

For Inventory Lite, channel/account context should influence:

- product/SKU publication;
- stock publication policy;
- pricing;
- order identity;
- shipping/payment integration;
- settlement economics;
- permission/account scope.

This aligns with W4's recommendation to use `platform_account_id` as part of canonical external identity.

#### B. Commerce core versus integration app

Saleor's app architecture is a strong conceptual boundary:

```text
Core commerce event/state
 -> integration app/provider
```

Inventory Lite should use connector modules for Taobao/Pinduoduo/website rather than mix provider API semantics into order/inventory core.

#### C. API as primary contract

Saleor's GraphQL-first design demonstrates the value of a coherent public API contract, but Inventory Lite does not need GraphQL merely to copy modern architecture.

Portable principle:

- stable typed API schemas;
- explicit object IDs/status;
- version/deprecation policy;
- permission-aware integration surface.

REST is adequate if governed consistently.

## 4. Saleor security lesson

Saleor 3.23.22 fixed 2026 account-pre-hijacking and GraphQL authorization vulnerabilities, and adjacent releases also fixed permission checks.

Portable lesson:

A powerful extensible API greatly increases object-level authorization risk. Inventory Lite's W5 security recommendation—route/action registry + permission/scope tests—should apply equally to future connector/admin APIs.

Do not equate an API framework with security correctness.

## 5. Medusa — strongest architectural benchmark for Inventory Lite

Medusa v2's design is unusually relevant because it combines modular-monolith concepts with explicit workflows and commerce modules.

Official docs list commerce modules such as:

- Cart;
- Customer;
- Fulfillment;
- Inventory;
- Order;
- Payment;
- Pricing;
- Product;
- Promotion;
- Sales Channel;
- Stock Location;
- Tax;
- Store.

Each module owns a bounded data model/service.

This is close to the target decomposition recommended for Inventory Lite.

## 6. Medusa inventory and reservation model

Official Inventory Module docs distinguish:

```text
InventoryItem
InventoryLevel by location
  stocked_quantity
  reserved_quantity
  incoming_quantity
ReservationItem
```

Available stock is derived from stocked minus reserved quantity; incoming quantity is distinct.

When an order is placed, reservations are created. On fulfilment, stocked and reserved quantities are reduced. On cancellation, reservations are released.

### This directly validates Inventory Lite's P0 priority

Current Inventory Lite cannot safely scale omnichannel until it has an authoritative reservation model.

A strong target is conceptually:

```text
physical / stocked
reserved by business reference
incoming/scheduled supply
quality/non-saleable exclusions
= ATP / available
```

The reservation itself should be a first-class object, not only a cached `quantity_locked` number.

## 7. Medusa inventory kits

Medusa can link a product variant to multiple inventory items, and ordering the variant reserves the required quantity of each inventory item.

This maps directly to Inventory Lite's **sales/kit BOM** use case.

Important boundary:

```text
Commerce kit BOM
!=
Engineering BOM
!=
Manufacturing BOM
```

Medusa is useful evidence for keeping a lightweight commerce inventory kit independent from W3's released MBOM.

## 8. Medusa sales-channel model

Official Sales Channel docs state a channel can scope:

- product availability;
- cart/order;
- inventory availability through linked stock locations.

Portable Inventory Lite pattern:

```text
Channel / platform account
 -> available products/SKUs
 -> permitted warehouse/stock-location pool
 -> channel price rules
 -> publication policy
 -> canonical orders
```

Do not create separate inventory balances owned by each marketplace unless they truly represent different physical/contractual stock.

Use central ATP with channel publication/allocation policy.

## 9. Medusa pricing and promotion separation

Medusa has independent Pricing and Promotion modules.

Pricing supports:

- multi-currency/region;
- price lists;
- quantity tiers;
- contextual rules such as customer group.

Promotion supports:

- percentage/amount discounts;
- order/item/shipping targets;
- eligibility rules;
- campaigns/budgets.

### Inventory Lite implication

Current `PricingService` is already strong enough that it should not be replaced. Instead, separate:

```text
Base/contract/channel price
Promotion/discount adjustment
Order price snapshot
Settlement/economic event
```

Do not make every campaign a new permanent product price row.

## 10. Medusa order returns

Medusa's Return model explicitly distinguishes:

- requested/received return lifecycle;
- received quantity;
- damaged quantity;
- return shipping;
- refund amount/transaction;
- exchanges and claims.

The inventory flow only restores received quantity considered restockable; damaged/dismissed quantity is not simply returned to stock.

This strongly validates W4's RMA conclusion:

```text
financial refund != physical return != restock eligibility
```

For RF products, Inventory Lite should go further by adding serial diagnosis/test/warranty/rework evidence.

## 11. Medusa workflows — strongest portable architecture pattern

Medusa workflows are composed of steps and explicitly support:

- progress tracking;
- rollback/compensation logic;
- asynchronous long-running actions;
- retry configuration;
- execution from APIs, subscribers and scheduled jobs.

This is very close to what Inventory Lite needs for multi-step cross-system operations.

### Portable use cases

- marketplace fulfilment push;
- settlement import;
- supplier data refresh;
- document extraction;
- RMA exchange;
- report generation;
- automated rule actions;
- controlled external machine integration.

### Do not copy the whole workflow engine initially

Inventory Lite can start with:

```text
domain transaction
 -> outbox/job
 -> step state
 -> idempotent handler
 -> compensating action
```

and only add a more general step-workflow abstraction where multiple real use cases converge.

## 12. Medusa module links

Medusa intentionally isolates module data models and links them through separate link records rather than allowing one module to reach into another module's schema casually.

This is an important maintainability lesson.

Inventory Lite can emulate the *ownership rule* without implementing Medusa's SDK:

```text
orders owns order tables
inventory owns stock/reservation tables
crm owns opportunity/customer-case data

cross-domain relation uses stable IDs/service/query projection
```

Avoid every new feature adding foreign-purpose columns to `orders` or `materials`.

## 13. Medusa event/subscriber distinction

Medusa distinguishes workflow events from service/technical events and emits workflow events after successful business flow completion.

This aligns almost exactly with W5 automation design:

- business event triggers notification/integration;
- technical event supports observability;
- integral steps remain inside the business workflow;
- side effects occur asynchronously where appropriate.

Inventory Lite should borrow this distinction.

## 14. Medusa plugins versus modules

Official docs state:

- module = isolated single-domain/integration capability;
- plugin = reusable package that may combine modules, API routes, workflows, links, subscribers, jobs and admin extensions.

Recommended Inventory Lite evolution:

### First

Internal modules only.

### Later

Provider/plugin packaging for:

- marketplace connector;
- distributor part-data provider;
- shipping carrier;
- accounting export;
- test-equipment adapter;
- AI provider.

Do not create a third-party plugin marketplace before internal extension contracts are stable.

## 15. Medusa infrastructure modules — what to borrow and what to avoid

Medusa abstracts event, cache, workflow-engine, file, notification and locking infrastructure.

Portable principle:

Business code depends on an interface rather than Redis/S3/provider-specific implementation.

For Inventory Lite:

```text
ArtifactStore
NotificationProvider
CommerceConnector
PartDataProvider
AIProvider
```

are worthwhile.

But current scale does **not** justify immediately abstracting every database/cache/lock subsystem or deploying Redis solely to imitate Medusa.

## 16. Sylius — strongest lesson: explicit commerce state machines and framework customization

Sylius remains actively maintained; v2.2.8 is the current observed release and the core is MIT-licensed.

It is built on Symfony/API Platform and has a long-standing state-machine/customization orientation.

The public repository also distinguishes Sylius Plus commercial capabilities such as advanced multi-store, returns and multi-source inventory.

### Portable lessons

#### A. Explicit state transitions

Commerce actions such as order/payment/shipment should be modeled as valid transitions, not arbitrary status edits.

Inventory Lite already needs this for:

- order;
- shipment;
- return/RMA;
- platform sync;
- settlement.

#### B. Extension through framework services/plugins

Sylius demonstrates how a commerce product can remain customizable without editing every core path. Again, Inventory Lite should formalize provider and domain extension seams.

#### C. Open-source/commercial boundary warning

Feature comparisons must distinguish core from paid modules. Inventory Lite should avoid selecting a pattern solely because a vendor's marketing page lists a feature.

## 17. Cross-system capability comparison

| Capability | Saleor | Medusa | Sylius | Inventory Lite direction |
|---|---|---|---|---|
| API-first commerce | Very strong GraphQL | Strong REST/framework | Strong API Platform | Governed REST/domain API sufficient |
| Sales channels | Core concept | First-class module | Core concept | Platform account/channel context |
| Product/channel availability | Strong | Strong | Strong | Channel publication/mapping |
| Inventory reservation | Mature commerce behavior | Explicit ReservationItem | Commerce inventory patterns | P0 first-class reservation ledger |
| Multi-location stock | Strong commerce model | InventoryLevel + StockLocation | Core/Plus split depending feature | Central stock positions + channel pools |
| Pricing | Channel/context rich | Dedicated pricing module | Price/channel rules | Preserve PricingService + clarify context |
| Promotions | Strong | Separate promotion module | Strong | Separate promotion from master price |
| Orders | Strong | Dedicated order module | Strong state-machine heritage | Canonical order + immutable snapshots |
| Returns | Strong commerce flow | Explicit return/RMA/exchange concepts | Core/Plus capability varies | Serial-aware RMA extension |
| Payments/transactions | Strong | Dedicated module | Strong | Integrate/payment evidence, don't rebuild PSP |
| Plugins/apps | Strong Apps | Modules/plugins | Symfony/Sylius plugins | Connector/provider interfaces |
| Durable workflow | Webhook/app orchestration | Very strong built-in workflow engine | State machines/services | Lightweight outbox/jobs first |

## 18. What Inventory Lite should NOT become

Do not rebuild:

- shopping cart engine;
- storefront CMS;
- payment gateway orchestration platform;
- generic promotion engine beyond actual business needs;
- international tax engine;
- multi-tenant marketplace platform;
- headless frontend framework.

Those products solve customer-facing commerce creation. Inventory Lite's current value is **back-office operational truth and marketplace integration**.

For the company website, a headless commerce platform can be integrated later if website checkout/catalog complexity grows.

## 19. Correct system boundary

Recommended architecture:

```text
Website / Taobao / Pinduoduo / future commerce platforms
             |
       Connector adapters
             |
 External object ledger + canonical order
             |
      Reservation / ATP kernel
             |
 Inventory / fulfilment / RMA / settlement
```

If a future Saleor/Medusa/Sylius storefront is introduced:

```text
Commerce engine owns cart/checkout/customer storefront experience
Inventory Lite owns enterprise SKU, warehouse/manufacturing/quality truth
Sync uses idempotent external-object + reservation/inventory contracts
```

Do not dual-own the same order/inventory fields without an explicit source-of-truth matrix.

## 20. Patterns to adopt immediately

### P0

1. Medusa-style explicit reservation object/lifecycle.
2. Separate stocked/reserved/incoming concepts.
3. First-class sales-channel/account scope.
4. Separate price, promotion adjustment and settlement economics.
5. Return received/restockable/damaged distinctions.
6. domain modules with explicit ownership.
7. domain event after successful workflow + async subscriber/outbox.
8. typed integration/provider boundaries.

### P1

1. workflow step/compensation abstraction for cross-system actions;
2. plugin/provider packaging;
3. API schema/deprecation governance;
4. website commerce connector if direct web sales grow;
5. customer/account synchronization rules.

### Avoid for now

1. GraphQL migration purely for fashion;
2. storefront platform rewrite;
3. Redis/event-bus infrastructure before measured need;
4. generic checkout/cart/payment engine;
5. enterprise multi-store marketplace complexity.

## 21. Security lessons

Current peer releases also demonstrate that commerce APIs are high-value attack surfaces:

- Saleor 2026 releases fixed account and authorization vulnerabilities;
- Sylius 2026 releases included IDOR/payment/channel restriction security fixes.

Inventory Lite should therefore require:

- object-level permission tests;
- platform account scope;
- order state-transition validation;
- immutable price/address snapshots;
- idempotency on externally replayable commands;
- webhook/polling signature/provenance checks where providers support them;
- no trust in client-supplied role/warehouse/order ownership.

## 22. Sources

Current public evidence consulted on 2026-09-11:

### Saleor

- Core repository/releases: https://github.com/saleor/saleor/releases
- Saleor organization/core repository: https://github.com/saleor
- Documentation: https://docs.saleor.io/

### Medusa

- Repository/license: https://github.com/medusajs/medusa
- Current documentation: https://docs.medusajs.com/
- Commerce Modules: https://docs.medusajs.com/resources/commerce-modules
- Inventory Module: https://docs.medusajs.com/resources/commerce-modules/inventory
- Inventory concepts: https://docs.medusajs.com/resources/commerce-modules/inventory/concepts
- Reservations lifecycle: https://docs.medusajs.com/resources/commerce-modules/inventory/reservations-lifecycle
- Sales Channel Module: https://docs.medusajs.com/resources/commerce-modules/sales-channel
- Pricing: https://docs.medusajs.com/resources/commerce-modules/pricing
- Promotion: https://docs.medusajs.com/resources/commerce-modules/promotion
- Order: https://docs.medusajs.com/resources/commerce-modules/order
- Returns: https://docs.medusajs.com/resources/commerce-modules/order/return
- Modules: https://docs.medusajs.com/learn/fundamentals/modules
- Module Links: https://docs.medusajs.com/learn/fundamentals/module-links
- Workflows: https://docs.medusajs.com/learn/fundamentals/workflows
- Events/Subscribers: https://docs.medusajs.com/learn/fundamentals/events-and-subscribers
- Plugins: https://docs.medusajs.com/learn/fundamentals/plugins

### Sylius

- Repository/license: https://github.com/Sylius/Sylius
- Releases: https://github.com/Sylius/Sylius/releases
- Documentation: https://docs.sylius.com/

## 23. Acceptance signals

- Saleor, Medusa and another maintained headless commerce framework are compared using current evidence;
- channel, product, inventory reservation, pricing/promotion, orders, returns and integration patterns are covered;
- core/open-source versus enterprise/commercial boundaries are acknowledged;
- the report identifies what Inventory Lite should integrate rather than rebuild;
- recommendation preserves one source of truth for warehouse/manufacturing inventory;
- architecture patterns map directly to W4 omnichannel/RMA/finance conclusions;
- no required connector/workflow/scheduler path depends on GitHub Actions.

## 24. Core recommendation

Medusa provides the most directly portable commerce architecture pattern: **domain modules + explicit reservation + workflows/events + provider interfaces**. Saleor reinforces channel/API/app separation, and Sylius reinforces state-machine discipline. Inventory Lite should adopt those back-office patterns while deliberately refusing to become a storefront/checkout/payment platform.