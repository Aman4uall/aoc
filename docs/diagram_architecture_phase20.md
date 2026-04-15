# Diagram Architecture Phase 20

## BAC BFD Perfection Pass

Phase 20 hardens the BAC block flow diagram into a fixed high-level process backbone. The BAC BFD now prioritizes stable presentation structure over incidental blueprint ordering.

## Implemented

- Added a locked BAC BFD section order:
  - feed preparation
  - reaction
  - cleanup
  - concentration
  - purification
  - storage
  - waste handling
- Added BAC-specific BFD display labels:
  - Feed Preparation
  - Quaternization Reaction
  - Primary Cleanup
  - Concentration
  - Purification
  - Product Storage
  - Waste Handling
- BAC BFD semantics now expand to the full BAC section spine and rebuild the main process-flow path in canonical left-to-right order.
- BAC rendered BFD nodes now follow the same locked section order and label set.
- Added BAC BFD validation to block:
  - wrong section order
  - missing required BAC BFD sections
  - incorrect BAC BFD section labels
- Extended BFD section canonicalization so plant wording like `tankage` still resolves into BAC storage.

## Outcome

BAC BFD is now much closer to a stable report-grade front-page process summary. Even if upstream blueprint wording varies, the BAC block flow diagram should present the same disciplined section backbone every time.

## Next BAC Targets

- Tighten BAC BFD edge labels and recycle naming.
- Add BAC BFD regression fixtures for exact SVG signature checks.
- Move to BAC PFD perfection with stricter BAC-specific cleanliness thresholds and routing fixtures.
