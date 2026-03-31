# Phase D: Equipment-Wide Sizing Parity

Status: complete

Why this phase had looked missed:
- the main-equipment sizing logic was built incrementally during Phase C and later parity work
- that meant reactor, main separation, exchanger, storage, and several package-level sections already existed
- but the phase was never isolated as its own benchmark-parity track, so rotating and auxiliary families were not clearly treated as first-class completion criteria

What Phase D covers:
- equipment-wide sizing coverage beyond only the main reactor and main separation unit
- chapter-level treatment for storage, thermal-service, rotating, and auxiliary equipment families
- appendix-grade datasheet coverage across the same equipment families
- report-parity markers that make missing equipment-family coverage visible

Delivered:
- `equipment_design_sizing` now includes:
  - `Storage and Inventory Vessel Basis`
  - `Major Process Equipment Basis`
  - `Heat Exchanger and Thermal-Service Basis`
  - `Rotating and Auxiliary Package Basis`
  - `Utility-Coupled Package Inventory`
  - `Datasheet Coverage Matrix`
  - `Equipment-by-Equipment Sizing Summary`
- the datasheet bundle now includes:
  - storage-specific derivation basis
  - dedicated transfer-pump datasheet coverage
  - package-level derivation basis for thermal and auxiliary service items
- report parity now checks the Phase D equipment-family chapter markers directly

Acceptance reached:
- the equipment sizing chapter is no longer centered only on the main reactor/column pair
- storage, heat-exchanger/thermal-service, rotating, and auxiliary package families now have explicit chapter coverage
- datasheet output includes the missing rotating-equipment family through the transfer-pump path
- Phase D is now a formally tracked and closed benchmark-parity phase
