# Diagram Architecture Phase 1

## Objective

Freeze a strict intermediate schema for chemical-plant diagrams so AoC can generate clean diagrams without mixing BFD, PFD, control, and P&ID-lite concerns in one renderer pass.

The Phase 1 contract is intentionally additive. It does not replace the current `DiagramNode` / `DiagramEdge` / `DiagramSheet` rendering artifacts yet. Instead, it introduces an upstream semantic and module layer that later phases can render and stitch deterministically.

## Problem Statement

The current diagram architecture is strongly presentation-oriented:

- `DiagramNode`
- `DiagramEdge`
- `DiagramSheet`
- final SVG sheet generation

That makes it easy for rendering logic to mix detail levels too early. The result is inconsistent symbol vocabulary, unstable layouts, and PFD/P&ID contamination on the same sheet.

## Design Principle

The architecture must follow this sequence:

`plant semantics -> diagram modules -> sheet composition -> rendered output`

It must not follow this sequence:

`mixed semantic inference + full-sheet drawing in one pass`

## Frozen Diagram Taxonomy

### BFD

- Section-level blocks only
- No equipment-level symbols
- No instrument bubbles
- Only major process direction and major recycle/vent/waste indications

### PFD

- Equipment-level process units
- Major process streams
- Major utility hookups when materially needed for understanding
- No control-loop bubbles
- No valve-level P&ID clutter

### Control

- Control loops, sensors, actuators, signals, and safeguard linkages
- May reference process units abstractly
- Must not become a second PFD

### P&ID-lite

- Unit-cluster-level instruments, valves, interlocks, and safeguards
- Still simplified compared with drafting-grade industrial P&IDs
- Must remain isolated from the main PFD renderer

## New Model Layers

### 1. Plant semantics

Implemented by:

- `PlantDiagramEntity`
- `PlantDiagramConnection`
- `PlantDiagramSemanticsArtifact`

Responsibilities:

- capture meaning, not layout
- assign every entity a diagram level
- preserve section ownership and preferred module ownership
- preserve stream/control identities without deciding geometry

### 2. Diagram module spec

Implemented by:

- `DiagramModulePort`
- `DiagramModuleConstraint`
- `DiagramModuleSpec`
- `DiagramModuleArtifact`

Responsibilities:

- define one clean diagram slice at a time
- freeze symbol policy per module
- freeze allowed edge roles per module
- define boundary ports for later stitching
- prevent illegal entity kinds from entering a module

### 3. Sheet composition

Implemented by:

- `DiagramModulePlacement`
- `DiagramInterModuleConnector`
- `DiagramSheetComposition`
- `DiagramSheetCompositionArtifact`

Responsibilities:

- place already-clean modules on sheets
- connect boundary ports between modules
- decide sheet-level continuation markers
- avoid overlap without redrawing module internals

## Key Invariants

These are the Phase 1 schema rules that later builders and validators must enforce:

1. Every entity belongs to exactly one primary `diagram_level`.
2. Every connection references valid source and target entities.
3. PFD modules must not include `instrument`, `valve`, or `control_loop` entity kinds.
4. Control modules must not use `process_only` symbol policy.
5. BFD modules must use `block_only` symbol policy.
6. P&ID-lite content must be isolated into `pid_lite` modules and sheets.
7. Inter-module connectors may connect only declared boundary ports.
8. Stitching may place modules and connectors, but it may not invent units, streams, or symbols.

## Why This Structure Matters

This model prevents the stitcher from making semantic decisions and prevents the renderer from deciding scope on the fly.

That is the core fix for current cleanliness issues:

- local modules can be made clean independently
- final sheets are composed structurally
- mixed-detail diagrams become invalid by schema and later by validation

## Planned Next Steps

Phase 2 will define the canonical symbol system and style rules per diagram level.

Phase 3 will refactor existing builders to emit:

- semantic artifacts
- module artifacts
- composition artifacts

before producing final SVG output.
