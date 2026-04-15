# Diagram Architecture Phase 3

## Objective

Refactor diagram generation so AoC emits structured pre-render artifacts before final SVG output.

Phase 3 began with the BFD path because it was the simplest diagram class and gave a low-risk migration pattern for the PFD and control paths that followed.

Phase 3 is now complete for the current migration target:

- BFD pre-render architecture
- PFD pre-render architecture
- control pre-render architecture
- partial renderer integration for all three families

## What Changed

The diagram pipeline now follows four explicit layers:

1. semantic meaning
2. module slices
3. sheet composition
4. final rendered SVG artifact

This keeps report output stable while replacing renderer-first generation with artifact-first generation.

## New Builders

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `build_block_flow_diagram_semantics(...)`
- `build_block_flow_diagram_modules(...)`
- `build_block_flow_diagram_sheet_composition(...)`
- `build_process_flow_diagram_semantics(...)`
- `build_process_flow_diagram_modules(...)`
- `build_process_flow_diagram_sheet_composition(...)`
- `build_control_system_semantics(...)`
- `build_control_system_modules(...)`
- `build_control_system_sheet_composition(...)`

## Pipeline Integration

Implemented in [`aoc/pipeline.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py):

The `block_diagram` stage now saves:

- `diagram_symbol_library`
- `block_flow_diagram_semantics`
- `block_flow_diagram_modules`
- `block_flow_diagram_sheet_composition`
- `block_flow_diagram_artifact`
- `block_flow_diagram_acceptance`

The material-balance / process-flow stage now saves:

- `diagram_symbol_library`
- `process_flow_diagram_semantics`
- `process_flow_diagram_modules`
- `process_flow_diagram_sheet_composition`
- `process_flow_diagram_artifact`
- `process_flow_diagram_acceptance`

The instrumentation/control stage now saves:

- `diagram_symbol_library`
- `control_system_semantics`
- `control_system_modules`
- `control_system_sheet_composition`
- `control_system_diagram_artifact`
- `control_architecture`
- `control_plan`

## Validation Integration

The migrated stages now validate:

- symbol library integrity
- semantics structure
- semantics against symbol policy
- module structure
- modules against symbol policy
- sheet composition integrity

This means the new pre-render architecture is not just generated, it is checked before the stage completes.

## Renderer Integration

Phase 3 no longer stops at artifact generation.

The final renderers now consume the new contracts in visible ways:

- BFD:
  deterministic section artifacts drive the final section-level diagram basis
- PFD:
  sheet assignment, section grouping, continuation markers, module boundaries, and inter-module routing now follow the semantic/module/composition artifacts
- control:
  sheet sizing, unit ordering, module boundaries, and overlay placement now follow the control semantic/module/composition artifacts

This is still an incremental renderer migration, not a full visual rewrite.

## Migration Strategy

Phase 3 intentionally keeps the existing SVG renderers in place for final output.

That means:

- no report regression from switching renderers too early
- new artifacts are available now for debugging and future rendering
- the legacy renderers can be replaced incrementally instead of all at once

## Completion Boundary

Phase 3 is considered complete because:

- all three major diagram families emit semantic artifacts
- all three major diagram families emit module artifacts
- all three major diagram families emit sheet-composition artifacts
- pipeline stages persist and validate those artifacts
- final PFD and control output now uses the new artifacts for real layout decisions

## Next Step

Phase 4 should focus on local module layout quality rather than more artifact plumbing:

- per-module layout engines
- cleaner intra-module routing
- reduced label collisions
- benchmark-grade visual polish
