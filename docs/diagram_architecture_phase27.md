# Diagram Architecture Phase 27

Phase 27 adds a review and approval workflow to the BAC drawing package so the generated diagrams can be tracked as controlled engineering drawings rather than only exported artifacts.

## Implemented

- Added review metadata to [aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py):
  - `checked_by`
  - `reviewed_by`
  - `approved_by`
  - `approved_date`
- Extended the BAC package/register models with:
  - per-sheet review fields
  - package-level `review_workflow_status`
  - `revision_history`
  - package-level checker / reviewer / approver fields
- Added `apply_diagram_review_workflow_metadata()` in [aoc/diagrams.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py).
- Extended `build_bac_drawing_package_artifact()` in [aoc/diagrams.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py) so it derives package review state from the actual sheet issue statuses.
- Added `validate_bac_drawing_package_artifact()` in [aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py) to catch:
  - approved/as-built packages without approvers
  - approved/as-built sheets without approvers
  - as-built sheets without approval dates
  - incomplete register-kind coverage

## Result

- BAC drawing packages can now represent Draft, For Review, Approved, and As Built workflow states.
- Review-chain metadata is now carried from the sheet level into the package register.
- The validator layer prevents silent promotion of BAC drawing packages into approved states without the required metadata.

## Validation

- `python3 -m py_compile aoc/models.py aoc/diagrams.py aoc/validators.py tests/test_diagram_architecture.py tests/test_validators.py`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators`
- `python3 -m unittest tests.test_diagram_architecture tests.test_validators tests.test_pipeline`
