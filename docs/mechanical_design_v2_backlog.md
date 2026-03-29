# Mechanical Design v2 Backlog

This backlog tracks Stage 6 work that moves the mechanical layer from basic vessel screening toward richer preliminary design packets.

## Scope

Primary objective:
- deepen support, nozzle, load-case, and access/platform logic so the mechanical chapter and annexures feel closer to a real preliminary design package

Guardrails:
- keep the current `mechanical_design_moc` stage and existing CLI/report flow intact
- stay at preliminary / screening rigor, not code-stamped detailed design
- make every new field deterministic and critic-friendly

## Stage 6 Slices

### V6.1 Load Cases, Connection Classes, and Access Basis

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_mechanical.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_mechanical.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Artifacts:
- `MechanicalComponentDesign.support_load_case`
- `MechanicalComponentDesign.pressure_class`
- `MechanicalComponentDesign.hydrotest_pressure_bar`
- `MechanicalComponentDesign.design_vertical_load_kn`
- `MechanicalComponentDesign.piping_load_kn`
- `MechanicalComponentDesign.wind_load_kn`
- `MechanicalComponentDesign.seismic_load_kn`
- `MechanicalComponentDesign.maintenance_platform_required`
- `MechanicalComponentDesign.platform_area_m2`
- `MechanicalComponentDesign.pipe_rack_tie_in_required`
- `SupportDesign.support_load_case`
- `SupportDesign.foundation_note`
- `NozzleSchedule.nozzle_orientations_deg`
- `NozzleSchedule.nozzle_connection_classes`
- `NozzleSchedule.nozzle_load_cases_kn`
- `VesselMechanicalDesign.hydrotest_pressure_bar`
- `VesselMechanicalDesign.pressure_class`
- `VesselMechanicalDesign.access_platform_required`

Acceptance:
- mechanical design emits explicit wind, seismic, piping, and vertical load components by equipment family
- headers and HTM packages carry pipe-rack and connection-class consequences instead of generic vessel logic
- mechanical chapter and annexures expose pressure class, hydrotest basis, load case, and access-platform basis directly

### V6.2 Support, Foundation, and Nozzle Interaction Basis

Status:
- implemented

Delivered:
- support variants now distinguish skirt, saddle, leg, lug, and rack-style support screening
- anchor-group count and foundation footprint are emitted per equipment item
- nozzle reinforcement family and local shell/load interaction factors are persisted per equipment item
- vessel support and nozzle schedules carry the same basis into annexures and mechanical chapter tables

### V6.3 Datasheet, Layout, and Critic Coupling

Status:
- implemented

Delivered:
- equipment datasheets are regenerated after mechanical design so they carry pressure class, hydrotest, support variant, foundation, clearance, ladder, lifting-lug, and nozzle basis
- layout now includes maintenance/foundation basis so mechanical clearance and rack tie-in consequences are visible downstream
- mechanical-stage validation now blocks missing pressure class, hydrotest, support load case, foundation footprint, anchor-group basis, and invalid shell interaction factors

## Stage 6 Status

Status:
- complete

Acceptance reached:
- mechanical chapter and annexures now expose support/load, foundation/access, and nozzle/reinforcement basis directly
- equipment datasheets carry mechanical basis instead of stopping at process-only sizing fields
- layout/report coupling now includes maintenance clearance and foundation footprint consequences
- mechanical stage now has dedicated critics instead of relying only on generic chapter/value validation

## Next Priorities

1. Start Stage 7 economics/finance v4 so replacement cycles, procurement timing, and outage-linked revenue impacts become more realistic.
2. Push the new mechanical basis into richer package-level cost correlations and maintenance scopes.
3. Deepen relief, piping-class, and connection schedule logic if we want to keep extending mechanical depth later.
