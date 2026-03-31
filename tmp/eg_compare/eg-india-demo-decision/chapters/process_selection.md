## Process Selection

### Route Comparison

| Route | Family | Total score | Residual hot utility (kW) | Heat case | Scenario stability |
| --- | --- | --- | --- | --- | --- |
| eo_hydration | liquid_hydration_train | 39.95 | 49263.839 | eo_hydration_pinch_htm | reviewed |
| omega_catalytic | liquid_hydration_train | 60.60 | 43800.060 | omega_catalytic_pinch_htm | stable |
| chlorohydrin | chlorinated_hydrolysis_train | -1.00 | 13044.246 | chlorohydrin_no_recovery | reviewed |

### Selected Route

OMEGA catalytic route via ethylene carbonate is selected because the `Liquid Hydration Train` route family stays economically competitive after the chosen heat-integration case `omega_catalytic_pinch_htm`, while retaining credible industrial maturity and India fit.

### Route Family Profiles

| Route | Family | Reactor Basis | Separation Train | Heat Style | India Blocker |
| --- | --- | --- | --- | --- | --- |
| eo_hydration | Liquid Hydration Train | Tubular plug-flow hydrator | EO flash -> water removal -> vacuum glycol distillation | condenser_reboiler_cluster | none |
| omega_catalytic | Liquid Hydration Train | Tubular plug-flow hydrator | EO flash -> water removal -> vacuum glycol distillation | condenser_reboiler_cluster | none |
| chlorohydrin | Chlorinated Hydrolysis Train | Agitated hydrolysis CSTR train | Salt removal -> brine handling -> water removal -> purification | utility_led_with_brine_management | Route generates chloride-heavy waste and is not preferred for India deployment under the current policy basis. |

### Unit-Operation Family Expansion

Route `omega_catalytic` is expanded into the `Liquid Hydration Train` unit-operation family.

| Service Group | Candidate | Status | Score | Rationale |
| --- | --- | --- | --- | --- |
| reactor | tubular_plug_flow_hydrator | preferred | 102.0 | Tubular hydrator with strong dehydration integration fit |
| reactor | jacketed_cstr_train | preferred | 78.0 | CSTR fallback for liquid hydration service |
| reactor | high_pressure_carbonylation_loop | blocked | 18.0 | High-pressure carbonylation loop |
| separation | distillation_train | preferred | 100.0 | Flash and glycol distillation train |
| separation | extractive_distillation_train | fallback | 82.0 | Extractive/vacuum polishing distillation |
| separation | packed_absorption_train | blocked | 20.0 | Packed absorption train |

- Supporting unit operations: flash, dehydration_column, glycol_polishing_column, heat_exchanger_cluster, reactor, distillation, heat_exchanger
- Applicability critics: dehydration_duty, glycol_split_vle_basis, water_recycle_closure, relative_volatility_claims, reboiler_duty_burden

### Chemistry Family Adapter

Adapter `continuous_liquid_organic_train` supports continuous liquid organic train under a organic chemistry basis.

- Route hints: hydration, carbonylation, hydrogenation, dehydration cleanup
- Property priority: molecular_weight, normal_boiling_point, liquid_density, liquid_viscosity, liquid_heat_capacity, heat_of_vaporization, antoine_constants, binary_interaction_parameters
- Preferred reactor candidates: tubular_plug_flow_hydrator, jacketed_cstr_train
- Preferred separation candidates: distillation_train, extraction_recovery_train
- Common unit operations: reactor, flash, distillation, heat_exchanger, storage
- Corrosion cues: organic_acid_presence, water_content, chloride_trace_monitoring
- Heat-integration patterns: reboiler_condenser_cluster, shared_htm_island_network, moderate_temperature_recovery
- Critic focus: relative_volatility_claims, water_recycle_closure, reboiler_duty_burden
- Sparse-data blockers: missing_vle_basis, missing_density_viscosity_for_column_hydraulics

### Sparse-Data Policy

| Stage | Subject | Artifact Family | Est. | Analogy | Heuristic Fallback | Min Confidence | Status | Triggered Items |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| thermodynamic_feasibility | molecular_weight | pure_component_identity | yes | no | no | 0.55 | covered | - |
| thermodynamic_feasibility | normal_boiling_point | pure_component_thermo | yes | no | no | 0.60 | covered | - |
| energy_balance | liquid_heat_capacity | bulk_thermal_properties | yes | no | no | 0.55 | covered | - |
| energy_balance | heat_of_vaporization | bulk_thermal_properties | yes | no | no | 0.55 | covered | - |
| reactor_design | liquid_density | transport_properties | yes | no | no | 0.60 | covered | - |
| reactor_design | liquid_viscosity | transport_properties | yes | no | no | 0.60 | covered | - |
| distillation_design | liquid_density | separation_transport | yes | no | no | 0.60 | covered | - |
| distillation_design | liquid_viscosity | separation_transport | yes | no | no | 0.60 | covered | - |
| distillation_design | binary_interaction_parameters | vle_nonideal_basis | no | no | yes | 0.00 | warning | ethylene_glycol__ethylene_oxide, ethylene_glycol__water, ethylene_oxide__water |

### Selected Reactor Basis

Tubular or plug-flow hydrator service selected as the highest-ranked alternative.

### Selected Separation Basis

Distillation and flash purification train selected as the highest-ranked alternative.

### Selected Heat-Integration Case

Pinch + HTM loop: Pinch-based heat recovery with an indirect hot-oil loop materially reduces purchased steam.