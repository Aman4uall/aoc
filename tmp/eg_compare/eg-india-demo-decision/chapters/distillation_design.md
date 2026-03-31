## Distillation / Process-Unit Design

Column PU-201 hydraulic basis uses tray spacing 0.450 m and flooding fraction 0.538, with superficial vapor velocity 0.188 m/s against allowable 0.350 m/s. Integrated reboiler duty basis is 0.000 kW via shared HTM island network (shared_htm) with 1 utility islands, family shared_htm, with reboiler area 0.000 m2 at 0.000 K.

### Route-Family Basis

| Parameter | Value |
| --- | --- |
| Route family | Liquid Hydration Train |
| Route family id | liquid_hydration_train |
| Primary separation train | EO flash -> water removal -> vacuum glycol distillation |
| Heat recovery style | condenser_reboiler_cluster |
| Dominant phase pattern | liquid_reactive |
| Data anchors | binary_interaction_parameters, liquid_density, liquid_viscosity, missing_vle_basis, missing_density_viscosity_for_column_hydraulics |

### Governing Equations

- `Fenske / Underwood / Gilliland equivalents`
- `Q = U * A * LMTD`
- `A = Q / (U * LMTD)`
- `m_phase = Q / lambda`

### Solver Packet Basis

| Packet | Unit | Type | Inlet kg/h | Outlet kg/h | Closure Error (%) | Status |
| --- | --- | --- | --- | --- | --- | --- |
| purification_unit_packet | purification | distillation | 26583.820 | 26583.820 | 0.000 | converged |

### Balance Reference Snapshot

| Stream | Role | From | To | kg/h | Dominant Components |
| --- | --- | --- | --- | --- | --- |
| S-301 | recycle | recycle_recovery | purification | 26583.820 | Ethylene glycol=25252.5, Water=565.2, Ethylene oxide=523.2, Trace heavy glycols=242.9 |
| S-401 | recycle | purification | feed_prep | 1001.496 | Water=523.6, Ethylene oxide=477.9 |
| S-402 | product | purification | storage | 24974.747 | Ethylene glycol=24974.7 |
| S-403 | waste | purification | waste_treatment | 0.000 | - |

### Unit-by-Unit Feed / Product / Recycle Summary

| Unit | Service | Stream | Local Role | Stream Role | Section | Phase | kg/h | kmol/h | Dominant Components |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| purification | Purification train | S-301 | recycle feed | recycle | recycle_recovery_carbonate_loop_cleanup | gas | 26583.820 | 452.537668 | Ethylene glycol=25252.5, Water=565.2, Ethylene oxide=523.2, Trace heavy glycols=242.9 |
| purification | Purification train | S-401 | recycle product | recycle | purification | gas | 1001.496 | 39.913416 | Water=523.6, Ethylene oxide=477.9 |
| purification | Purification train | S-402 | product | product | purification | gas | 24974.747 | 402.364225 | Ethylene glycol=24974.7 |
| purification | Purification train | S-403 | waste | waste | purification | mixed | 0.000 | 0.000000 | - |

### Process-Unit Local Stream Split Summary

| Split | Stream Count | Mass Flow (kg/h) | Molar Flow (kmol/h) |
| --- | --- | --- | --- |
| fresh_feed | 0 | 0.000 | 0.000000 |
| recycle_feed | 1 | 26583.820 | 452.537668 |
| total_feed | 1 | 26583.820 | 452.537668 |
| product_effluent | 1 | 24974.747 | 402.364225 |
| recycle_effluent | 1 | 1001.496 | 39.913416 |
| side_draw_purge_vent | 1 | 0.000 | 0.000000 |

### Key Process-Unit Component Balance

| Unit | Service | Component | Inlet kg/h | Outlet kg/h | Delta kg/h |
| --- | --- | --- | --- | --- | --- |
| purification | Purification train | Ethylene glycol | 25252.525 | 24974.747 | -277.778 |
| purification | Purification train | Water | 565.238 | 523.595 | -41.643 |
| purification | Purification train | Ethylene oxide | 523.157 | 477.901 | -45.256 |
| purification | Purification train | Trace heavy glycols | 242.900 | 0.000 | -242.900 |

### Separation Design Inputs

