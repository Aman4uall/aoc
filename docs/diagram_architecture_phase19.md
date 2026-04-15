# Diagram Architecture Phase 19

## BAC Control And P&ID Boundary Cleanup

Phase 19 starts the BAC-first hardening track. The purpose of this phase is to stop BAC process-flow diagrams from drifting toward mixed PFD/P&ID/control notation.

## Implemented

- BAC PFD generation now suppresses visible loop-ID labels such as `TIC-101` on process equipment.
- BAC PFD generation now suppresses visible utility-duty callouts such as `+250 kW heat` on process equipment.
- Suppressed BAC control and utility context is retained in node notes metadata so it is still traceable for downstream control or P&ID views.
- Added `validate_bac_pfd_process_purity()` to block BAC PFD content that exposes:
  - control-loop annotations
  - utility-duty annotations
  - valve/controller/instrument symbol families that belong in P&ID-lite or control views
- Added BAC-specific regression tests for both generation and validation behavior.

## Outcome

BAC PFD now behaves more like a report-grade equipment flow diagram:

- major units stay visible
- process streams stay visible
- BAC-specific layout and stream callouts remain intact
- local instrumentation and control detail stay out of the PFD body

## Next BAC Targets

- Tighten BAC BFD section naming and section-order fixtures.
- Harden BAC PFD acceptance thresholds beyond the generic plant thresholds.
- Expand BAC P&ID-lite cluster coverage around reaction, purification, storage, and safeguards.
- Add BAC benchmark fixtures so perfect BAC outputs stay locked.
