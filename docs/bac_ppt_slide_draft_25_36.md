# BAC PPT Slide Draft: Slides 25-36

This file contains the Phase 7 draft content for Slides 25-36 of the BAC PPT.

These slides complete the deck with:
- instrumentation and control
- HAZOP and SHE / waste basis
- site and layout
- CAPEX, OPEX, working capital, and finance
- conclusion

## Slide 25: Instrumentation and Control Philosophy

**Slide Title**

Instrumentation and Control Philosophy

**Primary Table**

Use `T-14` from [bac_ppt_curated_tables.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_curated_tables.md)

| Parameter | Value |
| --- | --- |
| Selected architecture | SIS-augmented regulatory control |
| Critical units | R-101, PU-201, TK-301 |
| Loop count | 8 |
| Utility services linked | 6 |
| High-criticality loops | 4 |

**Right / Bottom Bullets**

- Reactor temperature, pressure, and feed ratio form the critical control core.
- Purification pressure and inventory control protect product quality and operability.
- Storage blanketing and level control support safe dispatch and containment.

**Speaker Note**

- Keep the architecture summary high-level here
- Reserve the actual control graphic for Slide 26

## Slide 26: Control System Diagram / PID

**Slide Title**

Control System Diagram

**Primary Visual**

Use [control_system_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/control_system_sheet_1.png)

**Caption**

Principal BAC control loops centered on reactor safety, purification stability, and storage handling.

**Design Note**

- Keep this slide figure-led
- No large table on this slide

## Slide 27: HAZOP Overview

**Slide Title**

HAZOP Overview

**Primary Table**

Use `T-15`

| Parameter | Value |
| --- | --- |
| Node count | 4 |
| High-severity route hazards | 3 |
| Control loops linked | 8 |
| Node families | Reactor, separation, thermal exchange, storage |

**Bottom Note**

The HAZOP is focused on the major BAC risk nodes rather than on an exhaustive detailed-plant register.

## Slide 28: HAZOP Critical Deviations

**Slide Title**

Critical HAZOP Deviations

**Primary Table**

Use `T-16`

| Node | Deviation | Severity | Main Consequence | Safeguards |
| --- | --- | --- | --- | --- |
| R-101 | High reactor temperature | High | Runaway tendency, selectivity loss, pressure rise | TIC-R-101, PIC-R-101, FRC-R-101 |
| PU-201 | Low separation pressure | High | Air ingress, instability, off-spec separation | LIC-PU-201, PIC-PU-201, FIC-PU-201 |
| E-101 | Low thermal duty | Medium | Poor temperature control and downstream upset | TIC-R-101, PIC-R-101 |
| TK-301 | High storage level | Medium | Overflow and containment loss | LIC-TK-301, PIC-TK-301 |

**Bottom Statement**

Reactor temperature control and storage containment remain the most important safety anchors in the present BAC process basis.

## Slide 29: SHE, Waste, and ETP Basis

**Slide Title**

SHE, Waste, and ETP Basis

**On-Slide Content**

**Safety**

- Benzyl chloride and BAC service require contained handling, PPE, and spill / exposure controls.
- The reactor section is treated as the primary process-safety-critical zone.

**Environmental Control**

- Air and vapor releases are controlled through closed handling and vent-management logic.
- No untreated process effluent is discharged directly.

**Waste and Effluent Handling**

- Wastewater is segregated, collected, and routed for treatment.
- The treated disposal path is aligned to CETP-based handling at Dahej.
- Hazardous liquid and solid wastes are stored in contained areas for authorized disposal.

**Bottom Note**

The SHE basis is aligned with hazardous-chemical handling, segregated waste management, and a no-direct-discharge operating philosophy.

## Slide 30: Site Selection

**Slide Title**

Site Selection

**Primary Table**

Use `T-17`

| Parameter | Value |
| --- | --- |
| Selected site | Dahej, Gujarat |
| Region | India |
| Industrial basis | Coastal chemical cluster / PCPIR-linked basis |
| Utility basis | Grounded in cited site utility basis |
| Logistics basis | Coastal cluster dispatch basis |
| Site-fit note | Best available fit for BAC continuous liquid chemical manufacture |

**Right / Bottom Bullets**

- Strong feedstock ecosystem and chemical-cluster support
- Good coastal and land logistics
- Suitable utility and regulatory basis for hazardous liquid chemical manufacture

**Speaker Note**

- Present Dahej as the preferred site basis for this feasibility case

## Slide 31: Plant Layout Basis

**Slide Title**

Plant Layout Basis

**Primary Visual**

Use the future simplified zoning schematic defined in [bac_ppt_visual_integration.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_visual_integration.md)

