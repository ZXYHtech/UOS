# Route Map Return Receipt — Scheme C

FigureID: FIG-TG-DJY-MAP-C
PromptVersion: ROUTE_MAP_PROMPT_PACKET_V2
FactSheetVersion: MAP_FACT_SHEETS_V1
OperatorReturn: 1000030631.png
Dimensions: 1024x1536
MappingBasis: operator return order 3/5; no opportunistic remap
ReviewRound: 1

## QA
- Independent image / no collage: PASS
- No readable labels / workflow metadata: PASS
- Phone portrait readability: PASS
- Subject intent: PARTIAL
- Food/old-city dwell emphasis: PARTIAL
- Route order vs fact sheet: PARTIAL
- Station/rail logic: FAIL
- Visual style: PASS as illustration reference

## Reject reasons
1. Multiple train depictions and a long rail corridor visually suggest rail running along the scenic/urban route rather than one central Lidui Park arrival/return node.
2. The three food/rest roles required by Scheme C (small snack, dessert/tea rest, formal meal) are not distinctly encoded.
3. The illustrated background invents detailed road, river and building geometry, creating false precision.
4. The scheme reads closer to a general classic route than a clearly food-and-old-city-weighted plan.

Verdict: REJECTED
RejectCode: STATION_LOGIC;FOOD_NODE_DIFFERENTIATION;GEOGRAPHY_HALLUCINATION;SCHEME_DIFFERENTIATION
NextAction: regenerate using an abstract three-zone scaffold and three clearly distinct unlabeled food/rest icons after the hydraulic core.