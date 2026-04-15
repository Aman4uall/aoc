# Diagram Architecture Phase 24

Phase 24 improves BAC Draw.io export fidelity so stitched BAC sheets remain editable, traceable, and structurally stable after regeneration.

## Implemented

- Added stable Draw.io cell identifiers based on sheet and object identity instead of transient page counters.
- Added editable Draw.io layer groups for BAC exports:
  - `Equipment Layer`
  - `Streams Layer`
  - `Annotations Layer`
- Assigned BAC process units to the equipment layer, stream connectors to the streams layer, and module boxes / legends / title blocks / stitch annotations to the annotations layer.
- Added Draw.io stitch-panel annotation cells that carry:
  - the BAC panel title
  - `Continues from` references
  - `Continues to` references
- Preserved existing generic Draw.io behavior for non-BAC exports to avoid disturbing earlier regression signatures.

## Result

- BAC Draw.io pages are easier to edit manually because major content classes are separated more intentionally.
- Regenerated BAC diagrams now keep more stable object identity, which is better for comparison and downstream cleanup.
- BAC stitched sheet context is visible inside the editable Draw.io document instead of living only in SVG or external naming.

## Validation

- `python3 -m py_compile aoc/diagrams.py tests/test_diagram_architecture.py`
- `python3 -m unittest tests.test_diagram_architecture`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators tests.test_pipeline`
