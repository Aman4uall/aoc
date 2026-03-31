## Instrumentation and Process Control

The deterministic control plan derives 10 loops from 13 major equipment items and 6 utility services. Loops are attached to thermal, pressure, level, feed-stability, startup/shutdown, and override risks rather than generated as generic instrumentation text.

### Control Philosophy

| Parameter | Value |
| --- | --- |
| Selected architecture | cascade_override |
| Critical units | R-101, PU-201, TK-301, HX-01-EXP |
| Loop count | 10 |
| Utility services linked | 6 |
| High-criticality loops | 3 |

### Control Architecture Decision

Selected control architecture: Cascade temperature/pressure control with override protection.

Critical units: R-101, PU-201, TK-301, HX-01-EXP.

Existing control loops captured: 10.

### Loop Objective Matrix

| Loop | Unit | Controlled Variable | Manipulated Variable | Objective | Disturbance Basis | Criticality |
| --- | --- | --- | --- | --- | --- | --- |
| TIC-R-101 | R-101 | Tubular Plug Flow Hydrator temperature | Cooling or heating duty | Maintain reactor temperature within the conversion/selectivity window. | Reaction heat release, feed-ratio drift, and utility temperature fluctuations. | high |
| PIC-R-101 | R-101 | Tubular Plug Flow Hydrator pressure | Back-pressure control | Keep the reactor inside the design-pressure and phase-stability envelope. | Gas evolution, condenser instability, and downstream restriction changes. | high |
| FRC-R-101 | R-101 | Tubular Plug Flow Hydrator feed ratio | Lead/lag feed flow trim | Maintain stoichiometric or dilution ratio through startup and steady operation. | Upstream feed composition change and pump-speed drift. | medium |
| LIC-PU-201 | PU-201 | Distillation and purification train level | Bottoms withdrawal | Maintain bottoms inventory and protect internals from flooding or dry operation. | Feed swings, vapor-rate changes, and downstream withdrawal interruptions. | medium |
| PIC-PU-201 | PU-201 | Distillation and purification train pressure | Condenser or vent-duty trim | Hold the main separation unit on its target pressure / vacuum basis. | Condenser duty swings, vent-load changes, and upstream composition disturbance. | high |
| FIC-PU-201 | PU-201 | Distillation and purification train quality driver | Reflux / solvent / circulation flow | Hold the separation-driving flow that protects product quality and capture/yield targets. | Feed flow/composition variation and utility availability changes. | medium |
| LIC-TK-301 | TK-301 | Ethylene Glycol storage via vertical tank farm level | Dispatch pump permissive | Prevent overflow and dry-running while maintaining dispatch-ready inventory. | Filling / dispatch mismatch and restart buffer drawdown. | medium |
| PIC-TK-301 | TK-301 | Ethylene Glycol storage via vertical tank farm blanketing pressure | Nitrogen make-up / vent trim | Maintain safe storage pressure and inert atmosphere for inventory handling. | Ambient temperature swing, filling surge, and dispatch withdrawal. | medium |
| LIC-HX-01-EXP | HX-01-EXP | R-rough to D-rough heat recovery HTM expansion and inventory hold-up level | Dispatch pump permissive | Prevent overflow and dry-running while maintaining dispatch-ready inventory. | Filling / dispatch mismatch and restart buffer drawdown. | medium |
| PIC-HX-01-EXP | HX-01-EXP | R-rough to D-rough heat recovery HTM expansion and inventory hold-up blanketing pressure | Nitrogen make-up / vent trim | Maintain safe storage pressure and inert atmosphere for inventory handling. | Ambient temperature swing, filling surge, and dispatch withdrawal. | medium |

### Controlled and Manipulated Variable Register

| Loop | Unit | Family | Controlled Variable | Manipulated Variable | Sensor | Actuator | Criticality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIC-R-101 | R-101 | temperature_cascade | Tubular Plug Flow Hydrator temperature | Cooling or heating duty | Temperature transmitter | Control valve | high |
| PIC-R-101 | R-101 | pressure_override | Tubular Plug Flow Hydrator pressure | Back-pressure control | Pressure transmitter | Control valve | high |
| FRC-R-101 | R-101 | feed_ratio | Tubular Plug Flow Hydrator feed ratio | Lead/lag feed flow trim | Ratio station with flow transmitters | Feed control valve / VFD | medium |
| LIC-PU-201 | PU-201 | inventory_level | Distillation and purification train level | Bottoms withdrawal | Level transmitter | Control valve | medium |
| PIC-PU-201 | PU-201 | pressure_regulatory | Distillation and purification train pressure | Condenser or vent-duty trim | Pressure transmitter | Control valve | high |
| FIC-PU-201 | PU-201 | quality_reflux_or_solvent | Distillation and purification train quality driver | Reflux / solvent / circulation flow | Flow transmitter with composition or ratio bias | Control valve / VFD | medium |
| LIC-TK-301 | TK-301 | inventory_level | Ethylene Glycol storage via vertical tank farm level | Dispatch pump permissive | Level transmitter | Pump trip | medium |
| PIC-TK-301 | TK-301 | blanketing_pressure | Ethylene Glycol storage via vertical tank farm blanketing pressure | Nitrogen make-up / vent trim | Pressure transmitter | Blanketing valve | medium |
| LIC-HX-01-EXP | HX-01-EXP | inventory_level | R-rough to D-rough heat recovery HTM expansion and inventory hold-up level | Dispatch pump permissive | Level transmitter | Pump trip | medium |
| PIC-HX-01-EXP | HX-01-EXP | blanketing_pressure | R-rough to D-rough heat recovery HTM expansion and inventory hold-up blanketing pressure | Nitrogen make-up / vent trim | Pressure transmitter | Blanketing valve | medium |

