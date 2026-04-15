# BAC PPT Slide Draft: Slides 13-24

This file contains the Phase 7 draft content for Slides 13-24 of the BAC PPT.

These slides cover:
- PFD continuation
- process description
- mass and energy basis
- reactor design
- equipment design and sizing
- mechanical design
- control opening section

## Slide 13: Process Flow Diagram II

**Slide Title**

Process Flow Diagram II

**Primary Visual**

Use [pfd_sheet_2.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_2.png)

**Caption**

Cleanup, finishing, storage, and waste-handling section of the selected BAC process train.

**Design Note**

- Keep the figure dominant
- Do not place a large table on this slide

## Slide 14: Process Description

**Slide Title**

Process Description

**On-Slide Content**

1. Dodecyldimethylamine and benzyl chloride are received, stored, and prepared in the feed-handling section.
2. The reactants are sent to the continuous quaternization reactor, where BAC is formed in the liquid phase.
3. The reactor effluent is routed to a primary flash step to remove volatile components and stabilize the downstream train.
4. The partially cleaned stream is concentrated and stripped to reduce volatile and light-end burden.
5. A purification section refines the product to the required sold-solution quality basis.
6. The finished BAC solution is transferred to storage for dispatch, while purge and waste streams are routed to controlled handling.

**Bottom Note**

The selected process architecture is designed around volatile cleanup and solution finishing rather than active-product distillation.

## Slide 15: Material Balance Summary

**Slide Title**

Material Balance Summary

**Primary Table**

Use `T-06` from [bac_ppt_curated_tables.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_curated_tables.md)

| Stream / Basis Item | Value |
| --- | --- |
| Feed to reactor | 3,461.60 kg/h |
| Product basis | 6,313.13 kg/h sold solution |
| Active basis | 3,156.57 kg/h |
| Design conversion | 95.0% |
| Major feed components | Dodecyldimethylamine, benzyl chloride |
| Major product basis | BAC solution with cleanup and finishing |

**Bottom Note**

This slide presents the plant balance basis only; the full stream ledger is intentionally kept out of the main deck.

## Slide 16: Energy Balance Summary

**Slide Title**

Energy Balance Summary

**Primary Table**

Use `T-07`

| Utility | Load | Units | Annualized Usage |
| --- | --- | --- | --- |
| Steam | 2,277.14 | kg/h | 18,034,917.1 kg/y |
| Cooling water | 107.59 | m3/h | 852,136.6 m3/y |
| Electricity | 151.56 | kW | 1,200,323.5 kWh/y |
| DM water | 2.00 | m3/h | 15,840.0 m3/y |
| Nitrogen | 3.00 | Nm3/h | 23,760.0 Nm3/y |

**Bottom Takeaway**

The thermal burden is dominated by steam and cooling-water service linked to concentration, purification, and reactor heat removal.

## Slide 17: Heat Integration and Utilities Basis

**Slide Title**

Heat Integration and Utilities Basis

**On-Slide Content**

- The current BAC design is carried forward on a `no recovery` heat-integration case.
- Residual utility demand remains:
  - Hot utility: `359.13 kW`
  - Cold utility: `567.12 kW`
- Steam, cooling water, electricity, nitrogen, and DM water are the principal utility services.
- Utility routing and control are integrated with the selected continuous liquid-train process architecture.

**Bottom Note**

The present utility strategy is suitable for feasibility-stage evaluation and can be tightened further during detailed optimization.

## Slide 18: Reactor Design Basis

**Slide Title**

Reactor Design Basis

**Primary Table**

Use `T-08`

| Parameter | Value |
| --- | --- |
| Reactor tag | R-101 |
| Adopted reactor basis | Glass-lined agitated reactor with external recirculation loop |
| Residence time | 25.0 h |
| Design conversion | 0.95 |
| Design temperature | 85.0 degC |
| Design pressure | 3.01 bar |
| Heat duty | 257.12 kW |
| Runaway risk label | Moderate |

**Bottom Statement**

R-101 is presented on the adopted glass-lined, externally cooled reactor basis selected for safe preliminary handling of the exothermic quaternization service.

## Slide 19: Reactor Sizing Summary

