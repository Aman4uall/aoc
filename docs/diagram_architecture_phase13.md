## Phase 13: Advanced Control Diagram Expansion

Phase 13 extends the control-diagram family beyond the supervisory architecture and overlay sheets.

The first delivered slice adds a dedicated interlock and permissive view built from the existing control-plan fields, so loop startup, shutdown, override, and safeguard logic are visible as a structured control artifact rather than only as table text in the report body.

### What Phase 13 Adds

- a third control sheet: `Interlocks and Permissives`
- composition support for interlock/permissive sheet placement
- rendered loop cards for:
  - startup permissives
  - shutdown actions
  - override / interlock logic
  - safeguard linkage emphasis through criticality styling
- a cause-and-effect style matrix layout with explicit columns for:
  - cause / permissive
  - action / shutdown
  - override
  - safeguard / trip
- a fourth control sheet: `Shutdowns and Protective Trips`
- a focused shutdown review layout that isolates:
  - trip cause
  - shutdown action
  - protected final action

The current matrix now distinguishes normal operator override logic from protective safeguard and trip behavior, so shutdown/interlock content is not visually mixed with ordinary control overrides.

The editable Draw.io export now also carries review-context blocks for:

- `Interlocks and Permissives`
- `Shutdowns and Protective Trips`

so these control-review views are preserved as reviewable/exported pages rather than only report SVG sheets.

The Draw.io export now also carries editable per-loop review rows on those pages, including cause/effect and shutdown-trip content drawn from the control plan itself rather than only page-level guidance.

Phase 13 now also has a first-class structured review artifact, `control_cause_effect`, so the review sheets and editable control pages are backed by persisted cause/effect rows instead of only renderer-local formatting logic.

### Current Sheet Set

Control output now includes:

- `Process Control Architecture`
- `Instrumented Process Flow Overlay`
- `Interlocks and Permissives`
- `Shutdowns and Protective Trips`

### Logic Source

The new sheet is driven from the existing `ControlLoop` fields:

- `startup_logic`
- `shutdown_logic`
- `override_logic`
- `safeguard_linkage`
- `criticality`

This keeps the Phase 13 expansion aligned with the existing control-plan artifact instead of introducing an unrelated parallel schema.

### Boundary After This Step

This first Phase 13 slice still does **not** include:

- full permissive cause-and-effect matrices
- shutdown-sequence timing diagrams
- explicit ESD/SIS hierarchy sheets
- logic-gate style trip voting diagrams
- full Draw.io-specific control logic geometry

Those remain later Phase 13 follow-up work.
