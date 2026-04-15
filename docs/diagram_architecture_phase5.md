# Diagram Architecture Phase 5

## Objective

Turn diagram cleanliness from an implicit visual preference into an explicit
acceptance contract backed by benchmark-oriented checks.

Phase 5 builds on the Phase 3 architecture and Phase 4 layout engine by adding:

- measurable cleanliness metrics
- acceptance thresholds
- curated benchmark cases
- regression coverage tied to representative plant patterns

## Scope Completed

Phase 5 is started and the first benchmark-acceptance milestone is complete:

- diagram acceptance artifacts now carry layout-quality metrics
- PFD acceptance now evaluates cleanliness, not only content presence
- curated benchmark cases now exercise the acceptance gate across multiple
  layout patterns

## What Changed

The PFD acceptance gate is no longer limited to:

- missing required nodes
- missing required edges
- obvious label formatting mistakes

It now also evaluates layout-level quality indicators derived from the rendered
sheet and composition artifacts.

## Acceptance Metrics

Implemented in [`aoc/models.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
and [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `benchmark_cleanliness_score`
- `node_overlap_count`
- `node_label_overlap_count`
- `crowded_sheet_count`
- `max_sheet_utilization_fraction`

These metrics are computed from:

- rendered node geometry
- rendered node-label geometry
- packed module placements
- sheet utilization pressure
- dense one-row packing patterns

## Pipeline Integration

Implemented in [`aoc/pipeline.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py):

The process-flow stage now passes:

- rendered PFD sheets
- module artifacts
- sheet composition artifacts

into `build_diagram_acceptance(...)`.

This means PFD acceptance is now informed by actual layout quality, not only by
flowsheet semantics.

## Curated Benchmark Set

Implemented in [`tests/test_diagram_architecture.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_diagram_architecture.py):

The current curated benchmark set covers:

- linear liquid train
- mixed-height reaction and recovery train
- wide exchanger-heavy purification train
- recycle-heavy reaction train
- utility-dense conditioned train

Each benchmark case runs through the real PFD path:

1. semantics
2. modules
3. sheet composition
4. rendered artifact
5. diagram acceptance

This gives AoC a benchmark-style cleanliness check without requiring the full
end-to-end project pipeline for every diagram regression.

## Current Acceptance Contract

For the current milestone, a benchmark-clean PFD should satisfy:

- no node overlaps
- no node-label overlaps
- no unacceptable crowded-sheet count
- acceptable sheet utilization
- a benchmark cleanliness score above the configured practical threshold used in
  the tests

When those conditions are not met, the current gate downgrades from
`complete` to `conditional`.

## Why This Matters

Before Phase 5, AoC could produce a semantically correct PFD that still felt
visually cramped.

After this milestone:

- layout quality is measured
- crowded diagrams can be flagged automatically
- curated patterns help prevent regressions in different layout regimes

This is the first point where “clean enough for benchmark-style review” is
represented directly in the acceptance artifact.

## Completion Boundary

Phase 5 is not fully complete yet.

The current milestone covers:

- first-pass benchmark cleanliness metrics
- first curated benchmark family
- acceptance integration for PFD

The next milestone should expand this into a stronger benchmark acceptance
framework with:

- more benchmark patterns
- optional control-diagram cleanliness gates
- richer threshold tuning from observed benchmark outputs
- possible publishing/report surfacing of cleanliness status

## Next Step

The next sensible Phase 5 follow-up is to surface the cleanliness metrics in the
published diagram acceptance chapter or inspect output, so benchmark acceptance
is visible to users and not only enforced in tests.
