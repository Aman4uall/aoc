# BAC PPT Curated Table Pack

This file defines the presentation-safe tables to use in the BAC PPT.

Each table below is curated for a specific slide purpose. Use these tables instead of copying raw chapter tables directly into the deck.

## 1. Table Selection Policy

Keep:
- decision tables
- sizing summary tables
- cost summary tables
- financial summary tables
- short HAZOP / control summary tables

Do not keep in the main deck:
- packet-closure tables
- long stream ledgers
- procurement draw schedules
- 10+ row financial schedules
- raw utility support matrices
- repeated versions of the same reactor or equipment table

## 2. Slide-to-Table Map

| Slide No. | Slide Title | Table ID | Table Purpose |
| --- | --- | --- | --- |
| 4 | Product Profile | T-01 | Key commercial product basis |
| 5 | Market and Capacity Justification | T-02 | Capacity basis summary |
| 6 | Literature and Route Options | T-03 | Candidate route comparison |
| 7 | Process Selection | T-04 | Final route selection summary |
| 8 | Selected Process Basis | T-05 | Locked process basis |
| 15 | Material Balance Summary | T-06 | Overall plant balance snapshot |
| 16 | Energy Balance Summary | T-07 | Utility and duty summary |
| 18 | Reactor Design Basis | T-08 | Reactor operating and design basis |
| 19 | Reactor Sizing Summary | T-09 | Final reactor sizing summary |
| 20 | Reactor Mechanical Design | T-10 | Reactor mechanical summary |
| 21 | Major Process Unit Design | T-11 | Major unit design summary |
| 22 | Heat Exchanger and Thermal Equipment | T-12 | Thermal equipment summary |
| 23 | Pumps, Storage, and Auxiliary Equipment | T-13 | Pump and storage summary |
| 25 | Instrumentation and Control Philosophy | T-14 | Control architecture summary |
| 27 | HAZOP Overview | T-15 | HAZOP coverage summary |
| 28 | HAZOP Critical Deviations | T-16 | Critical node deviation summary |
| 30 | Site Selection | T-17 | Site basis summary |
| 33 | Equipment Costing and Project Cost | T-18 | CAPEX summary |
| 33 | Equipment Costing and Project Cost | T-19 | Equipment family cost summary |
| 34 | Cost of Production | T-20 | OPEX summary |
| 35 | Working Capital and Financial Analysis | T-21 | Working-capital summary |
| 35 | Working Capital and Financial Analysis | T-22 | Financial feasibility summary |

## 3. Curated Tables

### T-01 Product Profile

Use on: Slide 4

| Basis Item | Value |
| --- | --- |
| Product | Benzalkonium Chloride (BAC) |
| Commercial form | 50 wt% sold-solution basis |
| Throughput basis | Finished product |
| Active content | 50 wt% |
| Sold solution rate | 6,313.13 kg/h |
| Active rate | 3,156.57 kg/h |
| Selling price basis | INR 360.00/kg sold solution |

Source basis:
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

Omit:
- unsupported pure-component property rows such as melting and boiling point unavailability

### T-02 Capacity Basis Summary

Use on: Slide 5

| Parameter | Value |
| --- | --- |
| Installed capacity | 50,000 TPA |
| Annual operating days | 330 d/y |
| Product basis | 50 wt% BAC solution |
| Throughput basis | Finished product |
| Site basis | Dahej, Gujarat |
| Economic basis year | 2025 |

Source basis:
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

### T-03 Candidate Route Comparison

Use on: Slide 6

| Route | Family | Score | Status | Key Note |
| --- | --- | --- | --- | --- |
| Solvent-Free (Neat) Quaternization | Quaternization liquid train | 93.71 | Selected | Best overall route score; feasibility-grade basis |
| Quaternization in Butanone | Quaternization liquid train | 72.94 | Not selected | Lower overall score |
| Quaternization in Acetonitrile | Quaternization liquid train | 41.67 | Not selected | Least favorable route score |

Source basis:
- [process_selection.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/process_selection.md)

Omit:
- route-origin and chemistry scoring subcolumns on slide unless speaker notes need them

### T-04 Final Route Selection Summary

Use on: Slide 7

