# Route Map Return Receipt — Scheme A

FigureID: FIG-TG-DJY-MAP-A
PromptVersion: ROUTE_MAP_PROMPT_PACKET_V2
FactSheetVersion: MAP_FACT_SHEETS_V1
OperatorReturn: 1000030629.png
Dimensions: 1024x1536
MappingBasis: operator return order 1/5; no opportunistic remap
ReviewRound: 1

## QA
- Independent image / no collage: PASS
- No readable labels / workflow metadata: PASS
- Phone portrait readability: PASS
- Subject intent: PARTIAL
- Route order vs fact sheet: FAIL
- Geographic/operational fidelity: FAIL
- Station logic: FAIL
- Visual style: PASS as illustration reference

## Reject reasons
1. The rendered rail/station geography reads as if rail enters/exits the scenic mountain-water landscape at separate positions rather than a single central Lidui Park arrival/return node.
2. The scenic path visually behaves like a high/north-to-south traversal rather than the Scheme A Gate-1/Lidui-side first-timer logic.
3. Detailed pseudo-cartographic waterways, roads and structures are AI-invented and therefore cannot be treated as an operational map.
4. The image is attractive but its realistic bird's-eye treatment creates false geographic confidence.

Verdict: REJECTED
RejectCode: GEOGRAPHY_HALLUCINATION;STATION_LOGIC;ROUTE_ORDER
NextAction: revise prompt to abstract topological route diagram over a simplified three-zone geographic scaffold; regenerate; do not patch by prose.