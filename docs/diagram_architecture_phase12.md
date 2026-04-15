## Phase 12: P&ID-lite Layout and Routing Upgrade

Phase 12 improves the quality of the rendered P&ID-lite sheets.

Phase 11 established the schema, validators, builders, renderer path, and pipeline wiring. Phase 12 begins making the local unit-cluster sheets look more like disciplined engineering diagrams rather than generic structured layouts.

### What Phase 12 Adds

- role-aware local attachment placement around the unit anchor
- nozzle-aware visual grouping for transmitters, indicators, controllers, control valves, and relief devices
- local route hints for P&ID-lite edges
- dense-side attachment fan-out for crowded clusters
- automatic split views for unit clusters that outgrow a single clean local sheet
- local legend discipline for line classes, loop tags, and symbol meaning on each P&ID-lite sheet
- separate corridor behavior for:
  - control signals
  - safeguards
  - process-line attachments

### Layout Improvements

The local cluster layout now places attached items by functional role instead of with one generic fallback pattern.

Current role groups:

- `measurement`
- `local_indication`
- `local_control`
- `final_control_element`
- `safeguard_relief`
- `process_line`

This gives a more stable local diagram grammar:

- measurement devices bias left of the unit
- indication and controller elements bias above the unit
- final control elements bias right of the unit
- relief devices bias upper-right
- process-line valves bias below the unit

### Routing Improvements

P&ID-lite rendering now uses a dedicated route-hint builder:

- control signals prefer upper corridors
- safeguards prefer higher isolated corridors
- process-line attachments prefer lower corridors

That keeps the local clusters more readable and avoids relying only on the generic elbow logic used for process sheets.

### Crowding Control

When several attachments land on the same side of a local unit cluster, Phase 12 now fans them into multiple lanes instead of stacking them into one congested strip.

Current behavior:

- left/right attachment groups can split into secondary columns
- top/bottom attachment groups can split into secondary rows
- dense transmitter and control-valve groups now distribute across both axes when needed
- when one unit cluster still exceeds the local readability budget, the module builder emits multiple P&ID-lite views that repeat the unit anchor and keep each loop group intact

### Local Legend Discipline

Each P&ID-lite sheet now carries a compact local legend that is derived from the actual rendered content on that sheet.

Current legend content:

- line classes used on the local sheet
- loop tags present on the local unit cluster
- symbol meaning for the visible local symbol families

This keeps sheet interpretation more consistent and reduces reliance on inline labels alone.

The same local legend discipline is now carried into the Draw.io export as editable legend content, so the exported sheets preserve line-class, loop-tag, and symbol context instead of depending only on the SVG rendering.

The Draw.io export also now preserves local attachment-side intent on P&ID-lite edges through side-aware edge geometry, so instrument, valve, and relief connections remain closer to their intended nozzle/port direction after export.

### Validation and Coverage

Phase 12 is protected by focused tests that verify:

- attachment placement follows functional role
- control and safeguard edges route above the local unit
- process-line edges route below the local unit

### Boundary After Phase 12

Phase 12 still does **not** include:

- true nozzle-side equipment templates
- full valve-on-line drafting semantics
- automatic instrument crowding resolution for very dense clusters
- full ISA-style bubble/loop notation
- drafting-grade line spec annotation

Those belong to later refinement phases.
