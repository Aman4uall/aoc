# Diagram Architecture Phase 4

## Objective

Improve diagram cleanliness at the layout level after Phase 3 established the
semantic -> module -> sheet composition -> render architecture.

Phase 4 focused on local readability rather than new artifact plumbing:

- cleaner module-local node placement
- cleaner intra-module routing
- cleaner label placement
- cleaner module packing on sheets

## Scope Completed

Phase 4 is complete for the current layout milestone:

- module-local layout engine upgraded
- edge label collision handling added
- intra-module routing made lane-aware
- node label layout made family-aware
- module sizing made label-aware
- sheet composition made density-aware

## What Changed

The PFD path now uses a more explicit readability model during layout.

Instead of treating each node as only its equipment silhouette, the layout
system now considers:

- node family
- label count
- label wrap footprint
- lane usage
- routing corridors
- obstacle regions created by rendered labels

This makes module layout less likely to create overlap-heavy diagrams that have
to be cosmetically patched later.

## Layout Improvements

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `_layout_module_nodes(...)`
- `_module_lane_x_positions(...)`
- `_module_node_spacing(...)`
- `_estimate_pfd_module_footprint(...)`
- `_node_layout_footprint(...)`

These changes introduced:

- lane-based local node grouping
- module margin reservation for ports
- label-aware node spacing
- label-aware module footprint estimation
- placement of nodes inside effective footprint slots rather than raw symbol
  boxes only

## Routing Improvements

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `_build_pfd_sheet_route_hints(...)`
- `_pfd_route_points_within_module(...)`
- `_best_module_route(...)`
- `_candidate_module_corridors(...)`
- `_route_obstacle_score(...)`

These changes introduced:

- route hints for intra-module streams, not only inter-module connectors
- dedicated corridor behavior for utility, recycle, vent, waste, and purge
  traffic
- orthogonal route selection scored against label obstacle regions
- cleaner internal module routing before SVG rendering

## Label Improvements

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `_resolve_edge_label_position(...)`
- `_node_label_render_styles(...)`
- `_generic_label_policy(...)`
- `_node_label_bounds_for_rendering(...)`

These changes introduced:

- edge label placement that avoids equipment boxes
- edge label placement that avoids node label boxes
- edge label placement that avoids routed line segments when possible
- family-aware generic label policies for columns, vessels/reactors,
  exchangers, and rotating equipment
- packed non-overlapping label stacking for compact equipment

## Sheet Composition Improvements

Implemented in [`aoc/diagrams.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/diagrams.py):

- `build_process_flow_diagram_sheet_composition(...)`
- `_plan_pfd_sheet_module_chunks(...)`
- `_pack_pfd_modules_for_sheet(...)`

These changes introduced:

- footprint-aware module chunking
- row wrapping before sheets become visually crowded
- earlier sheet splitting for wide, dense module sets
- sheet sizing based on packed module geometry instead of mostly fixed canvas
  assumptions

## Validation And Test Coverage

Phase 4 added layout-focused regression coverage in
[`tests/test_diagram_architecture.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_diagram_architecture.py),
including checks for:

- nodes staying inside module bounds
- nodes staying non-overlapping inside modules
- edge labels avoiding equipment and node-label collisions
- local route hints staying orthogonal
- local routes avoiding label obstacles when possible
- generic node labels distributing vertically
- compact node labels staying non-overlapping
- family-aware label policy behavior
- module layout reacting to label-aware footprints
- dense sheet composition wrapping or splitting wide modules

## Completion Boundary

Phase 4 is considered complete because AoC now has a real layout-quality layer
on top of the Phase 3 architecture:

- local node layout is deterministic and lane-aware
- internal routing is obstacle-aware
- labels are treated as first-class layout geometry
- module size and sheet composition react to readability pressure

This is the first phase where “clean diagram” behavior is enforced by layout
structure rather than only by renderer heuristics.

## Next Step

The next sensible follow-up is Phase 5-style regression hardening and polish:

- SVG golden or visual regression coverage
- benchmark-case diagram acceptance thresholds
- final tuning for crowded benchmark plants
- optional export parity work once layout quality is stable
