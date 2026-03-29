# Flowsheet Solver v3 Backlog

This backlog tracks the Stage 4 solver-core work that pushes the plant model beyond the earlier family-shaped sequence solver.

## Scope

Primary objective:
- make the solved flowsheet more graph-native, section-aware, and side-draw-aware without breaking the current pipeline contracts

Guardrails:
- keep `StreamTable`, `FlowsheetCase`, and `SolveResult` usable by the existing report and economics path
- surface blocked topology and continuity issues in critics instead of burying them in narrative text

## Stage 4 Slices

### V3.1 Sectioned Topology and Side Draws

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)

Artifacts:
- `FlowsheetSection`
- `StreamRecord.stream_role`
- `StreamRecord.section_id`
- `SeparationPacket.component_split_to_side_draw`
- `SolveResult.section_status`

Acceptance:
- the solved stream table exposes explicit section topology
- separator side draws are explicit artifacts, not hidden inside product or waste buckets
- critics can block broken section continuity independently of unit closure

### V3.2 Descriptor-Driven Sections and Topology-Aware Recycles

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/recycle_network.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/recycle_network.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/flowsheet.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/flowsheet.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)

Artifacts:
- descriptor-driven `FlowsheetSection` ordering
- topology-aware `RecyclePacket.recycle_target_unit_id`
- topology-aware `RecycleLoop.source_section_id` / `target_section_id`
- graph node `section_id`, `section_type`, `stream_roles`, `recycle_loop_ids`, `side_draw_stream_ids`

Acceptance:
- route separation descriptors can reorder active sections instead of always collapsing into one family-shaped blueprint
- cleanup and recycle-routing streams follow the expanded topology instead of one fixed feed-prep return assumption
- section-aware graph nodes and critics expose dynamic unit/section topology for EG, acetic acid, sulfuric acid, and solids benchmarks

## Next Stage 4 Priorities

1. Reduce remaining family shortcuts inside `build_generic_sequence_streams` so more route descriptors expand into distinct unit-op packets instead of sharing one generic separation branch.
2. Add side-cut and bleed routing policies that can create multiple purification or recovery subsections when the route descriptors imply staged cleanup.
3. Push topology-aware routing deeper into energy and equipment modules so unit duties and package sizing follow the descriptor-expanded section path directly.