| Parameter | Value |
| --- | --- |
| Service | Distillation and purification train |
| Equilibrium model | screening_vle |
| Equilibrium parameter ids | none |
| Light key | Water |
| Heavy key | Ethylene Glycol |
| Relative volatility | 19.315 |
| Minimum stages | 3.278 |
| Theoretical stages | 4.278 |
| Design stages | 7 |
| Minimum reflux ratio | 0.150 |
| Operating reflux ratio | 0.200 |

### Section and Feed Basis

| Parameter | Value |
| --- | --- |
| Feed quality q-factor | 1.106 |
| Murphree efficiency | 0.634 |
| Top relative volatility | 25.909 |
| Bottom relative volatility | 14.399 |
| Rectifying theoretical stages | 2.444 |
| Stripping theoretical stages | 1.833 |
| Rectifying vapor load (kg/h) | 6352.735 |
| Stripping vapor load (kg/h) | 5683.010 |
| Rectifying liquid load (m3/h) | 6090.003 |
| Stripping liquid load (m3/h) | 16500.036 |

### Distillation Equation-Substitution Basis

| Check | Equation | Substitution | Result |
| --- | --- | --- | --- |
| Fenske minimum stages | Nmin = Fenske(alpha, LK/HK split) | alpha=19.315; alpha_top=25.909; alpha_bottom=14.399 | 3.278 |
| Underwood minimum reflux | Rmin = Underwood(alpha, q, keys) | alpha_top=25.909; alpha_bottom=14.399; q=1.106 | 0.150 |
| Gilliland operating stages | N = Gilliland(Nmin, R/Rmin) | Nmin=3.278; R/Rmin=1.333 | 4.278 |
| Murphree tray conversion | Nactual = Ntheoretical / Em | Ntheoretical=4.278; Em=0.634 | 6.748 equivalent trays |

### Feed and Internal Flow Derivation

| Check | Formula / Basis | Result |
| --- | --- | --- |
| Minimum stages | Fenske screening | 3.278 |
| Minimum reflux | Underwood screening | 0.150 |
| Operating stages | Gilliland screening | 4.278 |
| Feed condition | q-factor basis | 1.106 |
| Rectifying section split | Section stage allocation | 2.444 stages |
| Stripping section split | Section stage allocation | 1.833 stages |
| Rectifying internal vapor load | Top section vapor load | 6352.735 kg/h |
| Stripping internal vapor load | Bottom section vapor load | 5683.010 kg/h |
| Rectifying liquid load | Top section liquid load | 6090.003 m3/h |
| Stripping liquid load | Bottom section liquid load | 16500.036 m3/h |

### Feed Condition and Internal Flow Substitution Sheet

| Check | Equation | Substitution | Result |
| --- | --- | --- | --- |
| Feed quality basis | q = feed thermal condition parameter | selected feed stage=4; q=1.106 | 1.106 |
| Rectifying section split | Nrect = f(feed stage, N) | feed stage=4; N=7 | 2.444 stages |
| Stripping section split | Nstrip = N - Nrect | N=4.278; Nrect=2.444 | 1.833 stages |
| Rectifying vapor load | Vrect from section screening | R=0.200; Rmin=0.150 | 6352.735 kg/h |
| Stripping vapor load | Vstrip from bottom section screening | Nstrip=1.833; q=1.106 | 5683.010 kg/h |
| Rectifying liquid load | Lrect from reflux / internal flow basis | R=0.200 | 6090.003 m3/h |
| Stripping liquid load | Lstrip from boilup / internal flow basis | Reboiler duty=3179.805 kW | 16500.036 m3/h |

### Column Operating Envelope

| Parameter | Value |
| --- | --- |
| Column diameter (m) | 1.500 |
| Column height (m) | 12.000 |
| Top temperature (C) | 108.0 |
| Bottom temperature (C) | 203.3 |
| Liquid density (kg/m3) | 1.158 |
| Vapor density (kg/m3) | 6.005 |
| Superficial vapor velocity (m/s) | 0.188 |
| Allowable vapor velocity (m/s) | 0.350 |
| Flooding fraction | 0.538 |
| Pressure drop per stage (kPa) | 0.282 |

### Reboiler and Condenser Package Basis