### Startup, Shutdown, and Override Basis

| Loop | Startup Logic | Shutdown Logic | Override / Permissive Basis |
| --- | --- | --- | --- |
| TIC-R-101 | Ramp utility service first, then introduce feed under low-rate permissive until reactor temperature stabilizes. | Isolate feeds, hold cooling/inerting until the reactor contents fall below the safe residual-temperature limit. | High-high temperature override closes feed and drives maximum cooling / quench response. |
| PIC-R-101 | Hold reactor on pressure trim while vent / recycle path is proven open before feed escalation. | Depressure through the controlled path after feed isolation and maintain inert purge if required. | High-pressure override opens relief / vent control path and blocks further feed increase. |
| FRC-R-101 | Keep secondary feed on ratio-follow mode to the lead feed until circulation and temperature are stable. | Drive secondary feed closed first, then ramp down the lead feed to avoid off-ratio inventory. | High-reactor-temperature or low-circulation permissive forces low-feed bias and ratio hold. |
| LIC-PU-201 | Establish reflux / circulation first, then release bottoms under minimum-level permissive. | Reduce feed, maintain reflux / boil-up as needed, and drain to the safe low-level setpoint. | High-high level overrides bottoms withdrawal or feed cutback depending on service family. |
| PIC-PU-201 | Pull pressure into band before advancing feed and enabling automatic reflux or solvent circulation. | Unload feed, keep pressure control active during rundown, then isolate to safe ambient / inert condition. | Low-pressure / high-pressure override biases vent or condenser duty to prevent air ingress or overpressure. |
| FIC-PU-201 | Run on minimum stable recycle/reflux, then close quality target once pressure and inventory loops settle. | Return manipulated flow to rundown minimum before stopping duty or feed sources. | Analyzer or high-differential-pressure override trims reflux / solvent / circulation to a safe fallback value. |
| LIC-TK-301 | Keep dispatch permissive blocked until minimum operating inventory is restored. | Stop transfer on low-low level and retain restart inventory if the plant is entering outage mode. | High-high level override stops filling and opens alternate routing if configured. |
| PIC-TK-301 | Establish blanketing pressure before opening transfer inlets or outlets. | Maintain minimum blanketing setpoint through static storage and isolation. | High-pressure / low-pressure override trims venting or nitrogen make-up ahead of tank relief action. |
| LIC-HX-01-EXP | Keep dispatch permissive blocked until minimum operating inventory is restored. | Stop transfer on low-low level and retain restart inventory if the plant is entering outage mode. | High-high level override stops filling and opens alternate routing if configured. |
| PIC-HX-01-EXP | Establish blanketing pressure before opening transfer inlets or outlets. | Maintain minimum blanketing setpoint through static storage and isolation. | High-pressure / low-pressure override trims venting or nitrogen make-up ahead of tank relief action. |

### Alarm and Interlock Basis

| Loop | Deviation | Protective Layer | Purpose |
| --- | --- | --- | --- |
| TIC-R-101 | High/low Tubular Plug Flow Hydrator temperature | alarm + override / interlock response | Feeds reactor runaway protection, utility permissives, and emergency feed isolation logic. |
| PIC-R-101 | High/low Tubular Plug Flow Hydrator pressure | alarm + override / interlock response | Supports relief sizing assumptions, pressure alarms, and shutdown permissives. |
| FRC-R-101 | High/low Tubular Plug Flow Hydrator feed ratio | alarm + operator response | Links throughput control to reactor temperature and pressure safeguard logic. |
| LIC-PU-201 | High/low Distillation and purification train level | alarm + operator response | Protects internals, reboiler circulation, and downstream product-quality stability. |
| PIC-PU-201 | High/low Distillation and purification train pressure | alarm + override / interlock response | Feeds column pressure alarms, vacuum protection, and offgas routing logic. |
| FIC-PU-201 | High/low Distillation and purification train quality driver | alarm + operator response | Ties separation quality control to utility duty, flooding risk, and off-spec prevention. |
| LIC-TK-301 | High/low Ethylene Glycol storage via vertical tank farm level | alarm + operator response | Supports storage overflow protection and working-inventory assumptions. |
| PIC-TK-301 | High/low Ethylene Glycol storage via vertical tank farm blanketing pressure | alarm + operator response | Links storage pressure control to inerting and vent-protection assumptions. |
| LIC-HX-01-EXP | High/low R-rough to D-rough heat recovery HTM expansion and inventory hold-up level | alarm + operator response | Supports storage overflow protection and working-inventory assumptions. |
| PIC-HX-01-EXP | High/low R-rough to D-rough heat recovery HTM expansion and inventory hold-up blanketing pressure | alarm + operator response | Links storage pressure control to inerting and vent-protection assumptions. |

