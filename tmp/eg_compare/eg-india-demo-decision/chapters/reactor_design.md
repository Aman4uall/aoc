## Reactor Design

Reactor R-101 uses Tubular Plug Flow Hydrator basis in gas_phase_catalytic service with k=14.9632 1/h and Da=14.963. Thermal stability basis gives DeltaTad=414.73 C and heat-removal margin 0.120. Integrated duty basis is 0.000 kW via shared HTM island network (shared_htm) with 1 utility islands [shared_htm], with explicit coupled area 0.000 m2 at 0.000 K.

### Governing Equations

- `V = tau * volumetric_flow`
- `k = A * exp(-Ea/RT)`
- `Da = k * tau`
- `Q = U * A * LMTD`
- `Nu = 0.023 * Re^0.8 * Pr^0.4`

### Route-Family Basis

| Parameter | Value |
| --- | --- |
| Route family | Liquid Hydration Train |
| Route family id | liquid_hydration_train |
| Primary reactor class | Tubular plug-flow hydrator |
| Primary separation train | EO flash -> water removal -> vacuum glycol distillation |
| Heat recovery style | condenser_reboiler_cluster |
| Data anchors | binary_interaction_parameters, liquid_density, liquid_viscosity, missing_vle_basis, missing_density_viscosity_for_column_hydraulics |

### Solver Packet Basis

| Packet | Primary Value 1 | Primary Value 2 | Closure / Recoverable | Status / Media |
| --- | --- | --- | --- | --- |
| reactor_unit_packet | 26953.864 | 26953.863 | 0.000 | converged |
| R-101_thermal_packet | 0.000 | 7600.213 | 0.000 | Dowtherm A, cooling water |

### Balance Reference Snapshot

| Stream | Role | From | To | kg/h | Dominant Components |
| --- | --- | --- | --- | --- | --- |
| S-150 | intermediate | feed_prep | reactor | 26953.864 | Ethylene oxide=18856.6, Water=8097.3 |
| S-201 | intermediate | reactor | primary_flash | 26953.863 | Ethylene glycol=25252.5, Ethylene oxide=754.3, Water=694.1, Trace heavy glycols=253.0 |

### Reactor Feed / Product / Recycle Summary

| Unit | Service | Stream | Local Role | Stream Role | Section | Phase | kg/h | kmol/h | Dominant Components |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reactor | Reaction zone | S-150 | feed | intermediate | reaction | gas | 26953.864 | 877.547235 | Ethylene oxide=18856.6, Water=8097.3 |
| reactor | Reaction zone | S-201 | product | intermediate | reaction | gas | 26953.863 | 465.036538 | Ethylene glycol=25252.5, Ethylene oxide=754.3, Water=694.1, Trace heavy glycols=253.0 |

### Reactor Local Stream Split Summary

| Split | Stream Count | Mass Flow (kg/h) | Molar Flow (kmol/h) |
| --- | --- | --- | --- |
| fresh_feed | 1 | 26953.864 | 877.547235 |
| recycle_feed | 0 | 0.000 | 0.000000 |
| total_feed | 1 | 26953.864 | 877.547235 |
| product_effluent | 1 | 26953.863 | 465.036538 |
| recycle_effluent | 0 | 0.000 | 0.000000 |
| side_draw_purge_vent | 0 | 0.000 | 0.000000 |

### Key Reactor Component Balance

| Component | Inlet kg/h | Outlet kg/h | Delta kg/h |
| --- | --- | --- | --- |
| Ethylene glycol | 0.000 | 25252.525 | 25252.525 |
| Ethylene oxide | 18856.564 | 754.263 | -18102.301 |
| Water | 8097.300 | 694.054 | -7403.246 |
| Trace heavy glycols | 0.000 | 253.021 | 253.021 |

### Reactor Design Inputs

| Parameter | Value |
| --- | --- |
| Residence time hr | 1.000 |
| Design volume m3 | 27004.165 |
| Design conversion fraction | 0.9600 |
| Phase regime | gas_phase_catalytic |
| Kinetic rate constant 1 hr | 14.9632 |
| Kinetic space time hr | 0.6000 |
| Kinetic damkohler number | 14.9632 |
| Heat duty kw | 7600.213 |
| Heat release density kw m3 | 0.281 |
| Adiabatic temperature rise c | 414.729 |
| Heat removal capacity kw | 8512.239 |
| Heat removal margin fraction | 0.1200 |
| Thermal stability score | 5.00 |
| Runaway risk label | moderate |
| Integrated thermal duty kw | 0.000 |
| Residual utility duty kw | 7600.213 |
| Integrated lmtd k | 0.000 |
| Integrated exchange area m2 | 0.000 |
| Allocated recovered duty target kw | 0.000 |

