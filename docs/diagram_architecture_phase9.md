# Phase 9: Regression and Benchmark Expansion

Phase 9 broadens the protection around the new diagram architecture so stability does not depend on a small number of happy-path tests.

## Delivered Scope

- Added a Draw.io regression signature fixture for the representative PFD export.
- Added a Draw.io regression test that freezes page/module/edge structure for the exported PFD document.
- Added a multi-sheet PFD stress benchmark that verifies:
  - the composition layer splits wide process trains across multiple sheets
  - the rendered artifact emits multiple sheets
  - the Draw.io exporter emits multiple diagram pages from that composition
- Preserved the rule that stress layouts may be `conditional` but should not silently collapse into blocked or single-sheet regressions unless a true quality failure occurs.

## Why This Matters

Earlier phases protected:

- semantic correctness
- module composition
- SVG output structure
- cleanliness scoring
- export generation

Phase 9 extends that protection into broader topology and export-stability space, especially where layout density and multi-sheet composition can regress subtly.

## Current Coverage Shape

The regression surface now includes:

- SVG signature coverage
- Draw.io signature coverage
- curated benchmark PFD patterns
- blocked-quality edge cases
- multi-sheet stress behavior

## Next Phase Boundary

Phase 10 should focus on rollout and operationalization:

- making the modular path the default long-term rendering contract
- documenting migration away from legacy assumptions
- tightening any remaining publish/report workflows that still assume older direct-render behavior
