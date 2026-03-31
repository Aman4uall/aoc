# Phase A: Report Parity Framework

Status: implemented

## Scope
- Define the benchmark report contract explicitly.
- Evaluate the generated report against that contract.
- Surface missing chapters, partial chapters, and missing support appendices without silently hiding the gap.

## Implemented
- `report_parity_framework` artifact built during `project_intake`
- `report_parity` artifact built during `final_report`
- chapter-contract coverage for the benchmark report structure
- support-contract coverage for:
  - references
  - Appendix A: Material Safety Data Sheet
  - Appendix B: Python Code
  - Appendix C: Process Design Data Sheet
- `inspect()` visibility for report parity status and missing support sections
- validator hooks:
  - missing benchmark chapter contracts block
  - missing benchmark report chapters block
  - remaining partial/missing support parity stays visible as warnings

## Acceptance
- A run produces a formal benchmark chapter contract.
- A completed run produces a report parity assessment.
- Missing benchmark chapters are treated as real blockers.
- Missing appendix/support parity is visible in the output instead of being hidden.

## Next
- Use the parity results to drive Phase B and later phases chapter-by-chapter.