| Parameter | Value |
| --- | --- |
| Reboiler package type | none |
| Reboiler medium | none |
| Reboiler integrated duty (kW) | 0.000 |
| Reboiler LMTD (K) | 0.000 |
| Reboiler integrated area (m2) | 0.000 |
| Reboiler phase-change load (kg/h) | 6187.729 |
| Condenser package type | none |
| Condenser recovery medium | none |
| Condenser recovery duty (kW) | 0.000 |
| Condenser recovery LMTD (K) | 0.000 |
| Condenser recovery area (m2) | 0.000 |
| Condenser phase-change load (kg/h) | 7049.642 |

### Reboiler and Condenser Thermal Substitution Sheet

| Check | Equation | Substitution | Result |
| --- | --- | --- | --- |
| Operating reflux multiple | R/Rmin = R / Rmin | R=0.200; Rmin=0.150 | 1.333 |
| Integrated reboiler area | A = Q / (U * LMTD) | Q=0.0 W; U=0.0 W/m2-K; LMTD=0.000 K | 0.000 m2 |
| Reboiler phase-change basis | m = Q / lambda | Q=3179.805 kW; lambda~=1850.0 kJ/kg | 6187.729 kg/h |
| Condenser recovery area | A = Q / (U * LMTD) | Q=0.0 W; U=0.0 W/m2-K; LMTD=0.000 K | 0.000 m2 |
| Condenser phase-change basis | m = Q / lambda | Q=0.000 kW; lambda~=0.0 kJ/kg | 7049.642 kg/h |

### Process-Unit Sizing Basis

| Parameter | Value |
| --- | --- |
| Service | Distillation and purification train |
| Light key | Water |
| Heavy key | Ethylene Glycol |
| Relative volatility | 19.315 |
| Minimum stages | 3.278 |
| Theoretical stages | 4.278 |
| Design stages | 7 |
| Tray efficiency | 0.660 |
| Minimum reflux ratio | 0.150 |
| Reflux ratio | 0.200 |
| R / Rmin | 1.333 |
| Diameter (m) | 1.500 |
| Height (m) | 12.000 |
| Feed stage | 4 |

### Hydraulics Basis

| Parameter | Value |
| --- | --- |
| Tray spacing (m) | 0.450 |
| Flooding fraction | 0.538 |
| Downcomer area fraction | 0.140 |
| Vapor velocity (m/s) | 0.188 |
| Allowable vapor velocity (m/s) | 0.350 |
| Capacity factor (m/s) | 350000.000 |
| Active area (m2) | 1.520 |
| Liquid load (m3/h) | 6090.003 |
| Vapor load (kg/h) | 6187.729 |
| Liquid density (kg/m3) | 1.158 |
| Vapor density (kg/m3) | 6.005 |
| Pressure drop per stage (kPa) | 0.282 |
| Top temperature (C) | 108.0 |
| Bottom temperature (C) | 203.3 |

### Heat-Transfer Package Inputs

| Parameter | Value |
| --- | --- |
| Heat load kw | 34024.794 |
| Lmtd k | 8.000 |
| U w m2 k | 470.000 |
| Package family | process_exchange |
| Circulation flow m3 hr | 1818.329 |
| Phase change load kg hr | 0.000 |
| Package holdup m3 | 542.949 |
| Utility topology | shared HTM island network (shared_htm) with 1 utility islands |
| Utility architecture family | shared_htm |
| Selected train step id | omega_catalytic_pinch_htm__shared_htm_step_01 |
| Selected island id | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 |
| Selected header level | 1 |
| Selected cluster id | none |
| Allocated recovered duty target kw | 42530.992 |
| Boiling side coefficient w m2 k | 1200.000 |
| Condensing side coefficient w m2 k | 1200.000 |

### Exchanger Package Selection Basis

| Parameter | Value |
| --- | --- |
| Package family | process_exchange |
| Selected package roles | circulation, controls, exchanger, expansion, header, relief |
| Selected package items | omega_catalytic_pinch_htm__shared_htm_step_01_exchanger, omega_catalytic_pinch_htm__shared_htm_step_01_controls, omega_catalytic_pinch_htm__shared_htm_step_01_header, omega_catalytic_pinch_htm__shared_htm_step_01_circulation, omega_catalytic_pinch_htm__shared_htm_step_01_expansion, omega_catalytic_pinch_htm__shared_htm_step_01_relief |

### Utility Coupling

