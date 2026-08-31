# QuickBoard Product & Implementation Specification

Status: Accepted implementation specification for `TASK_QUICKBOARD_SPEC_01`  
Project: `QUICKBOARD`  
Intent: `QUICKBOARD_INTENT_V1`

## 1. Product goal

QuickBoard is a small, polished, offline-capable personal Kanban board that opens directly in a modern browser. It proves that UOS can take an ordinary same-repository project from specification through implementation, documentation and review without relying on AI_book, a backend, a framework, a package manager or a CDN.

The primary experience is deliberately simple: open the page, see three columns, create a card, move it through the workflow, edit it, delete it, close the browser and later reopen the same board from local storage.

## 2. Screen structure

### Header

The top area contains:

- product name: **QuickBoard**;
- a short subtitle such as “A tiny offline task board”;
- a primary **New task** button;
- a compact live summary showing Todo / In Progress / Done counts.

The header must remain readable on narrow screens and may wrap vertically rather than forcing horizontal scrolling.

### Board

The main content contains exactly three workflow columns in this order:

1. `Todo` (`todo`)
2. `In Progress` (`in-progress`)
3. `Done` (`done`)

Each column contains:

- a semantic heading;
- the current card count;
- a card list;
- an empty-state message when no cards exist.

Desktop/tablet presentation should use three columns when space permits. On small screens the columns stack vertically in workflow order. The page must not require horizontal scrolling for normal content.

### Card

Each task card displays:

- title (required);
- optional description;
- current status;
- Edit action;
- Move action(s) or an accessible status selector;
- Delete action.

Cards should have clear visual separation, readable line length and visible keyboard focus states.

### Create / edit form

Create and edit use the same form UI. A native `<dialog>` is acceptable for the target modern-browser scope, provided the form remains keyboard usable.

Fields:

- **Title** — required, trimmed, maximum 120 characters;
- **Description** — optional, maximum 1000 characters;
- **Status** — one of Todo, In Progress, Done.

Actions:

- Save;
- Cancel.

Validation errors must be understandable in text and not indicated by color alone.

## 3. Card data model

The persisted board state is an array of plain objects:

```text
{
  id: string,
  title: string,
  description: string,
  status: "todo" | "in-progress" | "done",
  createdAt: ISO-8601 string,
  updatedAt: ISO-8601 string
}
```

Rules:

- `id` is generated locally and must be unique within the stored board;
- user-provided text is rendered with text-safe DOM APIs (`textContent`), never injected as HTML;
- unknown/invalid status values normalize to `todo` or the invalid record is discarded safely;
- timestamps are metadata and do not need to be prominently displayed in V1.

## 4. Required interactions

### Create

1. User activates **New task**.
2. Form opens with blank title/description and default status `todo`.
3. Save validates and creates the card.
4. State is persisted immediately.
5. Board and counts rerender.

### Edit

1. User activates Edit on a card.
2. Form is prefilled from that card.
3. Save updates title, description, status and `updatedAt` while preserving `id` and `createdAt`.
4. State is persisted and rerendered.

### Delete

Delete must require a lightweight confirmation (`confirm()` is sufficient for this pilot) so an accidental click does not immediately destroy a task. Confirmed deletion persists immediately.

### Move

Moving must not require drag-and-drop. V1 must provide an explicit keyboard-accessible mechanism, either:

- Previous / Next status buttons; or
- a labeled status `<select>` on each card.

Drag-and-drop may be added only as an enhancement; it cannot be the sole movement mechanism.

### Empty state

When a column contains no cards, show a short useful message such as “No tasks here yet.” It disappears automatically when cards are added.

## 5. Persistence

Storage backend: browser `localStorage` only.

Canonical key:

```text
quickboard.cards.v1
```

Persistence rules:

1. Load once during startup.
2. Parse inside `try/catch`.
3. If the key is absent, start with an empty array.
4. If JSON is malformed or the decoded value is not an array, fail safe to an empty board instead of breaking the UI.
5. Sanitize/normalize loaded records before rendering.
6. Save after every successful create, edit, move or delete.
7. No network request is needed for normal operation.

Storage is browser/profile/origin-local. The README must make clear that data is not synchronized across devices and clearing browser site data may remove it.