### Utility-Integrated Control Basis

| Utility | Load | Control Linkage |
| --- | --- | --- |
| Steam | 71672.825 kg/h | temperature / pressure loops depend on steam or cooling-service availability |
| Cooling water | 2778.003 m3/h | temperature / pressure loops depend on steam or cooling-service availability |
| Electricity | 28732.696 kW | inventory, purge, or protective logic references this plant utility service |
| DM water | 2.000 m3/h | inventory, purge, or protective logic references this plant utility service |
| Nitrogen | 3.608 Nm3/h | inventory, purge, or protective logic references this plant utility service |
| Heat-integration auxiliaries | 16.166 kW | inventory, purge, or protective logic references this plant utility service |

### Control Loop Sheets

| Loop | Unit | Family | Sensor | Actuator | Objective | Startup Basis | Override Basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIC-R-101 | R-101 | temperature_cascade | Temperature transmitter | Control valve | Maintain reactor temperature within the conversion/selectivity window. | Ramp utility service first, then introduce feed under low-rate permissive until reactor temperature stabilizes. | High-high temperature override closes feed and drives maximum cooling / quench response. |
| PIC-R-101 | R-101 | pressure_override | Pressure transmitter | Control valve | Keep the reactor inside the design-pressure and phase-stability envelope. | Hold reactor on pressure trim while vent / recycle path is proven open before feed escalation. | High-pressure override opens relief / vent control path and blocks further feed increase. |
| FRC-R-101 | R-101 | feed_ratio | Ratio station with flow transmitters | Feed control valve / VFD | Maintain stoichiometric or dilution ratio through startup and steady operation. | Keep secondary feed on ratio-follow mode to the lead feed until circulation and temperature are stable. | High-reactor-temperature or low-circulation permissive forces low-feed bias and ratio hold. |
| LIC-PU-201 | PU-201 | inventory_level | Level transmitter | Control valve | Maintain bottoms inventory and protect internals from flooding or dry operation. | Establish reflux / circulation first, then release bottoms under minimum-level permissive. | High-high level overrides bottoms withdrawal or feed cutback depending on service family. |
| PIC-PU-201 | PU-201 | pressure_regulatory | Pressure transmitter | Control valve | Hold the main separation unit on its target pressure / vacuum basis. | Pull pressure into band before advancing feed and enabling automatic reflux or solvent circulation. | Low-pressure / high-pressure override biases vent or condenser duty to prevent air ingress or overpressure. |
| FIC-PU-201 | PU-201 | quality_reflux_or_solvent | Flow transmitter with composition or ratio bias | Control valve / VFD | Hold the separation-driving flow that protects product quality and capture/yield targets. | Run on minimum stable recycle/reflux, then close quality target once pressure and inventory loops settle. | Analyzer or high-differential-pressure override trims reflux / solvent / circulation to a safe fallback value. |
| LIC-TK-301 | TK-301 | inventory_level | Level transmitter | Pump trip | Prevent overflow and dry-running while maintaining dispatch-ready inventory. | Keep dispatch permissive blocked until minimum operating inventory is restored. | High-high level override stops filling and opens alternate routing if configured. |
| PIC-TK-301 | TK-301 | blanketing_pressure | Pressure transmitter | Blanketing valve | Maintain safe storage pressure and inert atmosphere for inventory handling. | Establish blanketing pressure before opening transfer inlets or outlets. | High-pressure / low-pressure override trims venting or nitrogen make-up ahead of tank relief action. |
| LIC-HX-01-EXP | HX-01-EXP | inventory_level | Level transmitter | Pump trip | Prevent overflow and dry-running while maintaining dispatch-ready inventory. | Keep dispatch permissive blocked until minimum operating inventory is restored. | High-high level override stops filling and opens alternate routing if configured. |
| PIC-HX-01-EXP | HX-01-EXP | blanketing_pressure | Pressure transmitter | Blanketing valve | Maintain safe storage pressure and inert atmosphere for inventory handling. | Establish blanketing pressure before opening transfer inlets or outlets. | High-pressure / low-pressure override trims venting or nitrogen make-up ahead of tank relief action. |