| Parameter | Value |
| --- | --- |
| Utility topology | shared HTM island network (shared_htm) with 1 utility islands |
| Architecture family | shared_htm |
| Integrated reboiler duty (kW) | 0.000 |
| Allocated reboiler target (kW) | 0.000 |
| Residual reboiler utility (kW) | 3179.805 |
| Integrated reboiler LMTD (K) | 0.000 |
| Integrated reboiler area (m2) | 0.000 |
| Reboiler medium | none |
| Reboiler package type | none |
| Reboiler circulation ratio | 3.000 |
| Reboiler phase-change load (kg/h) | 6187.729 |
| Reboiler package items | none |
| Condenser recovery duty (kW) | 0.000 |
| Allocated condenser target (kW) | 0.000 |
| Condenser recovery LMTD (K) | 0.000 |
| Condenser recovery area (m2) | 0.000 |
| Condenser recovery medium | none |
| Condenser package type | none |
| Condenser phase-change load (kg/h) | 7049.642 |
| Condenser circulation flow (m3/h) | 6090.003 |
| Condenser package items | none |
| Selected utility islands | none |
| Selected header levels | none |
| Selected cluster ids | none |
| Selected train steps | none |

### Heat-Exchanger Thermal Basis

| Parameter | Value |
| --- | --- |
| Configuration | Shell And Tube |
| Heat load (kW) | 34024.794 |
| LMTD (K) | 8.0 |
| Overall U (W/m2-K) | 470.0 |
| Area (m2) | 9049.147 |
| Package family | process_exchange |
| Architecture family | shared_htm |
| Selected train step | omega_catalytic_pinch_htm__shared_htm_step_01 |
| Selected utility island | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 |
| Selected header level | 1 |
| Selected cluster id | none |
| Allocated island target (kW) | 42530.992 |
| Package roles | circulation, controls, exchanger, expansion, header, relief |
| Selected package items | omega_catalytic_pinch_htm__shared_htm_step_01_exchanger, omega_catalytic_pinch_htm__shared_htm_step_01_controls, omega_catalytic_pinch_htm__shared_htm_step_01_header, omega_catalytic_pinch_htm__shared_htm_step_01_circulation, omega_catalytic_pinch_htm__shared_htm_step_01_expansion, omega_catalytic_pinch_htm__shared_htm_step_01_relief |
| Boiling-side coefficient (W/m2-K) | 1200.000 |
| Condensing-side coefficient (W/m2-K) | 1200.000 |

### Process-Unit Calculation Traces