| Selection Item | Value |
| --- | --- |
| Selected route | Solvent-Free (Neat) Quaternization |
| Route family | Quaternization liquid train |
| Scientific status | Screening-feasible |
| Operating mode | Continuous |
| Main downstream train | Primary separation -> concentration -> purification |
| Selection caution | Feasibility-grade academic basis; not a bankable detailed route package |

Source basis:
- [process_selection.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/process_selection.md)
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

### T-05 Locked Process Basis

Use on: Slide 8

| Basis Item | Value |
| --- | --- |
| Product basis | 50 wt% BAC solution |
| Capacity | 50,000 TPA |
| Route family | Quaternization liquid train |
| Process train steps | 7 |
| Separation duties | 2 |
| Heat integration case | No recovery |
| Residual hot utility | 359.13 kW |
| Residual cold utility | 567.12 kW |

Source basis:
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

### T-06 Overall Plant Balance Snapshot

Use on: Slide 15

| Stream / Basis Item | Value |
| --- | --- |
| Feed to reactor | 3,461.60 kg/h |
| Product basis | 6,313.13 kg/h sold solution |
| Active basis | 3,156.57 kg/h |
| Design conversion | 95.0% |
| Major feed components | Dodecyldimethylamine, benzyl chloride |
| Major product basis | BAC solution with cleanup and finishing |

Source basis:
- [reactor_design.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/reactor_design.md)
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

Note:
- This is a summary table only. Do not paste the full stream ledger into the main deck.

### T-07 Utility and Duty Summary

Use on: Slide 16

| Utility | Load | Units | Annualized Usage |
| --- | --- | --- | --- |
| Steam | 2,277.14 | kg/h | 18,034,917.1 kg/y |
| Cooling water | 107.59 | m3/h | 852,136.6 m3/y |
| Electricity | 151.56 | kW | 1,200,323.5 kWh/y |
| DM water | 2.00 | m3/h | 15,840.0 m3/y |
| Nitrogen | 3.00 | Nm3/h | 23,760.0 Nm3/y |

Source basis:
- [storage_utilities.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/storage_utilities.md)

### T-08 Reactor Operating and Design Basis

Use on: Slide 18

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

Source basis:
- [reactor_design.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/reactor_design.md)

Note:
- Use chapter narrative language, not the conflicting artifact label, until the reactor-basis discrepancy is reconciled.

### T-09 Reactor Sizing Summary

Use on: Slide 19

| Parameter | Value |
| --- | --- |
| Design volume | 123.76 m3 |
| Liquid holdup | 101.44 m3 |
| Shell diameter | 4.00 m |
| Shell length | 9.85 m |
| Vessel height without skirt | 11.85 m |
| External-loop exchanger area | 15.00 m2 |
| Agitator arrangement | 3 x retreat-curve agitator |

Source basis:
- [reactor_design.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/reactor_design.md)

Omit:
- older superseded jacket/tube geometry

### T-10 Reactor Mechanical Summary

Use on: Slide 20

| Parameter | Value |
| --- | --- |
| Reactor type | Glass-lined vertical reactor |
| Pressure boundary basis | Carbon-steel shell with glass lining |
| Head type | 2:1 ellipsoidal heads |
| Cooling philosophy | External pump-around loop with exchanger |
| Heat-transfer area | 15.00 m2 |
| Runaway risk category | Moderate |

Source basis:
- [reactor_design.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/reactor_design.md)
- [mechanical_design_moc.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/mechanical_design_moc.md)

### T-11 Major Unit Design Summary

Use on: Slide 21

| ID | Unit | Service | Volume | Duty | Design T | Design P |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | Quaternization reaction | 123.76 m3 | 257.12 kW | 85.0 degC | 3.01 bar |
| PU-201 | Distillation column | Purification train | 21.21 m3 | 1,391.58 kW | 140.0 degC | 2.00 bar |
| V-101 | Flash drum | Intermediate disengagement | 22.28 m3 | 0.00 kW | 85.0 degC | 3.00 bar |
| E-101 | Heat exchanger | Thermal service | 8.17 m3 | 637.18 kW | 180.0 degC | 8.00 bar |

Source basis:
- [equipment_design_sizing.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/equipment_design_sizing.md)