### Reactor Operating Envelope

| Parameter | Value |
| --- | --- |
| Temperature c | 255.0 |
| Pressure bar | 20.00 |
| Cooling medium | Dowtherm A / cooling water |
| Utility topology | shared HTM island network (shared_htm) with 1 utility islands |
| Utility architecture family | shared_htm |
| Coupled service basis | standalone utility service |
| Selected utility islands | none |
| Selected header levels | none |
| Selected cluster ids | none |
| Catalyst name | CO2 catalytic loop |
| Catalyst inventory kg | 4914758.026 |
| Catalyst cycle days | 270.0 |
| Catalyst regeneration days | 5.0 |
| Catalyst whsv 1 hr | 0.0055 |

### Reactor Sizing Basis

| Parameter | Value |
| --- | --- |
| Selected reactor type | Tubular Plug Flow Hydrator |
| Design basis | tubular_plug_flow_hydrator selected at 1.00 h residence time and 0.960 conversion basis. |
| Phase regime | gas_phase_catalytic |
| Residence time (h) | 1.000 |
| Design volume (m3) | 27004.165 |
| Design temperature (C) | 255.0 |
| Design pressure (bar) | 20.00 |

### Reaction and Sizing Derivation Basis

| Check | Formula / Basis | Result |
| --- | --- | --- |
| Volumetric throughput | Vdot = V / tau | 27004.165 m3/h |
| Kinetic consistency | Da = k * tau | 14.9632 |
| Heat release density | q''' = Q / V | 0.281 kW/m3 |
| Heat-transfer area check | A = Q / (U * LMTD) | n/a |
| Design conversion basis | Target conversion | 0.9600 |
| Packet closure basis | Unit packet closure | 0.000 % |

### Reactor Equation-Substitution Sheet

| Check | Equation | Substitution | Result |
| --- | --- | --- | --- |
| Residence-time sizing | Vdot = V / tau | V=27004.165 m3; tau=1.000 h | 27004.165 m3/h |
| Damkohler basis | Da = k * tau | k=14.963167 1/h; tau=1.000 h | 14.9632 |
| Thermal intensity | q''' = Q / V | Q=7600.213 kW; V=27004.165 m3 | 0.281 kW/m3 |
| Heat-transfer area check | A = Q / (U * LMTD) | Integrated LMTD not available | n/a |
| Heat-removal margin | Margin = Qrem / Qduty - 1 | Qrem=8512.239 kW; Qduty=7600.213 kW | 0.1200 |
| Residual utility demand | Qres = Qduty - Qint | Qduty=7600.213 kW; Qint=0.000 kW | 7600.213 kW |

### Kinetic Design Basis

| Parameter | Value |
| --- | --- |
| Design conversion fraction | 0.9600 |
| Rate constant (1/h) | 14.963167 |
| Kinetic space time (h) | 0.600000 |
| Damkohler number | 14.963167 |

### Reactor Geometry and Internals

| Parameter | Value |
| --- | --- |
| Liquid holdup (m3) | 22884.886 |
| Shell diameter (m) | 19.016 |
| Shell length (m) | 95.081 |
| Tube count | 24 |
| Tube length (m) | 83.671 |
| Heat-transfer area (m2) | 50.578 |
| Cooling medium | Dowtherm A / cooling water |
| Utility topology | shared HTM island network (shared_htm) with 1 utility islands |

### Heat-Transfer Derivation Basis

| Parameter | Value |
| --- | --- |
| Heat duty (kW) | 7600.213 |
| Heat-release density (kW/m3) | 0.281 |
| Adiabatic temperature rise (C) | 414.729 |
| Heat-removal capacity (kW) | 8512.239 |
| Heat-removal margin | 0.1200 |
| Thermal stability score | 5.00 |
| Runaway risk label | moderate |
| Heat-transfer area (m2) | 50.578 |
| Overall U (W/m2-K) | 850.0 |
| Reynolds number | 1,000.0 |
| Prandtl number | 122.136 |
| Nusselt number | 39.49 |
| Tube count | 24 |
| Tube length (m) | 83.671 |

### Thermal Stability and Hazard Envelope

| Parameter | Value |
| --- | --- |
| Adiabatic temperature rise (C) | 414.729 |
| Heat-removal capacity (kW) | 8512.239 |
| Heat-removal margin | 0.1200 |
| Thermal stability score | 5.00 |
| Runaway risk label | moderate |
| Residual utility duty (kW) | 7600.213 |
| Integrated recovered duty (kW) | 0.000 |

### Catalyst Service Basis

