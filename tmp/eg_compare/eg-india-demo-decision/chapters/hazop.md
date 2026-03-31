## HAZOP

### HAZOP Coverage Summary

| Parameter | Value |
| --- | --- |
| Node count | 7 |
| High-severity route hazards | 0 |
| Control loops linked | 10 |
| Coverage summary | 7 HAZOP nodes across 4 node families derived from the selected flowsheet and equipment list. |
| Node families | column_or_main_separation, reactor, storage, thermal_exchange |

### HAZOP Node Basis

| Node | Family | Design Intent | Parameter | Guide Word | Deviation | Linked Control Loops |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | reactor | Maintain controlled conversion at safe temperature and pressure. | Temperature | More | Higher than intended reactor temperature | TIC-R-101; PIC-R-101; FRC-R-101 |
| PU-201 | column_or_main_separation | Maintain stable separation pressure, inventory, and quality-driving internal flows. | Pressure | Less | Lower than intended main-separation pressure | LIC-PU-201; PIC-PU-201; FIC-PU-201 |
| E-101 | thermal_exchange | Deliver required thermal duty without tube-side / shell-side upset or loss of containment. | Heat transfer | Less | Lower than intended thermal duty | TIC-R-101; PIC-R-101 |
| TK-301 | storage | Hold safe inventory, containment, and blanketing during receipt, storage, and dispatch. | Level | More | Higher than intended storage level | LIC-TK-301; PIC-TK-301 |
| HX-01 | thermal_exchange | Deliver required thermal duty without tube-side / shell-side upset or loss of containment. | Heat transfer | Less | Lower than intended thermal duty | TIC-R-101; PIC-R-101 |
| HX-01-EXP | storage | Hold safe inventory, containment, and blanketing during receipt, storage, and dispatch. | Level | More | Higher than intended storage level | LIC-HX-01-EXP; PIC-HX-01-EXP |
| HX-02 | thermal_exchange | Deliver required thermal duty without tube-side / shell-side upset or loss of containment. | Heat transfer | Less | Lower than intended thermal duty | TIC-R-101; PIC-R-101 |

### Critical Node Summary

| Node | Family | Deviation | Parameter | Guide Word | Severity | Consequences | Safeguards |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | reactor | Higher than intended reactor temperature | Temperature | More | high | Runaway tendency; Selectivity loss; Pressure rise and emergency shutdown risk | TIC-R-101; PIC-R-101; FRC-R-101 |
| PU-201 | column_or_main_separation | Lower than intended main-separation pressure | Pressure | Less | high | Air ingress; Column instability; Off-spec separation performance | LIC-PU-201; PIC-PU-201; FIC-PU-201 |
| E-101 | thermal_exchange | Lower than intended thermal duty | Heat transfer | Less | medium | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |
| TK-301 | storage | Higher than intended storage level | Level | More | medium | Overflow; Containment loss; Transfer spill / emissions event | LIC-TK-301; PIC-TK-301 |
| HX-01 | thermal_exchange | Lower than intended thermal duty | Heat transfer | Less | medium | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |
| HX-01-EXP | storage | Higher than intended storage level | Level | More | medium | Overflow; Containment loss; Transfer spill / emissions event | LIC-HX-01-EXP; PIC-HX-01-EXP |
| HX-02 | thermal_exchange | Lower than intended thermal duty | Heat transfer | Less | medium | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |

### Deviation Cause-Consequence Matrix

| Node | Deviation | Causes | Consequences | Safeguards |
| --- | --- | --- | --- | --- |
| R-101 | Higher than intended reactor temperature | Cooling failure; Excess reactant feed; Utility temperature excursion | Runaway tendency; Selectivity loss; Pressure rise and emergency shutdown risk | TIC-R-101; PIC-R-101; FRC-R-101 |
| PU-201 | Lower than intended main-separation pressure | Vacuum overshoot; Condenser instability; Vent control malfunction | Air ingress; Column instability; Off-spec separation performance | LIC-PU-201; PIC-PU-201; FIC-PU-201 |
| E-101 | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |
| TK-301 | Higher than intended storage level | Blocked outlet; Dispatch mismatch; Filling valve left open | Overflow; Containment loss; Transfer spill / emissions event | LIC-TK-301; PIC-TK-301 |
| HX-01 | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |
| HX-01-EXP | Higher than intended storage level | Blocked outlet; Dispatch mismatch; Filling valve left open | Overflow; Containment loss; Transfer spill / emissions event | LIC-HX-01-EXP; PIC-HX-01-EXP |
| HX-02 | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 |