### T-12 Thermal Equipment Summary

Use on: Slide 22

| Equipment | Service | Duty | Design T | Design P | MoC |
| --- | --- | --- | --- | --- | --- |
| E-101 | Shell-and-tube exchanger | 637.18 kW | 180.0 degC | 8.00 bar | Carbon steel |
| R-101 external loop | Reactor heat removal | 257.12 kW | 85.0 degC | 3.01 bar | Integrated with GLR loop |

Source basis:
- [equipment_design_sizing.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/equipment_design_sizing.md)
- [reactor_design.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/reactor_design.md)

### T-13 Pump and Storage Summary

Use on: Slide 23

| Equipment | Service | Key Size / Duty | Design Basis |
| --- | --- | --- | --- |
| TK-301 | BAC product storage tank | 1,969.85 m3 total volume | 11.6 days inventory |
| TK-301 Pump | Product transfer | 219.85 m3/h, 52.0 m head, 36.58 kW | Dispatch and tank-farm transfer |

Source basis:
- [equipment_design_sizing.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/equipment_design_sizing.md)
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

### T-14 Control Architecture Summary

Use on: Slide 25

| Parameter | Value |
| --- | --- |
| Selected architecture | SIS-augmented regulatory control |
| Critical units | R-101, PU-201, TK-301 |
| Loop count | 8 |
| Utility services linked | 6 |
| High-criticality loops | 4 |

Source basis:
- [instrumentation_control.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/instrumentation_control.md)

### T-15 HAZOP Coverage Summary

Use on: Slide 27

| Parameter | Value |
| --- | --- |
| Node count | 4 |
| High-severity route hazards | 3 |
| Control loops linked | 8 |
| Node families | Reactor, separation, thermal exchange, storage |

Source basis:
- [hazop.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/hazop.md)

### T-16 HAZOP Critical Deviations

Use on: Slide 28

| Node | Deviation | Severity | Main Consequence | Safeguards |
| --- | --- | --- | --- | --- |
| R-101 | High reactor temperature | High | Runaway tendency, selectivity loss, pressure rise | TIC-R-101, PIC-R-101, FRC-R-101 |
| PU-201 | Low separation pressure | High | Air ingress, instability, off-spec separation | LIC-PU-201, PIC-PU-201, FIC-PU-201 |
| E-101 | Low thermal duty | Medium | Poor temperature control and downstream upset | TIC-R-101, PIC-R-101 |
| TK-301 | High storage level | Medium | Overflow and containment loss | LIC-TK-301, PIC-TK-301 |

Source basis:
- [hazop.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/hazop.md)

### T-17 Site Basis Summary

Use on: Slide 30

| Parameter | Value |
| --- | --- |
| Selected site | Dahej, Gujarat |
| Region | India |
| Industrial basis | Coastal chemical cluster / PCPIR-linked basis |
| Utility basis | Grounded in cited site utility basis |
| Logistics basis | Coastal cluster dispatch basis |
| Site-fit note | Best available fit for BAC continuous liquid chemical manufacture |

Source basis:
- [site_selection.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/site_selection.md)
- [project_cost.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/project_cost.md)

### T-18 CAPEX Summary

Use on: Slide 33

| CAPEX Head | Value |
| --- | --- |
| Purchased equipment | 34.45 Cr INR |
| Installed equipment | 81.00 Cr INR |
| Direct plant cost | 93.98 Cr INR |
| Indirect cost | 22.56 Cr INR |
| Contingency | 9.40 Cr INR |
| Total CAPEX | 125.93 Cr INR |

Source basis:
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

### T-19 Equipment Family Cost Summary

Use on: Slide 33

| Equipment Family | Count | Installed Cost |
| --- | --- | --- |
| Storage tank | 1 | 47.36 Cr INR |
| Reactor | 1 | 19.99 Cr INR |
| Distillation column | 1 | 2.23 Cr INR |
| Heat exchanger | 1 | 1.05 Cr INR |
| Flash drum | 1 | 0.97 Cr INR |

Source basis:
- [project_cost.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/project_cost.md)

Note:
- Keep the reactor costing basis note in speaker notes because the GLR repricing is not fully reconciled.

### T-20 OPEX Summary

Use on: Slide 34

