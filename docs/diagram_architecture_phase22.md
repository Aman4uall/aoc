# Diagram Architecture Phase 22

## BAC P&ID Perfection Pass

Phase 22 strengthens BAC P&ID-lite coverage when the control plan is incomplete or uneven. The BAC diagram set should not lose critical local clusters just because only part of the plant has explicit control-loop detail.

## Implemented

- `build_pid_lite_semantics()` now accepts an optional BAC target profile.
- For BAC targets, P&ID-lite semantics now include required clusters for critical BAC units even when no explicit control loops are present.
- BAC sparse-cluster coverage now prioritizes units from:
  - reaction
  - cleanup
  - purification
  - storage
  - waste treatment
- BAC sparse clusters still include:
  - unit anchor
  - local process-line valves from attached streams
  - default relief/safeguard coverage for key pressure-holding units
- Added `validate_bac_pid_cluster_coverage()` to block missing BAC unit clusters and warn for missing relief coverage.
- Added regression tests for BAC sparse-cluster generation and validation.

## Outcome

BAC P&ID-lite is now more robust when the control-plan data is partial. Critical BAC equipment clusters can still appear as isolated local sheets instead of disappearing entirely from the P&ID-lite package.

## Next BAC Targets

- Tighten BAC P&ID-lite sheet titles, loop tagging, and line-class naming.
- Add BAC SVG regression fixtures for the main P&ID-lite sheets.
- Add BAC-specific expectations for purification, storage, and relief-device callouts.
