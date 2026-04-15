## Phase 11: P&ID-lite Foundation

Phase 11 begins the next major expansion after the modular BFD/PFD/control rollout: a proper P&ID-lite foundation.

The goal is not to jump directly to full industrial P&ID drafting. The goal is to give AoC a stricter local instrumentation-and-valving layer that can sit beside the PFD without contaminating it.

### What Phase 11 Adds

- richer P&ID-lite symbol vocabulary
- attachment-aware semantic fields
- line-class-aware P&ID-lite connections
- controller loop identifiers
- unit-cluster isolation rules
- stronger validators for P&ID-lite semantics and modules
- real P&ID-lite semantics, module, and sheet-composition builders

### Symbol-Library Expansion

The canonical diagram symbol library now includes a real P&ID-lite starter vocabulary:

- `pid_unit`
- `pid_indicator`
- `pid_transmitter`
- `pid_controller`
- `pid_manual_valve`
- `pid_control_valve`
- `pid_relief_valve`

This remains intentionally narrower than full ISA-style drafting, but it is enough to express the local instrumentation cluster around a unit operation.

### Semantic Additions

`PlantDiagramEntity` now carries additive P&ID-lite fields:

- `attached_to_entity_id`
- `attachment_role`
- `pid_function`
- `pid_loop_id`
- `line_class`

`PlantDiagramConnection` now also carries:

- `line_class`

These fields let the system capture:

- what instrument or valve is attached to
- what functional role it serves
- which local loop it belongs to
- what line class a process or utility line represents

### Validator Rules Added

Phase 11 introduces hard validation for the local P&ID-lite contract:

- P&ID-lite instruments and valves must declare attachments
- P&ID-lite instruments and valves must declare a `pid_function`
- P&ID-lite controllers must declare a `pid_loop_id`
- P&ID-lite process and utility lines must declare a `line_class`
- P&ID-lite material lines may not terminate directly on instrument entities
- P&ID-lite modules must be isolated local clusters
- P&ID-lite modules must include at least one unit anchor
- P&ID-lite attachments may not point outside the local module

### Boundary After Phase 11

Phase 11 is now a foundation-plus-builder phase.

It includes:

- `build_pid_lite_semantics(...)`
- `build_pid_lite_modules(...)`
- `build_pid_lite_sheet_composition(...)`
- `build_pid_lite_diagram(...)`

These produce isolated unit-cluster artifacts in the same architecture-first pattern used by BFD, PFD, and control.

The renderer path now produces:

- SVG P&ID-lite sheets
- Draw.io-exportable P&ID-lite sheets through the shared export path
- visible valve, controller, and instrument symbol rendering rather than generic placeholder boxes

It does **not** yet include:

- nozzle-aware valve placement
- loop-bubble placement around equipment
- full line-by-line ISA drafting behavior
- round-trip editable fidelity

Those belong to the next implementation phases.
