# Diagram Architecture Phase 23

Phase 23 adds BAC stitched sheet composition so large diagram sets behave like coordinated drawing packages instead of unrelated split pages.

## Implemented

- Added stitching metadata fields on diagram sheets and sheet compositions:
  - `stitch_panel_id`
  - `stitch_panel_title`
  - `stitch_prev_sheet_id`
  - `stitch_next_sheet_id`
- Added BAC-specific stitched PFD panel naming:
  - `BAC PFD Panel 1: Feed, Reaction, and Cleanup`
  - `BAC PFD Panel 2: Purification, Storage, and Offsites`
- Propagated stitched panel metadata from composition into rendered sheets.
- Updated BAC PFD continuation markers so cross-sheet references point to panel titles instead of opaque sheet ids.
- Added BAC P&ID stitched panel metadata and cross-sheet continuation markers derived from shared stream presence across isolated local clusters.
- Extended BAC SVG regression signatures to lock stitched panel naming and continuation rendering.

## Result

- BAC PFD sheets now read as a stitched multi-panel drawing set.
- BAC P&ID-lite sheets remain isolated and clean, while still showing where process continuity continues on adjacent BAC panels.
- Non-BAC generic PFD behavior keeps raw `sheet_n` continuation references for backward compatibility.

## Validation

- `python3 -m py_compile aoc/models.py aoc/diagrams.py tests/test_diagram_architecture.py`
- `python3 -m unittest tests.test_diagram_architecture`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators tests.test_pipeline`
