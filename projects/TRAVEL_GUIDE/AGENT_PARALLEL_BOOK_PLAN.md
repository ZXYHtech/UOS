# TRAVEL_GUIDE — Book-Scale Multi-Agent Research Plan

Status: ACTIVE
Task ceiling: 48 work units (<= 50)
Output mode: book-scale searchable web + PDF + Google Drive delivery

## Parallel topology

Use 6 research agents in parallel plus 1 editor/integrator. The 48 work units remain the canonical task ceiling; parallelism changes execution order, not task count.

### AGENT-GEO — Geography / transport / map freshness
Work units: 01-08
Responsibilities:
- Chengdu–Xipu–Dujiangyan rail and station logic
- Dujiangyan Station vs Lidui Park Station
- 1号门 / 6号门 / QinYanLou access
- POI freshness, walking buffers, taxi transfer, return resilience
- AMap deep links and pre-trip validation
Acceptance: every actionable place has current locator, freshness note, and non-GIS disclaimer.

### AGENT-HISTORY — Hydraulic engineering / history / local culture
Work units: 09-18
Responsibilities:
- Li Bing, Yuzui, Feishayan, Baopingkou
- Erwang Temple, Fulong Temple, QinYanLou, Anlan Bridge
- annual maintenance, Water-Releasing Festival, heritage values
- myth-vs-fact separation and conversation-worthy interpretation
Acceptance: every core place has a >=500 Chinese-character article and source trail.

### AGENT-DATA — Visitor profile / volume / seasonality
Work units: 19-26
Responsibilities:
- annual visitors, holiday peaks, crowd-control evidence
- age/sex/origin/travel-party evidence
- purpose mix, family/research-tour signals, internationalization
- strict denominator/year/method labeling
Acceptance: no unsupported percentages; proxy data visibly labeled.

### AGENT-REVIEWS — Recent reviews / news / operating changes
Work units: 27-34
Responsibilities:
- 2024-2026 visitor review themes
- queues, fatigue, commercialization, photo points, nightscape
- 6号门 notices, traffic control, night-tour changes, weather risks
Acceptance: time-sensitive facts carry dates; reviews treated as biased samples, not statistics.

### AGENT-FOOD — Food / restaurant / budget
Work units: 35-40
Responsibilities:
- local foods, old-city snack strategy, current restaurant candidates
- opening hours, price bands, comfort, queue risk
- 2-person <=500 RMB cost model
Acceptance: merchant claims refreshed; restaurant is never a single point of failure.

### AGENT-EXPERIENCE — 5 schemes / conversation / gift / photography / fallback
Work units: 41-48
Responsibilities:
- A-E plans with genuinely different priorities
- hourly location-based topics and natural interaction design
- low-pressure gift timing, photography boundary, return conversation
- private relationship-specific content remains encrypted in canonical repo storage
Acceptance: no manipulative social scripts; every plan has cut points and return buffers.

### EDITOR-01 — Integrator / book editor
Runs after each agent deposits chapter content, but may continuously merge non-conflicting sections.
Responsibilities:
- deduplicate facts and terminology
- resolve station/entrance/map conflicts
- enforce source hierarchy and freshness
- build concise cards + long-form detail pages
- maintain global search index, tags, AMap links, update timestamps
- produce book-scale PDF and web edition
- upload final artifacts to Google Drive

## Book architecture

The final web/PDF should read like a compact travel book rather than a short itinerary:
1. How to use this book
2. Geography and the city-water relationship
3. Rail / local transport / station strategy
4. Understanding the three hydraulic cores
5. People, maintenance, ritual and living heritage
6. Scenic-area nodes and old-city nodes
7. Recent visitor reviews and common mistakes
8. Visitor volume, demographic evidence and seasonality
9. Food, restaurant and budget strategy
10. Five one-day plans
11. Conversation, gift, photography and relationship boundaries
12. Plan-B decision system and T-1 verification
13. AMap quick-reference atlas
14. Source notes / evidence boundaries

## Content-depth requirement

- Existing short web version remains available as `brief` view.
- Every major point/topic receives a long-form `detail` article, minimum 500 Chinese characters; target 1,200-2,000 Chinese characters for core nodes.
- Core locations (Yuzui, Feishayan, Baopingkou, Anlan Bridge, Erwang Temple, QinYanLou, 1号门, Dujiangyan Station, Lidui Park Station, Guanxian Old City, Nanqiao) each require their own long-form entry.
- Book target: at least 3x the previous research volume; recommended >= 80,000 Chinese characters excluding HTML/CSS/JS and source URLs.

## Web UX requirements

- top global search across title / summary / detail / tags / location / food / review / news / interaction
- category filters and chapter navigation
- brief card -> detail article modal/page
- every geolocatable entry gets AMap direct/open-search link
- freshness + evidence-level badges
- bottom document switch retained for A/B/C/D/E, Research, Interaction
- mobile-first layout

## Storage / privacy

- Public travel research, maps, history, reviews, food, traffic may be plaintext.
- Exact private relationship context, gift/private scripts, exact sensitive origin details remain encrypted in canonical repo storage.
- Decrypted private deliverables may be produced for the operator and uploaded only to the operator-requested Google Drive destination.

## Google Drive target

Folder: `都江堰一日游_深度调研版_2026-09-05`
Required final uploads:
- searchable web edition (`index.html` or ZIP)
- book-scale research PDF
- source/evidence appendix
- current five-plan guide package
- latest maps
