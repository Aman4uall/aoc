# Flowsheet Solver v2 Backlog

This backlog breaks the solver upgrade into concrete slices that keep the current pipeline runnable while moving the core from family-shaped stream assembly toward a reusable plant-solving engine.

## Scope

Primary objective:
- make the material and convergence core generic enough that multiple chemistry families use the same solver path

Guardrails:
- keep the existing `StreamTable`, `FlowsheetCase`, and `SolveResult` contracts stable enough for the current pipeline
- do not bypass evidence lock, India-only economics rules, or chapter gates
- block weakly solved flowsheets instead of writing around missing engineering state

## Milestone Order

### M1. Separation and Recycle Packets

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)

Artifacts:
- `SeparationPacket`
- `RecyclePacket`
- `SeparationSpec`
- `RecycleLoop`
- `SolveResult.separation_status`
- `SolveResult.recycle_status`

Acceptance:
- component split fractions are explicit for product, waste, and recycle outlets
- recycle loops carry per-component convergence error
- the flowsheet critic blocks weak separation closure and bad recycle convergence

### M2. Unitwise Sensitivity and Packet Coverage

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)

Artifacts:
- `UnitOperationPacket.notes`
- `UnitSpec.unresolved_sensitivities`
- richer `CriticVerdict` links from solver state

Acceptance:
- each solved unit can expose unresolved basis issues independently
- missing inlet, outlet, or recycle destinations block at the unit level
- `inspect()` can show blocked units without reading raw JSON artifacts

### M3. Phase Split and Separator Models

Status:
- implemented

Modules:
- new: `aoc/solvers/separators.py`
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py)

Artifacts:
- `PhaseSplitSpec`
- `SeparatorPerformance`
- richer `SeparationPacket` phase-state fields

Acceptance:
- flash, distillation-like, absorption-like, crystallization, and filtration families use explicit separator logic
- dominant phase tracking is replaced by resolved outlet phase-state calculations where possible

### M4. Recycle and Purge Convergence Engine

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/convergence.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/convergence.py)
- new: `aoc/solvers/recycle_network.py`
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)

Artifacts:
- `RecycleLoop.max_iterations`
- `RecycleLoop.component_convergence_error_pct`
- new `ConvergenceSummary`

Acceptance:
- multiple recycle loops can be solved independently
- purge policy is explicit per impurity family
- loop-level convergence reports are attached to the solved flowsheet

### M5. Unitwise Composition Propagation

Status:
- implemented

Modules:
- new: `aoc/solvers/composition.py`
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/energy.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/energy.py)

Artifacts:
- `StreamSpec.component_names`
- new `UnitCompositionState`
- new `CompositionClosure`

Acceptance:
- every major unit can report inlet and outlet composition state
- energy and equipment modules consume solved composition rather than route-only assumptions

### M6. Side-Reaction and Byproduct Closure

Status:
- implemented

Modules:
- new: `aoc/solvers/reaction_network.py`
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)

Artifacts:
- `ReactionExtentSet`
- `ByproductClosure`
- richer `ReactionSystem`

Acceptance:
- side-reaction assumptions are explicit
- unresolved byproduct closure blocks downstream separation and economics

### M7. Solver-Driven Report Integration

Status:
- planned

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)

Artifacts:
- `FlowsheetCase`
- `SolveResult`
- chapter annexures for unitwise closure and recycle/separation diagnostics

Acceptance:
- material balance and process description chapters are assembled from solved unit packets
- blocked solver artifacts stop report generation for dependent chapters

## Near-Term Test Matrix

Unit tests:
- component split closure on separation packets
- recycle component convergence thresholds
- blocked solve results when separation or recycle packets are inconsistent

Integration tests:
- distillation-heavy case emits explicit recycle and separation diagnostics
- solids case remains on the same sequence solver without liquid-only assumptions
- `inspect()` exposes solver state clearly enough for manual review

Benchmark rule:
- `ethylene_glycol` remains green after every slice
- at least one non-EG benchmark must pass through the same solver path before a slice is marked complete
