## Equipment Design and Sizing

### Storage Decision

Vertical atmospheric tank farm selected as the highest-ranked alternative.

### Material of Construction Decision

Carbon steel construction selected as the highest-ranked alternative.

### Storage Basis

| Parameter | Value |
| --- | --- |
| Inventory days | 14.1 |
| Dispatch buffer days | 9.4 |
| Operating stock days | 2.5 |
| Restart buffer days | 1.5 |
| Turnaround buffer factor | 1.050 |
| Working volume (m3) | 7661.521 |
| Total volume (m3) | 8580.903 |
| Tank diameter (m) | 13.979 |
| Straight-side height (m) | 55.914 |

### Operations Planning Basis

| Parameter | Value |
| --- | --- |
| Operating mode | continuous |
| Service family | continuous_liquid_purification |
| Raw-material buffer (d) | 19.6 |
| Finished-goods buffer (d) | 9.4 |
| Operating stock (d) | 2.5 |
| Restart buffer (d) | 1.5 |
| Startup ramp (d) | 2.0 |
| Campaign length (d) | 170.0 |
| Annual restart loss (kg/y) | 16,426.7 |

### Storage Transfer Pump Basis

| Parameter | Value |
| --- | --- |
| Pump id | TK-301_pump |
| Service | Ethylene Glycol storage via vertical tank farm transfer |
| Flow (m3/h) | 957.690 |
| Differential head (m) | 52.0 |
| Power (kW) | 159.360 |
| NPSH margin (m) | 2.500 |

### Storage and Inventory Vessel Basis

| ID | Type | Service | Volume (m3) | Design T (C) | Design P (bar) | MoC | Design Basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V-101 | Flash drum | Intermediate disengagement | 4860.750 | 85.0 | 3.00 | Carbon Steel | Generic separator hold-up |
| TK-301 | Storage tank | Ethylene Glycol storage via vertical tank farm | 8580.903 | 45.0 | 1.20 | SS304 | 14.1 days inventory |
| HX-01-EXP | HTM expansion tank | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | 2.835 | 210.0 | 6.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |

### Major Process Equipment Basis

| ID | Type | Service | Volume (m3) | Duty (kW) | Design T (C) | Design P (bar) | MoC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | Tubular Plug Flow Hydrator | 27004.165 | 7600.213 | 255.0 | 20.00 | Carbon Steel |
| PU-201 | Distillation column | Distillation and purification train | 21.206 | 3179.805 | 140.0 | 2.00 | Carbon Steel |
| E-101 | Heat exchanger | R-rough to D-rough heat recovery | 723.932 | 34024.794 | 180.0 | 8.00 | Carbon Steel |
| TK-301 | Storage tank | Ethylene Glycol storage via vertical tank farm | 8580.903 | 0.000 | 45.0 | 1.20 | SS304 |

### Heat Exchanger and Thermal-Service Basis

| ID | Type | Service | Duty (kW) | Design T (C) | Design P (bar) | MoC | Design Basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E-101 | Heat exchanger | R-rough to D-rough heat recovery | 34024.794 | 180.0 | 8.00 | Carbon Steel | LMTD 8.0 K |
| HX-01 | HTM loop exchanger | R-rough to D-rough heat recovery | 34024.794 | 213.0 | 11.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-CTRL | Utility control package | R-rough to D-rough heat recovery control valves, instrumentation, and bypass station | 0.000 | 203.0 | 9.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-HDR | Shared HTM header manifold | R-rough to D-rough heat recovery network header and isolation package | 34024.794 | 205.0 | 14.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-PMP | HTM circulation skid | R-rough to D-rough heat recovery circulation loop | 15.466 | 205.0 | 14.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-EXP | HTM expansion tank | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | 0.000 | 210.0 | 6.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-RV | HTM relief package | R-rough to D-rough heat recovery thermal relief and collection package | 0.000 | 213.0 | 13.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02 | Heat integration exchanger | D-rough to E-rough heat recovery | 8506.198 | 162.0 | 6.50 | SS316 | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02-CTRL | Utility control package | D-rough to E-rough heat recovery control valves, instrumentation, and bypass station | 0.000 | 158.0 | 5.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |

### Rotating and Auxiliary Package Basis

| ID | Type | Service | Flow/Volume Basis | Head/Pressure Basis | Power/Duty (kW) | NPSH Margin | Design Basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TK-301_pump | Transfer pump | Ethylene Glycol storage via vertical tank farm transfer | 957.690 | 52.000 | 159.360 | 2.500 | Dedicated pump design artifact |
| HX-01-PMP | HTM circulation skid | R-rough to D-rough heat recovery circulation loop | 0.250 | 14.50 | 15.466 | n/a | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |

### Utility-Coupled Package Inventory

| ID | Type | Service | Volume (m3) | Duty (kW) | MoC | Design Basis |
| --- | --- | --- | --- | --- | --- | --- |
| V-101 | Flash drum | Intermediate disengagement | 4860.750 | 0.000 | Carbon Steel | Generic separator hold-up |
| HX-01 | HTM loop exchanger | R-rough to D-rough heat recovery | 542.949 | 34024.794 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-CTRL | Utility control package | R-rough to D-rough heat recovery control valves, instrumentation, and bypass station | 0.150 | 0.000 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-HDR | Shared HTM header manifold | R-rough to D-rough heat recovery network header and isolation package | 0.851 | 34024.794 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-PMP | HTM circulation skid | R-rough to D-rough heat recovery circulation loop | 0.250 | 15.466 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-EXP | HTM expansion tank | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | 2.835 | 0.000 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-RV | HTM relief package | R-rough to D-rough heat recovery thermal relief and collection package | 1.309 | 0.000 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02 | Heat integration exchanger | D-rough to E-rough heat recovery | 30.379 | 8506.198 | SS316 | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02-CTRL | Utility control package | D-rough to E-rough heat recovery control valves, instrumentation, and bypass station | 0.150 | 0.000 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |

### Datasheet Coverage Matrix

| Equipment Family | Datasheet Count | Representative IDs |
| --- | --- | --- |
| Distillation column | 1 | PU-201 |
| Flash drum | 1 | V-101 |
| HTM circulation skid | 1 | HX-01-PMP |
| HTM expansion tank | 1 | HX-01-EXP |
| HTM loop exchanger | 1 | HX-01 |
| HTM relief package | 1 | HX-01-RV |
| Heat exchanger | 1 | E-101 |
| Heat integration exchanger | 1 | HX-02 |
| Reactor | 1 | R-101 |
| Shared HTM header manifold | 1 | HX-01-HDR |
| Storage tank | 1 | TK-301 |
| Transfer pump | 1 | TK-301_pump |
| Utility control package | 2 | HX-01-CTRL, HX-02-CTRL |

### Equipment-by-Equipment Sizing Summary

| ID | Type | Service | Volume (m3) | Duty (kW) | Design T (C) | Design P (bar) | MoC | Design Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | Tubular Plug Flow Hydrator | 27004.165 | 7600.213 | 255.0 | 20.00 | Carbon Steel | tubular_plug_flow_hydrator selected at 1.00 h residence time and 0.960 conversion basis. |
| PU-201 | Distillation column | Distillation and purification train | 21.206 | 3179.805 | 140.0 | 2.00 | Carbon Steel | 7 stages equivalent |
| V-101 | Flash drum | Intermediate disengagement | 4860.750 | 0.000 | 85.0 | 3.00 | Carbon Steel | Generic separator hold-up |
| E-101 | Heat exchanger | R-rough to D-rough heat recovery | 723.932 | 34024.794 | 180.0 | 8.00 | Carbon Steel | LMTD 8.0 K |
| TK-301 | Storage tank | Ethylene Glycol storage via vertical tank farm | 8580.903 | 0.000 | 45.0 | 1.20 | SS304 | 14.1 days inventory |
| HX-01 | HTM loop exchanger | R-rough to D-rough heat recovery | 542.949 | 34024.794 | 213.0 | 11.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-CTRL | Utility control package | R-rough to D-rough heat recovery control valves, instrumentation, and bypass station | 0.150 | 0.000 | 203.0 | 9.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-HDR | Shared HTM header manifold | R-rough to D-rough heat recovery network header and isolation package | 0.851 | 34024.794 | 205.0 | 14.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-PMP | HTM circulation skid | R-rough to D-rough heat recovery circulation loop | 0.250 | 15.466 | 205.0 | 14.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-EXP | HTM expansion tank | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | 2.835 | 0.000 | 210.0 | 6.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-01-RV | HTM relief package | R-rough to D-rough heat recovery thermal relief and collection package | 1.309 | 0.000 | 213.0 | 13.50 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_01; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02 | Heat integration exchanger | D-rough to E-rough heat recovery | 30.379 | 8506.198 | 162.0 | 6.50 | SS316 | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |
| HX-02-CTRL | Utility control package | D-rough to E-rough heat recovery control valves, instrumentation, and bypass station | 0.150 | 0.000 | 158.0 | 5.00 | Carbon steel | Utility train package item for omega_catalytic_pinch_htm__shared_htm_step_02; island omega_catalytic_pinch_htm__shared_htm_shared_htm_01; header 1; cluster - |