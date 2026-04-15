# Diagram Architecture Phase 21

## BAC PFD Perfection Pass

Phase 21 starts tightening BAC process-flow diagrams beyond the generic PFD quality bar. The goal is to make BAC PFD acceptance encode the higher cleanliness expectations needed for a report-grade benchmark diagram set.

## Implemented

- Added BAC-specific PFD acceptance warning thresholds on top of the generic PFD checks.
- BAC PFD now warns earlier for:
  - cleanliness score drift
  - route crossings
  - high sheet utilization
  - label-clearance problems
- Added BAC-specific blocking thresholds for:
  - severe cleanliness degradation
  - repeated route crossings
  - excessive sheet utilization
  - repeated label-clearance failures
- Acceptance markdown now reports route-crossing and routing-load metrics explicitly.
- Added BAC regression tests for:
  - a clean BAC PFD sheet that remains `complete`
  - a marginal-density BAC PFD sheet that becomes `conditional` under BAC-specific gates

## Outcome

BAC PFD is now judged by a stricter standard than the generic process-flow path. This gives us a real benchmark discipline for BAC instead of treating it as just another acceptable PFD.

## Next BAC Targets

- Add BAC-specific SVG regression signatures for the main PFD sheets.
- Tighten BAC route fixtures and continuation-marker placement.
- Add exact expected BAC stream-callout checks on the main rendered sheets.
- Continue to Phase 22 for BAC P&ID perfection.
