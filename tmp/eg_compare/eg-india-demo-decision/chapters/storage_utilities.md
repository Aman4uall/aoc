## Storage and Utilities

### Storage Basis

| Parameter | Value |
| --- | --- |
| Inventory days | 14.1 |
| Working volume (m3) | 7661.521 |
| Total volume (m3) | 8580.903 |
| Material of construction | SS304 |

### Storage Inventory and Buffer Basis

| Parameter | Value |
| --- | --- |
| Recommended operating mode | continuous |
| Availability policy | continuous_liquid_train |
| Raw-material buffer (d) | 19.6 |
| Finished-goods buffer (d) | 9.4 |
| Operating stock (d) | 2.5 |
| Dispatch buffer (d) | 9.4 |
| Restart buffer (d) | 1.5 |
| Campaign length (d) | 170.0 |
| Startup ramp (d) | 2.0 |
| Restart loss fraction | 0.0062 |
| Annual restart loss (kg/y) | 16,426.7 |
| Turnaround buffer factor | 1.050 |
| Shared buffer basis | Operations planning basis combines route-family campaign behavior, startup loss, and dispatch buffering so storage, working capital, and financial timing use the same assumptions. |

### Storage Service Matrix

| Equipment | Service | Type | MoC | Volume (m3) | Design Basis |
| --- | --- | --- | --- | --- | --- |
| TK-301 | Ethylene Glycol storage via vertical tank farm | Storage tank | SS304 | 8580.903 | 14.1 days inventory |
| HX-01-EXP | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | HTM expansion tank | Carbon steel | 2.835 | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |

### Selected Heat Integration

| Parameter | Value |
| --- | --- |
| Selected case | Pinch + HTM loop |
| Recovered duty (kW) | 47256.658 |
| Residual hot utility (kW) | 43800.060 |
| Residual cold utility (kW) | 32255.698 |

### Utility Basis Decision

| Parameter | Value |
| --- | --- |
| Selected basis | hp_steam_20bar |
| Steam pressure (bar) | 20.0 |
| Steam cost (INR/kg) | 1.80 |
| Power cost (INR/kWh) | 8.50 |

### Utility Consumption Summary

| Utility | Load | Units | Annualized Proxy | Basis |
| --- | --- | --- | --- | --- |
| Steam | 71672.825 | kg/h | 567648774.0 kg/y | 20.0 bar saturated steam equivalent |
| Cooling water | 2778.003 | m3/h | 22001783.8 m3/y | 10 C cooling-water rise |
| Electricity | 28732.696 | kW | 227562952.3 kWh/y | Agitation, pumps, vacuum auxiliaries, and transfer drives |
| DM water | 2.000 | m3/h | 15840.0 m3/y | Boiler and wash service allowance |
| Nitrogen | 3.608 | Nm3/h | 28575.4 Nm3/y | Inerting and blanketing |
| Heat-integration auxiliaries | 16.166 | kW | 128034.7 kWh/y | Selected utility train circulation, HTM pumping, and exchanger-network auxiliaries |

### Utility Service System Matrix

| Utility System | Supply Basis | Primary Services | Standby / Design Note |
| --- | --- | --- | --- |
| Steam | 20.0 bar saturated steam header | reactor heating, reboiler duty, and dryer endpoint polish | 1 x operating + startup margin on steam letdown / control valve basis |
| Cooling water | recirculating cooling-water network with 10 C rise | condenser duty, exchanger cooling, and thermal packet cold-side service | peak summer duty covered by screening CW oversizing factor |
| Electricity | plant electrical distribution / MCC basis | agitation, pumping, fans, controls, and heat-recovery auxiliaries | feasibility standby allowance embedded in peak demand factor |
| DM water | demineralized water and wash-service header | boiler make-up, washdown, and utility support | intermittent demand carried as service allowance rather than dedicated redundancy |
| Nitrogen | nitrogen blanketing / inerting manifold | storage blanketing, shutdown purge, and inert atmosphere protection | peak inerting event handled by conservative surge factor |
| Heat-integration auxiliaries | plant electrical distribution / MCC basis | agitation, pumping, fans, controls, and heat-recovery auxiliaries | feasibility standby allowance embedded in peak demand factor |

### Utility Peak and Annualized Demand