| OPEX Head | Value | Share of OPEX |
| --- | --- | --- |
| Raw materials | 586.59 Cr INR/y | 95.49% |
| Utilities | 4.95 Cr INR/y | 0.81% |
| Labor | 15.60 Cr INR/y | 2.54% |
| Maintenance | 3.54 Cr INR/y | 0.58% |
| Overheads | 3.64 Cr INR/y | 0.59% |
| Total OPEX | 614.31 Cr INR/y | 100.00% |

Source basis:
- [cost_of_production.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/cost_of_production.md)

### T-21 Working-Capital Summary

Use on: Slide 35

| Component | Value |
| --- | --- |
| Raw-material inventory | 27.12 Cr INR |
| Product inventory | 41.92 Cr INR |
| Receivables | 157.81 Cr INR |
| Cash buffer | 11.78 Cr INR |
| Payables | 38.57 Cr INR |
| Working capital | 204.62 Cr INR |

Source basis:
- [working_capital.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/working_capital.md)

### T-22 Financial Feasibility Summary

Use on: Slide 35

| Metric | Value |
| --- | --- |
| Annual revenue | 1,800.00 Cr INR/y |
| Annual operating cost | 614.31 Cr INR/y |
| Gross profit | 1,185.69 Cr INR/y |
| Payback | 0.48 y |
| NPV | 4,366.57 Cr INR |
| IRR | 60.00% |
| Break-even capacity | 34.10% |

Source basis:
- [financial_analysis.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/financial_analysis.md)
- [bac_ppt_master_data.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_ppt_master_data.md)

## 4. Tables To Keep Out Of Main Deck

These are useful for backup or appendix-style notes, but should not go into the main 34-36 slide deck.

- Reactor packet closure tables
- Long stream and composition ledgers
- Full utility service matrices
- Startup/shutdown loop sheets for all 8 loops
- Full HAZOP register
- Direct-cost allocation tables with 8+ rows
- Procurement timing and CAPEX draw schedules
- 10-12 year debt, P&L, and cash-accrual schedules

## 5. Outstanding Table Risks

| Risk ID | Issue | Impact |
| --- | --- | --- |
| TR-01 | Reactor equipment wording differs between artifact and chapter narrative | Could create inconsistent reactor tables if not controlled |
| TR-02 | Reactor cost note suggests legacy pressure-vessel pricing remains in use pending GLR repricing | Reactor CAPEX should be presented cautiously |
| TR-03 | Product carrier wording is not fully reconciled | Avoid over-specific formulation table language |
| TR-04 | Some financial outputs are extremely strong for a feasibility deck | Present as model outputs, not guaranteed business results |

## 6. Slide Composition Guidance

This section defines how each curated table should appear on the slide so the deck does not turn into a table-only presentation.