### HAZOP Node Register

| Node | Family | Parameter | Guide Word | Deviation | Causes | Consequences | Safeguards | Linked Loops | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | reactor | Temperature | More | Higher than intended reactor temperature | Cooling failure; Excess reactant feed; Utility temperature excursion | Runaway tendency; Selectivity loss; Pressure rise and emergency shutdown risk | TIC-R-101; PIC-R-101; FRC-R-101 | TIC-R-101; PIC-R-101; FRC-R-101 | Add high-high temperature trip, emergency feed isolation, and confirm cooling-failure response sequence. |
| PU-201 | column_or_main_separation | Pressure | Less | Lower than intended main-separation pressure | Vacuum overshoot; Condenser instability; Vent control malfunction | Air ingress; Column instability; Off-spec separation performance | LIC-PU-201; PIC-PU-201; FIC-PU-201 | LIC-PU-201; PIC-PU-201; FIC-PU-201 | Protect low-pressure operation, verify oxygen ingress response, and confirm safe reflux / circulation fallback. |
| E-101 | thermal_exchange | Heat transfer | Less | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 | TIC-R-101; PIC-R-101 | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. |
| TK-301 | storage | Level | More | Higher than intended storage level | Blocked outlet; Dispatch mismatch; Filling valve left open | Overflow; Containment loss; Transfer spill / emissions event | LIC-TK-301; PIC-TK-301 | LIC-TK-301; PIC-TK-301 | Provide level interlocks, overflow routing checks, and confirm dispatch / receipt isolation logic. |
| HX-01 | thermal_exchange | Heat transfer | Less | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 | TIC-R-101; PIC-R-101 | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. |
| HX-01-EXP | storage | Level | More | Higher than intended storage level | Blocked outlet; Dispatch mismatch; Filling valve left open | Overflow; Containment loss; Transfer spill / emissions event | LIC-HX-01-EXP; PIC-HX-01-EXP | LIC-HX-01-EXP; PIC-HX-01-EXP | Provide level interlocks, overflow routing checks, and confirm dispatch / receipt isolation logic. |
| HX-02 | thermal_exchange | Heat transfer | Less | Lower than intended thermal duty | Fouling; Utility interruption; Flow maldistribution | Poor temperature control; Downstream off-spec operation; Potential pressure upset in linked unit | TIC-R-101; PIC-R-101 | TIC-R-101; PIC-R-101 | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. |

### Recommendation Register

| Node | Priority | Status | Recommendation | Primary Causes |
| --- | --- | --- | --- | --- |
| R-101 | high | open | Add high-high temperature trip, emergency feed isolation, and confirm cooling-failure response sequence. | Cooling failure; Excess reactant feed; Utility temperature excursion |
| PU-201 | high | open | Protect low-pressure operation, verify oxygen ingress response, and confirm safe reflux / circulation fallback. | Vacuum overshoot; Condenser instability; Vent control malfunction |
| E-101 | medium | open | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. | Fouling; Utility interruption; Flow maldistribution |
| TK-301 | medium | open | Provide level interlocks, overflow routing checks, and confirm dispatch / receipt isolation logic. | Blocked outlet; Dispatch mismatch; Filling valve left open |
| HX-01 | medium | open | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. | Fouling; Utility interruption; Flow maldistribution |
| HX-01-EXP | medium | open | Provide level interlocks, overflow routing checks, and confirm dispatch / receipt isolation logic. | Blocked outlet; Dispatch mismatch; Filling valve left open |
| HX-02 | medium | open | Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response. | Fouling; Utility interruption; Flow maldistribution |