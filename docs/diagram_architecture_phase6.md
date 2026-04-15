# Phase 6: Hard Diagram Quality Gates

Phase 6 converts diagram cleanliness from an informative benchmark into a release-control signal.

## Delivered Scope

- `DiagramAcceptanceArtifact` now records both `warning_issue_codes` and `blocking_issue_codes`.
- `build_diagram_acceptance(...)` can now emit `complete`, `conditional`, or `blocked`.
- Severe PFD failures now block on hard readability conditions:
  - overlapping equipment nodes
  - excessive label overlap
  - extreme sheet utilization
  - very low cleanliness score
- BFD topology omissions now block because they indicate a structurally incomplete high-level diagram.
- Pipeline stages now convert blocked diagram acceptance into real `ValidationIssue` blockers.
- `inspect()` now surfaces diagram blocking issue codes so failures are visible without opening the raw artifact.

## Phase 6 Policy

The acceptance policy now follows this hierarchy:

1. `complete`
   The diagram passes required topology and readability checks.
2. `conditional`
   The diagram is usable but has quality concerns that should be reviewed.
3. `blocked`
   The diagram is not fit for release and must not silently pass downstream.

## Current Blocking Intent

Phase 6 is intentionally strict on visual collisions and extreme density, but not yet strict on every missing outlet edge in mock or sparse-data scenarios. Those remain conditional unless the topology loss becomes severe enough to indicate a structurally incomplete diagram.

## Next Phase Boundary

Phase 7 should focus on export and editing targets, with SVG retained as the source-of-truth render and optional Draw.io export added on top of the new acceptance-controlled architecture.
