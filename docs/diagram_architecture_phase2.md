# Diagram Architecture Phase 2

## Objective

Freeze the canonical symbol system and per-level style policy so AoC renderers stop inventing shapes, labels, and line styles on the fly.

Phase 2 builds directly on Phase 1:

- Phase 1 froze the semantic, module, and sheet-composition layers
- Phase 1.5 added validation gates for mixed-detail and stitching errors
- Phase 2 freezes the visual vocabulary those layers are allowed to use

## Core Rule

The renderer does not choose the symbol family.

The renderer only:

- looks up a canonical symbol
- applies the level policy
- places labels using the frozen typography rules
- routes edges using the frozen edge-role styles

## New Typed Components

Implemented in [`aoc/models.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py):

- `DiagramSymbolShape`
- `DiagramLinePattern`
- `DiagramSymbolDefinition`
- `DiagramEdgeStyleRule`
- `DiagramLevelStylePolicy`
- `DiagramSymbolLibraryArtifact`

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `build_diagram_symbol_library()`

## Canonical Symbol Vocabulary

### BFD

Allowed:

- `bfd_process_block`

Forbidden:

- all equipment symbols
- all instrument bubbles
- all valve symbols

Meaning:

- section-level blocks only

### PFD

Allowed:

- `pfd_reactor`
- `pfd_column`
- `pfd_vessel`
- `pfd_exchanger`
- `pfd_pump`
- `pfd_tank`
- `pfd_terminal`

Forbidden:

- control-loop symbols
- instrument bubbles
- valve symbols

Meaning:

- equipment-level process understanding only

### Control

Allowed:

- `control_unit_ref`
- `control_loop`
- `control_instrument`

Forbidden:

- valve-heavy P&ID detail
- process piping as primary content

Meaning:

- loop structure, signals, and safeguards

### P&ID-lite

Allowed:

- `pid_unit`
- `pid_instrument`
- `pid_valve`

Meaning:

- isolated unit-cluster detail only

## Edge Style Policy

The edge role determines style, not the renderer.

Examples:

- process/product: solid dark line
- recycle/purge/vent/waste: dashed variants
- utility: dotted utility-colored line
- control signal: dashed signal-colored line
- safeguard: dotted safeguard-colored line

## Typography And Readability Rules

Per-level policies now freeze:

- allowed symbols
- forbidden entity kinds
- allowed edge roles
- title font size
- primary and secondary label sizes
- minimum text size
- minimum node spacing
- minimum label clearance
- orthogonal-only routing requirement

These are policy-level constraints, not renderer suggestions.

## Why This Helps

This removes a major source of inconsistency:

- the same equipment type will no longer change shape across sheets
- PFD renderers can no longer drift into P&ID detail
- control sheets can no longer become process sheets with extra arrows
- future stitchers can assume a stable bounding-box vocabulary

## Output Of Phase 2

AoC now has a canonical symbol contract that later phases can consume for:

- module rendering
- layout sizing
- sheet composition
- validation of allowed symbol usage

## Next Step

Phase 3 should refactor current diagram builders so they emit:

- semantic artifacts
- module artifacts
- sheet-composition artifacts

and then render from the Phase 1 + Phase 2 contracts instead of directly mixing semantics and SVG decisions.
