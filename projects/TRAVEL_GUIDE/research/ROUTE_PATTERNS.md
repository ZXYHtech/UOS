# Dujiangyan One-Day Route Patterns — planning synthesis V1

## Design objective

Build five materially different one-day plans for a first-time visitor while keeping the paid Dujiangyan hydraulic heritage core, Guanxian old-city atmosphere, local food, moderate walking and realistic rail buffers.

This public file intentionally uses relative dayparts and durations rather than the travelers' exact private date/timing.

## Spatial backbone

For central one-day planning, the practical backbone is:

**Xipu rail -> Lidui Park-side central cluster -> Dujiangyan Scenic Area hydraulic core -> Guanxian Ancient City / Nanqiao cluster -> rail return**.

Dujiangyan railway station remains an alternate arrival/departure node when its timetable meaningfully improves return resilience. It must not be confused with Lidui Park station.

## Pattern A — Balanced classic first-timer

**Emphasis:** strongest first visit with low planning complexity.

Sequence concept:

1. early rail arrival via the most convenient central station;
2. enter the paid scenic area before the main weekend peak;
3. visit Fish Mouth, Feishayan and Baopingkou with short engineering explanations;
4. include Anlan Bridge / cultural node only if walking and crowd conditions remain comfortable;
5. exit toward the old-city / Nanqiao side;
6. one seated formal meal;
7. small old-city food/dessert tasting;
8. evening riverfront atmosphere;
9. return by the station with the best verified late timetable.

**Walking:** medium, target roughly 13k-16k steps depending on internal route and whether hillside nodes are included.

**Best for:** a first-time visitor who wants '都江堰该看的都看到' without turning the day into a checklist.

## Pattern B — History / culture depth

**Emphasis:** understanding the irrigation system and Li Bing tradition.

Compared with A:

- spend longer at the three hydraulic works;
- preserve time for Erwang Temple / Anlan Bridge or another verified interpretive cultural node;
- reduce snack hopping and commercial old-city wandering;
- formal meal remains, but food is secondary to interpretation.

**Walking/elevation:** medium-high if temple/hillside elements are used. The final scheme must state the extra climb rather than hiding it inside a generic step count.

**Risk:** can become tiring or overly 'lecture-like' unless explanations are concise and paired with observation/rest.

## Pattern C — Food + Guanxian old-city atmosphere

**Emphasis:** hydraulic core + living-city experience.

Compared with A:

- use the scenic-area core efficiently rather than maximizing every internal node;
- leave more time for Guanxian Ancient City / Yangliu River Street / Nanqiao-adjacent streets;
- plan one small savory tasting, one dessert/rest stop and one proper seated meal;
- allow unstructured street wandering rather than moving between too many named shops.

**Walking:** medium and more urban-flat after the scenic section.

**Risk:** tourist retail can dilute the 'local' feeling. Final food pins must be current and chosen for actual food quality/route convenience, not simply famous names from old lists.

## Pattern D — Relaxed comfort / conversation-first

**Emphasis:** least rushed, strongest rest quality.

Compared with A:

- keep only the highest-value scenic sequence;
- avoid optional hill climbing unless both travelers actively want it;
- schedule longer seated meal and at least one quiet drink/dessert pause;
- keep old-city/Nanqiao as a slow evening transition rather than a list of attractions;
- accept seeing fewer named points in exchange for lower fatigue.

**Walking:** medium-low to medium, nominally around 11k-14k steps; the public 15k target is a ceiling-like planning guide, not a quota.

**Best for:** maintaining energy and conversation quality over a full day.

## Pattern E — Weather / crowd resilient

**Emphasis:** ability to reshuffle the day.

Structure:

- preserve a core scenic-area window but do not bind the entire day to one exact internal sequence;
- keep a flexible formal-meal/rest block that can move earlier if rain/heat/crowding increases;
- maintain both Lidui Park and Dujiangyan-station return options until the final ticket check;
- use old-city covered/seated nodes as buffers;
- skip optional photo queues, steep nodes or night-tour ticket if conditions are poor.

**Walking:** variable, with explicit cut points.

**Best for:** forecast uncertainty, weekend crowd spikes or temporary access changes.

## Route rules shared by all five schemes

1. Do not combine Qingcheng Mountain, Panda Valley or other remote attractions into this one-day project; they undermine the first-time culture/food/comfort objective.
2. Enter the hydraulic heritage portion early when practical.
3. Interpret Fish Mouth / Feishayan / Baopingkou as one system, not isolated checkboxes.
4. Do not make a single photo platform or the blue-light river effect a critical dependency.
5. Keep at least one proper seated meal and one smaller rest opportunity.
6. Preserve rail/transfer buffer; do not plan to reach the return platform at the last possible minute.
7. Every final scheme needs a clear 'cut here if tired/raining/crowded' instruction.
8. Exact entrance/exit, internal walking links and meal pins must be validated in the scheme-specific map fact sheet before AI image generation.

## Map-generation implication

Each final scheme will receive a separate `MAP_FACT_SHEET` containing verified ordered stops and connections. Only after that will UOS generate a scheme-specific image prompt and route image, then inspect the image against the fact sheet and issue a VERIFIED/REJECTED receipt.

## Inputs

This synthesis uses the project's current geography/transit, history/culture, visitor-review, food, news and map-base research files. Dynamic train, weather, ticket and access facts remain subject to the T-minus-1 refresh.