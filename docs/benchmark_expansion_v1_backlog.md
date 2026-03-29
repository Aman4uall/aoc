# Benchmark Expansion v1

## Objective
Turn Stage 8.6 into a measurable acceptance matrix instead of a loose benchmark list.

## Acceptance Matrix
- `ethylene_glycol`
  - status: complete
  - family: continuous liquid organic / hydration
- `acetic_acid`
  - status: complete
  - family: liquid organic / carbonylation
- `sulfuric_acid`
  - status: complete
  - family: inorganic absorption / energy recovery
- `sodium_bicarbonate`
  - status: complete
  - family: solids crystallization / filtration / drying
- `phenol`
  - status: complete
  - family: oxidation / recovery
- `para_nitroanisole`
  - status: blocked by design
  - family: specialty aromatic / sparse-data separation intensive
  - expected block stage: `property_gap_resolution`

## Completion Criteria
- Successful benchmarks complete the generic pipeline with approvals only at configured gates.
- Blocked specialty benchmarks fail honestly and expose the blocking stage in `inspect()`.
- Expanded successful coverage includes route and unit-operation families beyond the original four benchmark products.

## Status
- `Phase 8.6`: complete

## Notes
- `phenol` expands successful coverage into oxidation-led recovery service.
- `para_nitroanisole` remains the sparse-data honesty benchmark and should not be relaxed into a forced success case without stronger cited property coverage.
