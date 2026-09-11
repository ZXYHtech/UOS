# TASK_INV_IMPL_E13_S06 — Loop Prevention, Kill Switch & Circuit Breakers

## Status
`DESIGN_READY_BLOCKED_BY_E13_S05`

## Objective
Prevent automation cascades, self-trigger loops and runaway high-impact activity while preserving manual operations.

## Controls
Support:

- causation chain / self-caused-event awareness;
- maximum automation chain depth;
- rule-cycle detection where statically possible;
- per-rule/domain/account rate limits;
- max quantity/value/action count per window;
- global automation pause;
- per-domain pause;
- per-rule disable;
- high-impact circuit breaker.

## Rule behavior
Automation context is propagated into emitted events. Rules may explicitly ignore their own causal events where appropriate.

A circuit breaker pauses future automation requests but never reverses already committed business history automatically.

Manual domain commands remain usable unless the domain itself is independently locked for safety.

## Tests
- A -> B -> A loop is stopped by depth/cycle controls;
- self-caused status event does not re-fire indefinitely;
- rate/value threshold trips circuit breaker;
- global pause stops automation jobs while manual command still works;
- resume does not blindly replay obsolete queued actions without state revalidation.

## Done
One bad rule cannot create an uncontrolled event/action storm or disable normal manual business operation.