| Utility | Normal Load | Units | Peak Factor | Peak Load | Annualized Usage | Cost Proxy |
| --- | --- | --- | --- | --- | --- | --- |
| Steam | 71672.825 | kg/h | 1.08 | 77406.651 | 567648774.0 kg/y | 1021767793 INR/y |
| Cooling water | 2778.003 | m3/h | 1.10 | 3055.803 | 22001783.8 m3/y | 176014270 INR/y |
| Electricity | 28732.696 | kW | 1.15 | 33042.600 | 227562952.3 kWh/y | 1934285095 INR/y |
| DM water | 2.000 | m3/h | 1.05 | 2.100 | 15840.0 m3/y | screening service allowance |
| Nitrogen | 3.608 | Nm3/h | 1.20 | 4.330 | 28575.4 Nm3/y | screening service allowance |
| Heat-integration auxiliaries | 16.166 | kW | 1.15 | 18.591 | 128034.7 kWh/y | 1088295 INR/y |

### Utility Demand by Major Unit

| Utility | Contributor | Estimated Demand | Basis |
| --- | --- | --- | --- |
| Steam | E-101 | 4532.727 kW | Feed preheat to operating temperature. |
| Steam | SEP-201 | 1248.737 kW | Generic purification duty. |
| Cooling water | R-101 | 7600.213 kW | Net reactor thermal duty from the selected thermodynamic basis. |
| Cooling water | SEP-201 | 624.369 kW | Generic purification duty. |
| Electricity | TK-301_pump | 159.360 kW | storage transfer and dispatch pumping basis |
| Heat-integration auxiliaries | omega_catalytic_pinch_htm__shared_htm | 42530.992 kW recovered | selected heat-recovery train circulation, controls, and HTM support |
| Nitrogen | TK-301 | 3.608 Nm3/h | storage blanketing and inerting demand |
| DM water | boiler_makeup_and_wash | 2.000 m3/h | boiler make-up and wash-service allowance |

### Utilities

| Utility | Load | Units | Basis |
| --- | --- | --- | --- |
| Steam | 71672.825 | kg/h | 20.0 bar saturated steam equivalent |
| Cooling water | 2778.003 | m3/h | 10 C cooling-water rise |
| Electricity | 28732.696 | kW | Agitation, pumps, vacuum auxiliaries, and transfer drives |
| DM water | 2.000 | m3/h | Boiler and wash service allowance |
| Nitrogen | 3.608 | Nm3/h | Inerting and blanketing |
| Heat-integration auxiliaries | 16.166 | kW | Selected utility train circulation, HTM pumping, and exchanger-network auxiliaries |

### Utility Island Service Basis

| Island | Role | Header Level | Cluster | Recovered Duty (kW) | Target Duty (kW) | HTM Inventory (m3) | Header Pressure (bar) | Control Complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | shared_htm | 1 | - | 42530.992 | 42530.992 | 3.936 | 14.500 | 2.500 |

### Header and Thermal-Loop Basis

| Step | Island | Header | Cluster | Role | Family | Pressure (bar) | Temperature (C) | Service |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| omega_catalytic_pinch_htm__shared_htm_step_01 | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 1 | - | controls | process_exchange | 9.00 | 203.0 | R-rough to D-rough heat recovery control valves, instrumentation, and bypass station |
| omega_catalytic_pinch_htm__shared_htm_step_01 | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 1 | - | header | process_exchange | 14.50 | 205.0 | R-rough to D-rough heat recovery network header and isolation package |
| omega_catalytic_pinch_htm__shared_htm_step_01 | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 1 | - | circulation | process_exchange | 14.50 | 205.0 | R-rough to D-rough heat recovery circulation loop |
| omega_catalytic_pinch_htm__shared_htm_step_01 | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 1 | - | relief | process_exchange | 13.50 | 213.0 | R-rough to D-rough heat recovery thermal relief and collection package |
| omega_catalytic_pinch_htm__shared_htm_step_02 | omega_catalytic_pinch_htm__shared_htm_shared_htm_01 | 1 | - | controls | process_exchange | 5.00 | 158.0 | D-rough to E-rough heat recovery control valves, instrumentation, and bypass station |

### Utility Architecture

Selected utility architecture: shared HTM island network (shared_htm) with 1 utility islands.

Selected case id: omega_catalytic_pinch_htm__shared_htm
Selected base case id: omega_catalytic_pinch_htm
Recoverable duty target: 59070.823 kW
Selected annual utility cost: INR 1,171,379,913.01/y
Thermal packet count: 3
Packet-derived exchanger candidates: 2
Composite intervals: 11
Selected utility islands: 1
Selected train steps: 2