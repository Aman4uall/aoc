## Energy Balance

### Overall Energy Summary

| Basis | Value | Units |
| --- | --- | --- |
| Total heating duty | 5781.464 | kW |
| Total cooling duty | 8224.582 | kW |
| Net external duty | -2443.118 | kW |
| Thermal packets | 3 | count |
| Recovery candidates | 2 | count |
| Recoverable packet duty | 624.369 | kW |

### Unit Duty Summary

| Unit | Section | Duty Type | Heating (kW) | Cooling (kW) | Notes |
| --- | --- | --- | --- | --- | --- |
| E-101 | - | sensible | 4532.727 | 0.000 | Feed preheat to operating temperature. |
| R-101 | - | reaction | 0.000 | 7600.213 | Net reactor thermal duty from the selected thermodynamic basis. |
| SEP-201 | - | sensible | 1248.737 | 624.369 | Generic purification duty. |

### Section Duty Summary

| Section | Label | Heating (kW) | Cooling (kW) | Recoverable (kW) | Status |
| --- | --- | --- | --- | --- | --- |
| feed_handling | Feed handling | 0.000 | 0.000 | 0.000 | converged |
| reaction | Reaction | 0.000 | 0.000 | 0.000 | converged |
| primary_recovery | Primary recovery | 0.000 | 0.000 | 0.000 | converged |
| recycle_recovery_carbonate_loop_cleanup | Carbonate loop cleanup | 0.000 | 0.000 | 0.000 | estimated |
| purification | Purification | 0.000 | 0.000 | 0.000 | estimated |

### Unit Thermal Packet Summary

| Packet | Unit | Section | Type | Heating (kW) | Cooling (kW) | Hot In (C) | Hot Out (C) | Cold In (C) | Cold Out (C) | Recoverable (kW) | Candidate Media |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E-101_thermal_packet | E-101 | - | sensible | 4532.727 | 0.000 | 270.0 | 255.0 | 225.0 | 240.0 | 0.000 | steam, hot oil |
| R-101_thermal_packet | R-101 | - | reaction | 0.000 | 7600.213 | 240.0 | 195.0 | 30.0 | 42.0 | 0.000 | Dowtherm A, cooling water |
| SEP-201_thermal_packet | SEP-201 | - | sensible | 1248.737 | 624.369 | 270.0 | 245.0 | 30.0 | 75.0 | 624.369 | cooling water, steam, hot oil |

### Recovery Candidate Summary

| Candidate | Source Unit | Sink Unit | Topology | Recovered Duty (kW) | Min Approach (C) | Feasible | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-101_to_SEP-201 | R-101 | SEP-201 | direct | 1123.863 | 20.0 | yes | Direct packet-level recovery candidate. |
| SEP-201_to_E-101 | SEP-201 | E-101 | direct | 561.932 | 20.0 | yes | Direct packet-level recovery candidate. |

### Utility Consumption Basis

| Unit | Route | Candidate Media | Peak Duty (kW) | Recoverable Duty (kW) | Service |
| --- | --- | --- | --- | --- | --- |
| E-101 | omega_catalytic | steam, hot oil | 4532.727 | 0.000 | Feed preheat to operating temperature. |
| R-101 | omega_catalytic | Dowtherm A, cooling water | 7600.213 | 0.000 | Net reactor thermal duty from the selected thermodynamic basis. |
| SEP-201 | omega_catalytic | cooling water, steam, hot oil | 1248.737 | 624.369 | Generic purification duty. |

### Route-Family Duty Focus

| Unit | Duty Type | Heating (kW) | Cooling (kW) | Section | Notes |
| --- | --- | --- | --- | --- | --- |
| E-101 | sensible | 4532.727 | 0.000 | - | Feed preheat to operating temperature. |
| R-101 | reaction | 0.000 | 7600.213 | - | Net reactor thermal duty from the selected thermodynamic basis. |

### Energy-Balance Calculation Traces

| Trace | Formula | Inputs | Result | Notes |
| --- | --- | --- | --- | --- |
| Feed preheat duty | Q = m * Cp * dT / 3600 | m=25952.368 kg/h; dT=215.0 K | 4532.727 kW | - |
| Reaction duty | Q = |n * dH| / 3600 | n=402.364225 kmol/h; dH=-68.000 kJ/mol | 7600.213 kW | - |
| Unitwise duty expansion | duty_count = number of explicit unit duties in the solved energy envelope | - | 3 duties | The generic energy solver now emits duty rows for each major process section rather than a single family-level total. |
| Thermal packet expansion | packet_count = number of unitwise thermal packets carried into utility and equipment design | - | 3 packets | These packets preserve unit-level hot and cold thermal interfaces downstream. |
| Packet-derived exchanger candidates | candidate_count = number of packet-to-packet heat-recovery candidates | - | 2 candidates | These candidates seed utility-architecture selection and detailed exchanger sizing. |
| Composition-driven thermal basis | Cp and latent-duty basis are derived from solved unit composition states and mixture-property packages | feed_state=feed_prep_composition_state; primary_state=primary_flash_composition_state; purification_state=purification_composition_state; feed_cp=2.816; product_cp=2.452; mixture_packages=5 | generic family | The energy solver now consumes mixture-property packages first and only retains heuristics as a compatibility fallback. |