| Slide No. | Slide Title | Visual Style | Table Use Rule | Recommended Supporting Element |
| --- | --- | --- | --- | --- |
| 4 | Product Profile | Table-led | Use T-01 only | small BAC application icons or 2-3 product-use bullets |
| 5 | Market and Capacity Justification | Hybrid | Use T-02 as half-slide table | short market paragraph or bar chart later if needed |
| 6 | Literature and Route Options | Table-led | Use T-03 only | 2-line takeaway under table |
| 7 | Process Selection | Table-led | Use T-04 only | one bold route-selection statement |
| 8 | Selected Process Basis | Table-led | Use T-05 only | no extra large figure |
| 11 | Block Flow Diagram | Figure-led | no main table | [bfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/bfd_sheet_1.png) plus 3-4 bullets |
| 12 | Process Flow Diagram I | Figure-led | no main table | [pfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_1.png) |
| 13 | Process Flow Diagram II | Figure-led | no main table | [pfd_sheet_2.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_2.png) |
| 14 | Process Description | Text-led | no table unless needed | 6-step process sequence bullets |
| 15 | Material Balance Summary | Table-led | Use T-06 only | 1 basis note under table |
| 16 | Energy Balance Summary | Table-led | Use T-07 only | 1 utility takeaway line |
| 17 | Heat Integration and Utilities Basis | Hybrid | use utility takeaway only, not a full new table | utility bullets or small duty callouts |
| 18 | Reactor Design Basis | Table-led | Use T-08 only | one reactor schematic or design note |
| 19 | Reactor Sizing Summary | Table-led | Use T-09 only | small sketch if available, otherwise table only |
| 20 | Reactor Mechanical Design | Table-led | Use T-10 only | one MoC / safety note |
| 21 | Major Process Unit Design | Table-led | Use T-11 only | no second full table |
| 22 | Heat Exchanger and Thermal Equipment | Table-led | Use T-12 only | one thermal-service note |
| 23 | Pumps, Storage, and Auxiliary Equipment | Table-led | Use T-13 only | do not add separate storage and pump tables |
| 25 | Instrumentation and Control Philosophy | Hybrid | Use T-14 as left or right panel | 3 critical loop bullets |
| 26 | Control System Diagram / PID | Figure-led | no main table | [control_system_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/control_system_sheet_1.png) |
| 27 | HAZOP Overview | Table-led | Use T-15 only | 1 sentence on node coverage |
| 28 | HAZOP Critical Deviations | Table-led | Use T-16 only | red/amber severity highlighting if styled |
| 29 | SHE, Waste, and ETP Basis | Hybrid | no full table unless condensed | 3-zone SHEW bullets + CETP/waste note |
| 30 | Site Selection | Hybrid | Use T-17 as compact table | 3 bullets from site chapter |
| 31 | Plant Layout Basis | Figure-led | no main table | mermaid layout redrawn or simplified zoning graphic |
| 32 | Layout and Utility Corridors | Hybrid | compress one matrix excerpt only if needed | zoning / utility routing bullets |
| 33 | Equipment Costing and Project Cost | Hybrid | pair T-18 and T-19 carefully | one CAPEX pie/bar chart if built later |
| 34 | Cost of Production | Table-led | Use T-20 only | optional small stacked bar later |
| 35 | Working Capital and Financial Analysis | Hybrid | Use T-21 and T-22 only if split layout remains readable | small metric callout boxes for payback, IRR, NPV |
| 36 | Conclusion | Text-led | no table | 5-7 conclusion bullets |

## 7. Table Density Rules Per Slide

- Figure-led slides should not include a large table.
- Table-led slides should contain only one large table.
- Hybrid slides may contain one compact table plus 2-4 bullets.
- If two tables must share a slide, one must be converted into a compact callout block.
- No slide should contain more than 8 body rows in a visible table unless the table is split visually into two columns.

## 8. Recommended Table Pairings

These pairings are allowed because they serve the same slide purpose and can be designed cleanly.

| Pairing | Allowed? | Rule |
| --- | --- | --- |
| T-18 + T-19 | Yes | Use T-18 as main CAPEX block and T-19 as a small side table or chart substitute |
| T-21 + T-22 | Yes | Use T-21 as top mini-table and T-22 as bottom metric box set |
| T-08 + T-09 | No on same slide | Split into reactor basis and reactor sizing slides |
| T-14 + control diagram | No on same slide if full-size diagram used | Keep table on Slide 25 and diagram on Slide 26 |
| T-15 + T-16 | No on same slide | Coverage summary and critical deviations should remain separate |

## 9. Tables Requiring Speaker-Note Context

| Table ID | Why Context Is Needed | Speaker Note Reminder |
| --- | --- | --- |
| T-03 | Selected route is not fully detailed industrial proof | Mention that selection remains feasibility-grade |
| T-08 | Reactor basis has a reconciliation flag | State that chapter narrative basis is being followed for presentation clarity |
| T-18 | CAPEX basis is still preliminary | Call it preliminary project cost estimation |
| T-19 | Reactor cost note indicates legacy pricing basis | Mention equipment-family costs are screening estimates |
| T-22 | Financial outputs are strong and optimistic | State that results depend on current route, yield, and pricing assumptions |

## 10. Tables To Convert Into Visual Callouts Instead Of Full Tables

These should not appear as normal tables in the PPT even though they may still support the narrative.

- utility peak and annualized demand matrix
- utility service system matrix
- full control loop objective matrix
- startup / shutdown loop matrix
- direct-cost allocation matrix with 8+ heads
- procurement timing schedule
- debt repayment schedule
- 10-12 year financial schedules