## 6. Accessibility minimum

QuickBoard V1 must include:

- semantic headings and buttons;
- explicit form labels;
- keyboard-operable create/edit/delete/move controls;
- visible `:focus-visible` indication;
- sufficient text/background contrast;
- status/count information available as text, not color alone;
- a polite live region or equivalent update for meaningful board changes where practical;
- a logical DOM/tab order matching the visible workflow;
- no interaction that requires a mouse or drag gesture.

Use `aria-*` only where native HTML semantics are insufficient.

## 7. Responsive behavior

Target widths:

- wide: three-column grid;
- medium: three columns may remain if readable, otherwise adapt to a two/one-column layout;
- narrow/mobile: one stacked column flow.

Minimum requirements:

- no clipped controls;
- touch targets remain comfortably usable;
- long titles/descriptions wrap;
- dialog/form fits within the viewport and can scroll internally when needed.

## 8. Visual direction

The interface should feel calm and modern rather than framework-demo-like:

- restrained neutral page surface;
- strong heading hierarchy;
- clearly distinct board columns;
- cards with subtle elevation/border;
- one consistent primary action treatment;
- status may use restrained visual accents, but meaning must remain understandable without color.

No external fonts, icon libraries, images, CSS frameworks or CDNs are permitted. System fonts and simple Unicode/text labels are sufficient.

## 9. Exact file plan

Implementation is intentionally zero-build and split by responsibility:

```text
projects/QUICKBOARD/
├── SPEC.md        # this specification
├── index.html     # semantic page shell, board containers, dialog/form
├── styles.css     # responsive layout and visual/accessibility states
├── app.js         # model, persistence, rendering and interactions
├── README.md      # user-facing run/usage/limitations/file guide
└── REVIEW.md      # final acceptance evidence
```

Responsibilities:

### `index.html`

- semantic landmarks and headings;
- header and summary placeholders;
- three named board columns;
- reusable create/edit dialog and form;
- links only local `styles.css` and `app.js`;
- no inline remote resources.

### `styles.css`

- tokens through CSS custom properties where useful;
- responsive board/grid behavior;
- cards, form/dialog, buttons and empty states;
- visible focus states;
- reduced-motion-friendly behavior (avoid unnecessary animation).

### `app.js`

- storage key and data normalization;
- CRUD operations;
- status movement;
- DOM-safe rendering;
- counts and empty states;
- dialog/form lifecycle;
- event handling;
- localStorage error tolerance.

### `README.md`

- purpose;
- how to open/run;
- features;
- persistence behavior and limitations;
- file structure;
- explicitly states there is no backend or cross-repository dependency.

### `REVIEW.md`

Final reviewer records pass/fail evidence for CRUD, movement, persistence, responsive behavior, keyboard/basic accessibility, documentation and zero external dependency.

## 10. Parallel implementation boundary

After this specification is completed, UOS may release these two tasks in parallel:

- `TASK_QUICKBOARD_UI_01` owns `index.html` and `styles.css`;
- `TASK_QUICKBOARD_LOGIC_01` owns `app.js`.

Both must implement against this specification and must not casually modify the other task's owned files. The shared contract between them is the following stable DOM vocabulary:

- board column lists use `data-column="todo|in-progress|done"`;
- column counts use `data-count="todo|in-progress|done"`;
- New task control uses `#new-task-button`;
- editor dialog uses `#task-dialog`;
- editor form uses `#task-form`;
- form fields use `#task-title`, `#task-description`, `#task-status`;
- hidden/edit identity may use `#task-id`;
- announcement region uses `#board-announcer`.

`app.js` may render card internals dynamically and should not depend on styling-only class names for logic.

## 11. Acceptance checklist for the specification task

- [x] Screen layout is defined.
- [x] Card data model is defined.
- [x] Create/edit/delete/move interactions are defined.
- [x] Persistence key and failure behavior are defined.
- [x] Accessibility minimum is defined.
- [x] Responsive behavior is defined.
- [x] Exact zero-dependency file plan is defined.
- [x] UI/logic parallel-work boundary and shared DOM contract are defined.
- [x] No AI_book or cross-repository dependency is introduced.
