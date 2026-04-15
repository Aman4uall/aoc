# Diagram Architecture Phase 18

## Drafting Validation

Phase 18 makes the Phase 17 drafting layer enforceable. The system now checks whether generated plant diagram sheets are traceable, reviewable, and safe to export as controlled engineering drawings.

## Implemented

- Added drafting QA metrics to diagram acceptance artifacts:
  - Missing drafting metadata fields.
  - Duplicate drawing numbers.
  - Duplicate sheet numbers.
  - Rendered SVG sheets missing the drafting title block.
  - Equipment/node overlap with the reserved title-block area.
- Added acceptance warning codes for drafting metadata and title-block problems.
- Added blocking acceptance codes for duplicate drawing identity, missing SVG title blocks, and title-block overlap.
- Added `validate_diagram_drafting_sheets()` for reusable sheet-level drafting validation.
- Added regression tests for standalone validation and PFD acceptance blocking.

## Why This Matters

PFD, BFD, P&ID-lite, and control diagrams must not quietly become mixed or uncontrolled images. Phase 18 makes the drawing package fail loudly when a sheet cannot be traced, reviewed, or safely edited.

## Next Hardening Targets

- Reuse the same visible title-block renderer inside bespoke control SVG sheets.
- Add revision ledger integration for checker, approver, and approval-date fields.
- Validate Draw.io pages directly after export.
- Add automatic layout repair when the title block collides with equipment.
