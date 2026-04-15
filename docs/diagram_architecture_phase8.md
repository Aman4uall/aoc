# Phase 8: First-Class Pipeline Integration

Phase 8 makes diagram outputs visible and durable across the normal AoC pipeline, not just inside diagram-specific stages.

## Delivered Scope

- `inspect()` now reports a dedicated `diagram_exports` section.
- Export visibility includes:
  - BFD SVG sheet count
  - PFD SVG sheet count
  - control SVG sheet count
  - generated Draw.io filenames
- `FinalReport` now stores:
  - `diagram_svg_paths`
  - `diagram_drawio_paths`
- Diagram exports are therefore treated as first-class final-report outputs rather than opaque side files.

## Why This Matters

By Phase 7, the pipeline could generate SVG and Draw.io exports, but those outputs were still mostly “hidden implementation details.” Phase 8 promotes them into the same output contract as the other report artifacts, which improves:

- inspectability
- traceability
- downstream publishing consistency
- future export/publish automation

## Current Boundary

Phase 8 does not yet build a dedicated report appendix or manifest chapter for diagram artifacts. It instead ensures the pipeline’s persistent artifacts and final report metadata recognize those outputs explicitly.

## Next Phase Boundary

Phase 9 should expand regression and benchmark coverage so diagram quality and export stability are protected across a broader range of plant patterns and failure cases.
