## Phase 14: Routing and Connector Engine Upgrade

Phase 14 strengthens the routing layer behind the modular diagram architecture.

The first delivered slice promotes PFD route geometry from transient renderer state into a first-class persisted routing artifact.

### What Phase 14 Adds

- a persisted routing artifact for PFD output:
  - `process_flow_diagram_routing`
- structured route-hint models for:
  - routed edge geometry
  - label anchors
  - condition-label anchors
  - continuation markers
- PFD renderer support for consuming persisted routing instead of recomputing route hints ad hoc

### Current Scope

The current Phase 14 routing artifact covers:

- sheet-local orthogonal route points
- inter-module connector geometry
- intra-module routed paths
- continuation markers between sheets
- route crossing counts per sheet
- congested routing channel counts per sheet
- max routing channel load per sheet

This gives the routing layer a cleaner contract:

`semantics -> modules -> sheet composition -> routing -> rendered diagram`

### Why This Matters

Before this step, routing existed mostly as ephemeral helper output inside the PFD renderer path.

Now route geometry is:

- inspectable as its own artifact
- persistable in the pipeline
- reusable by later exporters and validators
- separable from the SVG renderer itself
- measurable for acceptance gating and cleanliness scoring

### Current Quality Gates

Phase 14 now feeds routing quality into PFD acceptance:

- orthogonal crossing counts reduce the cleanliness score
- congested routing channels reduce the cleanliness score
- severe routing congestion can block the final acceptance result
- routing metrics are stored per sheet for later export and review

### Current Optimization Pass

The routing stage now includes a deterministic post-pass for PFD route hints:

- candidate orthogonal corridor shifts are generated for eligible routes
- each candidate is scored against the whole sheet routing set
- lower-crossing and lower-congestion alternatives are preferred
- path length remains a secondary tie-breaker so routes do not wander unnecessarily

### Export Fidelity

Phase 14 now carries optimized route geometry into editable export:

- persisted route hints can be supplied to the Draw.io builder
- orthogonal internal waypoints are written into the exported edge geometry
- editable PFD, P&ID-lite, and control-overlay pages keep more of the optimized route shape instead of falling back to generic connectors

### Lane Reservation

Phase 14 now reserves connector corridors before optimization on dense PFD sheets:

- sibling inter-module connectors can be assigned distinct midline corridors
- top and bottom connector families can be fanned across reserved y-lanes
- the optimization pass now starts from a less congested initial routing state

### Boundary After This Step

The current Phase 14 slice still does **not** include:

- lane reservation conflict resolution across all diagram families

Those are the next natural Phase 14 follow-up steps.