**Side / Bottom Bullets**

- Tank farm and receipt zone positioned near feed entry and dispatch edge
- Reaction zone segregated from occupied and dispatch areas
- Separation and finishing zone located downstream of reaction for short process transfer
- Waste / recovery zone isolated but connected to the main process train

**Caption**

Conceptual zoned plant layout based on segregated hazard-zone planning.

## Slide 32: Layout and Utility Corridors

**Slide Title**

Layout and Utility Corridors

**On-Slide Content**

- Steam and cooling-water headers run parallel to the process train with branch take-offs at major units.
- Electrical and service corridors are routed away from wet and hot process hazard zones.
- Nitrogen service is aligned with storage blanketing and inerting requirements.
- Truck movement, utility routing, emergency response, and maintenance access are kept separate wherever practical.

**Optional Supporting Element**

- simplified utility-routing graphic if created later

**Bottom Note**

Layout planning is guided by hazard segregation, service accessibility, and continuous-operation support.

## Slide 33: Equipment Costing and Project Cost

**Slide Title**

Equipment Costing and Project Cost

**Primary Table**

Use `T-18`

| CAPEX Head | Value |
| --- | --- |
| Purchased equipment | 34.45 Cr INR |
| Installed equipment | 81.00 Cr INR |
| Direct plant cost | 93.98 Cr INR |
| Indirect cost | 22.56 Cr INR |
| Contingency | 9.40 Cr INR |
| Total CAPEX | 125.93 Cr INR |

**Secondary Compact Table / Callout**

Use `T-19`

| Equipment Family | Count | Installed Cost |
| --- | --- | --- |
| Storage tank | 1 | 47.36 Cr INR |
| Reactor | 1 | 19.99 Cr INR |
| Distillation column | 1 | 2.23 Cr INR |
| Heat exchanger | 1 | 1.05 Cr INR |
| Flash drum | 1 | 0.97 Cr INR |

**Bottom Note**

Project cost has been estimated on a screening basis to support feasibility assessment; further refinement is required during detailed design.

## Slide 34: Cost of Production

**Slide Title**

Cost of Production

**Primary Table**

Use `T-20`

| OPEX Head | Value | Share of OPEX |
| --- | --- | --- |
| Raw materials | 586.59 Cr INR/y | 95.49% |
| Utilities | 4.95 Cr INR/y | 0.81% |
| Labor | 15.60 Cr INR/y | 2.54% |
| Maintenance | 3.54 Cr INR/y | 0.58% |
| Overheads | 3.64 Cr INR/y | 0.59% |
| Total OPEX | 614.31 Cr INR/y | 100.00% |

**Bottom Takeaway**

The BAC case is strongly raw-material-cost dominated, while utility and maintenance burdens remain comparatively smaller at the present feasibility basis.

## Slide 35: Working Capital and Financial Analysis

**Slide Title**

Working Capital and Financial Analysis

**Top Compact Table**

Use `T-21`

| Component | Value |
| --- | --- |
| Raw-material inventory | 27.12 Cr INR |
| Product inventory | 41.92 Cr INR |
| Receivables | 157.81 Cr INR |
| Cash buffer | 11.78 Cr INR |
| Payables | 38.57 Cr INR |
| Working capital | 204.62 Cr INR |

**Bottom Metric Box / Compact Table**

Use `T-22`

| Metric | Value |
| --- | --- |
| Annual revenue | 1,800.00 Cr INR/y |
| Annual operating cost | 614.31 Cr INR/y |
| Gross profit | 1,185.69 Cr INR/y |
| Payback | 0.48 y |
| NPV | 4,366.57 Cr INR |
| IRR | 60.00% |
| Break-even capacity | 34.10% |

**Required Bottom Caveat**

These financial indicators are model-based feasibility outputs and remain sensitive to route assumptions, purification performance, and selling-price basis.

## Slide 36: Conclusion

**Slide Title**

Conclusion

**On-Slide Content**

- A continuous BAC plant on a 50 wt% sold-solution basis has been developed on a coherent feasibility-grade design basis.
- The selected quaternization route, process flow, and unit train are technically consistent with the present commercial product basis.
- Reactor, purification, storage, control, and safety sections have been carried through preliminary design and risk review.
- Dahej, Gujarat provides a suitable site basis for utilities, logistics, and hazardous-chemical industrial support.
- The current economic results indicate a promising case under the adopted assumptions, but require further refinement in route detail, purification basis, and project costing.
- Overall, the BAC plant appears technically coherent and economically promising on the current feasibility basis.

**Speaker Note**

- Keep the last line balanced and professional
- Do not overclaim final commercial certainty

