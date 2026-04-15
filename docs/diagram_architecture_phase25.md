# Diagram Architecture Phase 25

Phase 25 adds a BAC diagram QA benchmark artifact so the BAC drawing package can be judged as one benchmark-ready set instead of only as separate diagram tests.

## Implemented

- Added `BACDiagramBenchmarkRow` and `BACDiagramBenchmarkArtifact` in [aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py).
- Added `build_bac_diagram_benchmark_artifact()` in [aoc/diagrams.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py).
- The benchmark artifact evaluates four BAC package rows:
  - BFD
  - PFD
  - P&ID-lite
  - Draw.io
- BAC benchmark rows now check for:
  - locked BAC BFD section labels
  - stitched BAC PFD panel titles and continuation markers
  - BAC PFD acceptance state
  - locked BAC P&ID titles and visible relief coverage
  - editable BAC Draw.io layers and stitch metadata
- Added `validate_bac_diagram_benchmark_artifact()` in [aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py) to turn benchmark drift into explicit blocked/warning validation issues.

## Result

- BAC diagram quality is now represented by one benchmark artifact instead of being spread only across separate regression tests.
- The system can now say whether the BAC diagram package is:
  - `complete`
  - `conditional`
  - `blocked`
- This gives us a stronger foundation for the next delivery/export phase because package readiness is now explicit.

## Validation

- `python3 -m py_compile aoc/models.py aoc/diagrams.py aoc/validators.py tests/test_diagram_architecture.py tests/test_validators.py`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators tests.test_pipeline`
