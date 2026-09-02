# Route Map Return Receipt — Scheme D

FigureID: FIG-TG-DJY-MAP-D
PromptVersion: ROUTE_MAP_PROMPT_PACKET_V2
FactSheetVersion: MAP_FACT_SHEETS_V1
OperatorReturn: 1000030632.png
Dimensions: 1024x1536
MappingBasis: operator return order 4/5; no opportunistic remap
ReviewRound: 1

## QA
- Independent image / no collage: PASS
- No readable labels / workflow metadata: PASS
- Phone portrait readability: PASS
- Subject intent: PARTIAL
- Low-rush / few mandatory nodes: FAIL
- Rest/meal emphasis: PARTIAL
- Station logic: FAIL
- Geographic/operational fidelity: FAIL
- Visual style: PASS as illustration reference

## Reject reasons
1. The render shows separate rail/station positions rather than one central Lidui Park arrival/return node.
2. Scenic routing remains visually dense and complex; it does not communicate Scheme D's intentionally reduced mandatory-node load.
3. The formal meal and quiet dessert/tea rest are not clearly separated as two distinct high-dwell nodes.
4. The pseudo-realistic basemap invents internal paths and river/building geometry, which is too risky for a route map intended for actual use.

Verdict: REJECTED
RejectCode: STATION_LOGIC;LOW_RUSH_STRUCTURE;REST_NODE_DIFFERENTIATION;GEOGRAPHY_HALLUCINATION
NextAction: regenerate as the simplest topology of all five schemes, with one station anchor, one optional bridge branch, one prominent formal-meal stop and one separate quiet rest stop.