**Slide Title**

Reactor Sizing Summary

**Primary Table**

Use `T-09`

| Parameter | Value |
| --- | --- |
| Design volume | 123.76 m3 |
| Liquid holdup | 101.44 m3 |
| Shell diameter | 4.00 m |
| Shell length | 9.85 m |
| Vessel height without skirt | 11.85 m |
| External-loop exchanger area | 15.00 m2 |
| Agitator arrangement | 3 x retreat-curve agitator |

**Bottom Note**

The adopted geometry reflects the final report-basis reactor sizing and excludes superseded jacket-only wording from historical artifacts.

## Slide 20: Reactor Mechanical Design

**Slide Title**

Reactor Mechanical Design and MoC

**Primary Table**

Use `T-10`

| Parameter | Value |
| --- | --- |
| Reactor type | Glass-lined vertical reactor |
| Pressure boundary basis | Carbon-steel shell with glass lining |
| Head type | 2:1 ellipsoidal heads |
| Cooling philosophy | External pump-around loop with exchanger |
| Heat-transfer area | 15.00 m2 |
| Runaway risk category | Moderate |

**Side / Bottom Bullets**

- Glass lining is preferred to support corrosive quaternary-ammonium service.
- The external recirculation loop provides controlled heat removal for the exothermic reaction.
- Mechanical design at this stage remains preliminary and should be refined further during detailed design.

## Slide 21: Major Process Unit Design

**Slide Title**

Major Process Unit Design

**Primary Table**

Use `T-11`

| ID | Unit | Service | Volume | Duty | Design T | Design P |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | Quaternization reaction | 123.76 m3 | 257.12 kW | 85.0 degC | 3.01 bar |
| PU-201 | Distillation column | Purification train | 21.21 m3 | 1,391.58 kW | 140.0 degC | 2.00 bar |
| V-101 | Flash drum | Intermediate disengagement | 22.28 m3 | 0.00 kW | 85.0 degC | 3.00 bar |
| E-101 | Heat exchanger | Thermal service | 8.17 m3 | 637.18 kW | 180.0 degC | 8.00 bar |

**Bottom Note**

The selected BAC process is carried by a compact unit train dominated by reaction, volatile cleanup, purification, and storage service.

## Slide 22: Heat Exchanger and Thermal Equipment

**Slide Title**

Heat Exchanger and Thermal Equipment

**Primary Table**

Use `T-12`

| Equipment | Service | Duty | Design T | Design P | MoC |
| --- | --- | --- | --- | --- | --- |
| E-101 | Shell-and-tube exchanger | 637.18 kW | 180.0 degC | 8.00 bar | Carbon steel |
| R-101 external loop | Reactor heat removal | 257.12 kW | 85.0 degC | 3.01 bar | Integrated with GLR loop |

**Bottom Takeaway**

Thermal equipment design is driven by reactor temperature control and volatile-cleanup / purification duties.

## Slide 23: Pumps, Storage, and Auxiliary Equipment

**Slide Title**

Pumps, Storage, and Auxiliary Equipment

**Primary Table**

Use `T-13`

| Equipment | Service | Key Size / Duty | Design Basis |
| --- | --- | --- | --- |
| TK-301 | BAC product storage tank | 1,969.85 m3 total volume | 11.6 days inventory |
| TK-301 Pump | Product transfer | 219.85 m3/h, 52.0 m head, 36.58 kW | Dispatch and tank-farm transfer |

**Side Note**

Storage and transfer equipment are sized to support continuous production, dispatch buffering, and inventory control under the selected operating policy.

## Slide 24: Equipment Design Summary

**Slide Title**

Equipment Design Summary

**On-Slide Content**

- The BAC plant is built around a continuous quaternization and cleanup train with a limited number of major equipment items.
- Reactor R-101 remains the key safety-critical and design-critical unit.
- PU-201 and E-101 dominate the thermal and purification burden.
- TK-301 and its transfer service define the product-handling and dispatch basis.
- The overall equipment set is consistent with a compact continuous liquid-process facility rather than a solids-heavy plant layout.

**Bottom Note**

The equipment package shown here is intended for feasibility-stage sizing, layout planning, and cost estimation.