| Trace | Formula | Inputs | Result | Notes |
| --- | --- | --- | --- | --- |
| Process-unit family | service = selected separation family | - | Distillation and purification train | - |
| Separation thermodynamics basis | alpha = sqrt(alpha_top * alpha_bottom) from component K-values when a VLE basis exists | light_key=Water; heavy_key=Ethylene Glycol; alpha_top=25.9091; alpha_bottom=14.3988; method=ideal_raoult_missing_bip_fallback | 19.3148 - | Column volatility basis now prefers the separation-thermodynamics artifact built from Antoine / Clausius-Clapeyron K-values when available. |
| Minimum theoretical stages | Nmin = log[(xD,LK/xB,LK)*(xB,HK/xD,HK)] / log(alpha) | xD,LK=0.9850; xB,LK=0.0040; xD,HK=0.0150; xB,HK=0.9990; alpha=19.315 | 3.278 stages | - |
| Minimum reflux proxy | Rmin = f(alpha, q, xD,LK) | alpha=19.315; q=1.106; xD,LK=0.9850 | 0.150 - | This is a screening Underwood-style reflux estimate built from the solved property basis and separation severity. |
| Feed and volatility section basis | q from Cp and DeltaT; section volatility anchored to top/bottom alpha estimates | q=1.106; alpha_top=25.909; alpha_bottom=14.399; murphree_efficiency=0.634 | 1.106 - | Stage 2 separation design keeps the feed-quality and section-volatility basis explicit instead of burying it inside the reflux proxy. |
| Actual stage proxy | Nactual = g(Nmin, R/Rmin, tray efficiency) | Nmin=3.278; R=0.200; Rmin=0.150; tray_eff=0.660 | 7.000 actual stages | - |
| Rectifying and stripping section basis | Nrect + Nstrip = Ntheoretical ; section loads derived from reflux and bottoms circulation | feed_stage=4; Ntheoretical=4.278; Nrect=2.444; Nstrip=1.833; Vrect=6352.735; Vstrip=5683.010 | 4.278 stages | This makes the section-level column basis explicit before deeper M9-style tray-by-tray work. |
| Equivalent diameter | D = sqrt(4*Aactive/[pi*(1-Adc)]) | Aactive=1.105; Adc=0.140 | 1.500 m | - |
| Column hydraulic capacity basis | uallow = C * sqrt[(rhoL-rhoV)/rhoV]; uflood = usuperficial/uallow | C=0.300; rhoL=1.158; rhoV=6.005; usuperficial=0.188 | 0.538 - | - |
| Process-unit property-package basis | Hydraulics proxy uses density, viscosity, and Cp from the mixture-property package | density=1.158; viscosity=0.014479; Cp=2.452; mixture_package=purification_mixture_properties | 1.158 kg/m3 | - |
| Solved process-unit packet basis | packet basis -> outlet throughput and matched thermal packets | process_packet=purification_unit_packet; heating_packet=fallback; cooling_packet=fallback; composition_state=purification_composition_state | 3179.805 kW | Process-unit sizing now prefers solved separation packet, composition state, and thermal packet before route-level utility heuristics. |
| Process-unit utility-train coupling | Integrated reboiler duty = sum(selected train steps tied to process-unit cold sinks | heating_steps=none; condenser_steps=none; topology=shared HTM island network (shared_htm) with 1 utility islands; architecture_family=shared_htm; selected_islands=none; header_levels=none | 0.000 kW | This captures recovered duty delivered into the reboiler/process unit and heat recovered from condenser-side streams. |
| Reboiler package basis | Vboil = Qreb / lambda; circulation from selected train package when available | package=fallback; package_type=generic; phase_change_load_kg_hr=6187.729; circulation_ratio=3.000; selected_islands=none; target_recovered_kw=0.000; cluster_ids=none | 3179.805 kW | - |
| Condenser package basis | mcond = Qcond / lambda; circulation from selected train package when available | package=fallback; package_type=generic; phase_change_load_kg_hr=7049.642; circulation_flow_m3_hr=6090.003; selected_islands=none; target_recovered_kw=0.000; cluster_ids=none | 4112.291 kW | - |
| Integrated reboiler heat-transfer basis | A_reb,int = Q_reb,int / (U_reb * LMTD_reb,int) | Q_reb,int=0.0; U_reb=780.0; LMTD_reb,int=0.00 | 0.000 m2 | Integrated reboiler area is derived from selected train steps that feed the process-unit heating sink. |
| Condenser-side recovery basis | A_cond,rec = Q_cond,rec / (U_cond * LMTD_cond,rec) | Q_cond,rec=0.0; U_cond=700.0; LMTD_cond,rec=0.00 | 0.000 m2 | Recovered condenser duty is tied to selected train steps sourced from the process-unit hot side. |
| Solved equilibrium packet basis | selected separation packets provide the active phase-equilibrium model and split basis for this process-unit family | packet_ids=purification_separation_packet; models=heuristic; parameter_ids=none; fallback=no | heuristic_split | This basis is consumed directly from the solved separator packets rather than being inferred from chapter prose. |
| Exchanger area | A = Q/(U*dTlm) | Q=34024794.0; U=470.0; dTlm=8.0 | 9049.147 m2 | - |
| Solved exchanger packet basis | packet basis -> selected thermal packet | thermal_packet=fallback; selected_train_step=omega_catalytic_pinch_htm__shared_htm_step_01; architecture_family=shared_htm; selected_island=omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 34024.794 kW | Exchanger sizing now prefers the selected utility-train step and solved thermal packet before aggregate-duty fallback. |
| Utility package exchanger basis | Selected exchanger package -> family, area, LMTD, circulation, phase load | package_family=process_exchange; exchanger_package=omega_catalytic_pinch_htm__shared_htm_step_01_exchanger; circulation_flow_m3_hr=1818.329; phase_change_load_kg_hr=0.000; header_level=1; cluster_id=none; target_recovered_kw=42530.992 | 542.949 m3 | Reboiler/condenser package sizing now reads the selected utility package item before applying generic exchanger fallback. |