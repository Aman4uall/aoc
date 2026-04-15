# Phase 7: Export Targets

Phase 7 adds editable export targets without changing the diagram source of truth.

## Delivered Scope

- SVG remains the canonical rendered output for published diagrams.
- Draw.io export is now generated from the modular diagram artifacts rather than from ad hoc post-processing.
- BFD, PFD, and control diagrams now save `.drawio` files alongside their SVG sheets.
- Draw.io pages are generated per sheet.
- Module boundaries from sheet composition are preserved in the export.
- Equipment nodes and stream connectors are exported for BFD and PFD where node/edge artifacts exist.
- Control export currently preserves sheet/module structure and page geometry, with SVG remaining the richer rendered form.

## Export Policy

The architecture remains:

`semantics -> modules -> sheet composition -> rendered SVG / editable export`

Draw.io is an export target only. It must not become the primary semantic source, because that would reintroduce manual drift and mixed-detail inconsistencies.

## Current Limitations

- Draw.io exports currently prioritize clean editability and structure over exact path fidelity.
- Orthogonal connector geometry is preserved conceptually, but Draw.io may reroute connectors during manual editing.
- Control exports currently emphasize module/page composition more than fine-grained control-edge reconstruction.

## Next Phase Boundary

Phase 8 should deepen pipeline integration so these exports and acceptance artifacts are consistently treated as first-class outputs across inspect, publish, and report assembly paths.
