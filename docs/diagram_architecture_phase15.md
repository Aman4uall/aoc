## Phase 15: Equipment Template Library

Phase 15 starts by introducing a reusable equipment template layer behind the modular diagram architecture.

### What Phase 15 Adds

- a first-class equipment template artifact:
  - `diagram_equipment_templates`
- reusable family templates for:
  - reactor
  - column
  - vessel
  - heat exchanger
  - pump
  - tank
  - terminal
- per-template default port-side definitions for:
  - process inlet/outlet
  - vent / drain
  - utility and safeguard anchors where relevant

### Current Integration

The current Phase 15 slices now feed template data into:

- PFD semantic symbol selection
- PFD entity template metadata
- PFD module boundary-port side selection
- PFD module boundary-port role selection
- PFD node sizing defaults
- rendered PFD node notes and edge port-role metadata
- rendered PFD connection origins for family-specific ports like column overhead/bottoms and exchanger utility taps
- template-aware PFD module boundary spacing
- template-aware SVG overlays for visible family-specific nozzles and utility taps
- Draw.io anchor geometry for template-aware PFD exports
- shared node-family classification for downstream layout/rendering
- P&ID-lite unit template metadata
- P&ID-lite family-aware rendered unit geometry

### Why This Matters

Before this step, equipment family and port behavior were spread across multiple local heuristics.

Now we have:

- a reusable template contract
- one place to extend equipment defaults
- better consistency between semantics, ports, layout, and rendering

### Boundary After This Step

Phase 15 still does **not** yet include:

- nozzle-level equipment templates
- domain-specific template packs
- fully template-driven control-sheet geometry
- deeper per-equipment SVG families beyond the current template-aware overlays

Those are the next natural Phase 15 follow-up steps.