| Parameter | Value |
| --- | --- |
| Catalyst | CO2 catalytic loop |
| Catalyst inventory (kg) | 4914758.026 |
| Catalyst cycle (days) | 270.0 |
| Catalyst regeneration (days) | 5.0 |
| Catalyst void fraction | 0.350 |
| Catalyst WHSV (1/h) | 0.0055 |

### Integrated Utility Package Basis

| Parameter | Value |
| --- | --- |
| Architecture family | shared_htm |
| Coupled service basis | standalone utility service |
| Integrated LMTD (K) | 0.000 |
| Integrated exchange area (m2) | 0.000 |
| Allocated recovered-duty target (kW) | 0.000 |
| Selected utility islands | none |
| Selected header levels | none |
| Selected cluster ids | none |
| Selected train steps | none |

### Utility Coupling

| Parameter | Value |
| --- | --- |
| Utility topology | shared HTM island network (shared_htm) with 1 utility islands |
| Architecture family | shared_htm |
| Cooling medium | Dowtherm A / cooling water |
| Integrated duty (kW) | 0.000 |
| Allocated island target (kW) | 0.000 |
| Residual utility duty (kW) | 7600.213 |
| Integrated LMTD (K) | 0.000 |
| Integrated exchange area (m2) | 0.000 |
| Selected utility islands | none |
| Selected header levels | none |
| Selected cluster ids | none |
| Coupled service basis | standalone utility service |
| Selected train steps | none |

### Reactor Calculation Traces

| Trace | Formula | Inputs | Result | Notes |
| --- | --- | --- | --- | --- |
| Reactor holdup | V = Qv * tau * factor | Qv=22884.886; tau=1.000 | 22884.886 m3 | - |
| Reactor design volume | Vd = V * design_factor | V=22884.886; factor=1.180 | 27004.165 m3 | - |
| Kinetics-coupled sizing basis | k = A*exp(-Ea/RT); tau_design from kinetic space time, route time, and solved conversion target | Ea_kJ_mol=58.000; A_1_hr=1.200e+07; T_K=513.15; k_1_hr=14.9632; tau_kin_hr=0.6000; X_target=0.9600 | 1.000 h | Stage 3 reactor design now ties residence time to the selected kinetic basis instead of only a fixed route heuristic. |
| Reactor-side Reynolds number | Re = rho * v * Dh / mu | rho=1.2; v=0.200; Dh=0.032; mu=0.01304 | 1000.0 - | - |
| Reactor-side Nusselt number | Nu = 0.023 Re^0.8 Pr^0.4 | Re=1000.0; Pr=122.14 | 39.49 - | - |
| Reactor property-package basis | Pr = Cp * mu / k using mixture-property package values when available | Cp=2.448; mu=0.013037; k=0.2613; mixture_package=reactor_mixture_properties | 122.14 - | - |
| Solved reactor packet basis | reactor packet -> inlet mass and thermal duty | packet_inlet_mass_kg_hr=26953.864; thermal_packet=R-101_thermal_packet; composition_state=reactor_composition_state | 7600.213 kW | Reactor sizing now reads the solved reactor unit packet, composition state, and thermal packet before falling back to route-level heuristics. |
| Reactor utility-train coupling | Integrated reactor duty = sum(selected train steps tied to reactor source/sink) | selected_steps=none; topology=shared HTM island network (shared_htm) with 1 utility islands; architecture_family=shared_htm; selected_islands=none; header_levels=none; allocated_target_kw=0.000 | 0.000 kW | This captures recovered reactor duty exported to or imported from the selected utility train. |
| Reactor integrated heat-transfer basis | A_int = Q_int / (U * LMTD_int) | Q_int=0.0; U=850.0; LMTD_int=0.00 | 0.000 m2 | Integrated heat-transfer area is derived from the selected train-step thermal driving force, not only aggregate recovered duty. |
| Reactor thermal stability basis | DeltaTad = Q/(m*Cp); margin = (Qcap-Qduty)/Qduty | Qduty=7600.213; m_feed=26953.864; Cp_kJ_kg_K=2.448; DeltaTad=414.729; Qcap=8512.239 | 0.1200 fraction margin | This is a screening runaway and heat-removal check to keep reactor selection tied to thermal controllability. |
| Catalyst service basis | mcat = V*(1-eps)*rhobulk ; WHSV = mfeed/mcat | catalyst=CO2 catalytic loop; void_fraction=0.350; inventory_kg=4914758.026; WHSV_1_hr=0.0055; cycle_days=270.0 | 4914758.026 kg | Catalyst inventory and cycle are screening values used to connect reactor selection with service-life assumptions. |