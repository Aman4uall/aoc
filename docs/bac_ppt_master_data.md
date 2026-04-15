# BAC PPT Master Data Sheet

This file is the single presentation-basis reference for the BAC PPT build.

Use this sheet to populate slide tables, captions, figure titles, and summary bullets. If a downstream table conflicts with this file, update the table source or explicitly note the exception before using it in the deck.

## 1. Scope Freeze

| Field | Locked Value |
| --- | --- |
| Product name | Benzalkonium Chloride (BAC) |
| Commercial basis | 50 wt% sold solution |
| Throughput basis | Finished product |
| Installed capacity | 50,000 TPA |
| Active basis | 50 wt% active |
| Operating mode | Continuous |
| Site basis | Dahej, Gujarat, India |
| Currency basis | INR |
| Economic reference year | 2025 |
| Annual operating days | 330 d/y |
| Presentation depth | 34-36 slides |
| Presentation status | Feasibility-grade academic home-paper presentation |

## 2. Naming Conventions

| Item | Convention To Use In Slides |
| --- | --- |
| Product short name | BAC |
| Product formal name | Benzalkonium Chloride |
| Product basis wording | 50 wt% BAC solution |
| Capacity wording | 50,000 TPA finished product |
| Site wording | Dahej, Gujarat |
| Currency wording | INR (2025 basis) |
| Route family wording | Quaternization liquid train |
| Major reactor tag | R-101 |
| Major purification tag | PU-201 |
| Major exchanger tag | E-101 |
| Storage tank tag | TK-301 |
| Storage transfer pump tag | TK-301 Pump |

## 3. Units Conventions

| Quantity Type | Use In Slides | Notes |
| --- | --- | --- |
| Annual capacity | TPA | Do not mix with kg/y on summary slides unless both are labeled |
| Process throughput | kg/h | Primary process basis |
| Volumetric flow | m3/h | Use for pumps and utilities |
| Vessel volume | m3 | Use 1-2 decimals for slide tables |
| Temperature | degC | Avoid mixing K and degC on presentation tables |
| Pressure | bar | Keep one basis per table |
| Heat duty | kW | Preferred over kcal/h or MJ/h for slides |
| Cost summary | Cr INR or Lakh INR | Convert from raw INR in slide tables |
| Detailed economics basis | INR | Keep full-INR basis in background working tables only |
| Inventory time | days | Use one decimal where needed |
| Percentages | wt% or % | Always label active basis explicitly |

## 4. Rounding Rules

| Data Class | Slide Rounding Rule |
| --- | --- |
| Capacity, operating days | whole number |
| Flowrates | 1-2 decimals |
| Dimensions | 1-2 decimals |
| Utilities | 1-2 decimals |
| Cost summaries in Cr/Lakh | 2 decimals |
| Ratios and margins | 2 decimals |
| Financial indicators | 2 decimals |

Avoid raw solver precision such as 3-6 decimal places unless the slide is explicitly a calculation trace.

## 5. Commercial Product Basis

| Basis Item | Value |
| --- | --- |
| Product form | Liquid solution |
| Sold concentration | 50.0 wt% |
| Sold solution basis | 6,313.13 kg/h |
| Active basis | 3,156.57 kg/h |
| Sold-solution price | INR 360.00/kg |
| Active-normalized price | INR 720.00/kg active |
| Carrier components listed in project basis | Water, ethanol |
| Carrier component listed in market chapter | Water |
| Homolog distribution | C12 0.4, C14 0.5, C16 0.1 |
| Quality targets | 50 wt% active; residual free benzyl chloride below limit; residual free tertiary amine below limit |

## 6. Process Basis

| Basis Item | Value |
| --- | --- |
| Selected route family | Quaternization liquid train |
| Route selected in process-selection chapter | Solvent-Free (Neat) Quaternization |
| Selected route score | 93.71 |
| Process train | Feed preparation -> Reactor -> Primary separation -> Concentration -> Purification -> Storage -> Waste treatment |
| Blueprint step count | 7 |
| Separation duties | 2 |
| Recycle intents | 0 |
| Heat integration case | No recovery |
| Residual hot utility | 359.13 kW |
| Residual cold utility | 567.12 kW |

## 7. Reactor Basis

| Field | Value |
| --- | --- |
| Reactor tag | R-101 |
| Reactor type in artifact | Jacketed CSTR Train |
| Residence time | 25.0 h |
| Design volume | 123.76 m3 |
| Design temperature | 85.0 degC |
| Design pressure | 3.01 bar |
| Design conversion | 0.95 |
| Heat duty | 257.12 kW |
| Heat-transfer area | 15.00 m2 |
| Shell diameter | 3.16 m |
| Shell length | 15.79 m |
| Cooling medium | Dowtherm A / cooling water |
| Runaway risk label | Moderate |

## 8. Storage And Pump Basis

| Field | Value |
| --- | --- |
| Storage tank tag | TK-301 |
| Storage service | BAC product storage via vertical tank farm |
| Inventory days | 11.55 d |
| Working volume | 1,758.79 m3 |
| Total volume | 1,969.85 m3 |
| Storage MoC | SS304 |
| Tank diameter | 8.56 m |
| Straight side height | 34.24 m |
| Pump tag | TK-301 Pump |
| Pump flow | 219.85 m3/h |
| Differential head | 52.0 m |
| Pump power | 36.58 kW |
| NPSH margin | 2.5 m |

## 9. Utility Basis

| Utility | Normal Load | Annualized Usage | Cost Proxy Basis |
| --- | --- | --- | --- |
| Steam | 2,277.14 kg/h | 18,034,917.1 kg/y | 20 bar steam, INR 1.80/kg |
| Cooling water | 107.59 m3/h | 852,136.6 m3/y | recirculating CW |
| Electricity | 151.56 kW | 1,200,323.5 kWh/y | INR 8.50/kWh |
| DM water | 2.00 m3/h | 15,840.0 m3/y | service allowance |
| Nitrogen | 3.00 Nm3/h | 23,760.0 Nm3/y | inerting and blanketing |

## 10. CAPEX Basis

| CAPEX Head | Value |
| --- | --- |
| Purchased equipment | INR 344,493,929.42 |
| Installed equipment | INR 810,046,470.58 |
| Direct plant cost | INR 939,801,630.70 |
| Indirect cost | INR 225,552,391.37 |
| Contingency | INR 93,980,163.07 |
| Total CAPEX | INR 1,259,334,185.14 |

### Presentation Conversion

| CAPEX Head | Slide Value |
| --- | --- |
| Purchased equipment | 34.45 Cr INR |
| Installed equipment | 81.00 Cr INR |
| Direct plant cost | 93.98 Cr INR |
| Indirect cost | 22.56 Cr INR |
| Contingency | 9.40 Cr INR |
| Total CAPEX | 125.93 Cr INR |

## 11. OPEX Basis

| OPEX Head | Value |
| --- | --- |
| Annual OPEX | INR 6,143,068,271.54/y |
| Raw materials | INR 5,865,876,513.63/y |
| Utilities | INR 49,484,847.46/y |
| Labor | INR 156,000,000.00/y |
| Maintenance | INR 35,350,344.91/y |
| Unit cost of production | INR 122.86/kg |
| Selling price basis | INR 360.00/kg |

### Presentation Conversion

| OPEX Head | Slide Value |
| --- | --- |
| Annual OPEX | 614.31 Cr INR/y |
| Raw materials | 586.59 Cr INR/y |
| Utilities | 4.95 Cr INR/y |
| Labor | 15.60 Cr INR/y |
| Maintenance | 3.54 Cr INR/y |

## 12. Working Capital Basis

| Field | Value |
| --- | --- |
| Raw-material inventory days | 16.9 d |
| Product inventory days | 8.5 d |
| Receivable days | 32.0 d |
| Payable days | 24.0 d |
| Cash buffer days | 7.0 d |
| Working capital | INR 2,046,225,419.05 |
| Peak working capital | INR 2,046,225,419.05 |
| Peak working-capital month | 21.15 |

### Presentation Conversion

| Working-Capital Item | Slide Value |
| --- | --- |
| Working capital | 204.62 Cr INR |
| Raw-material inventory | 27.12 Cr INR |
| Product inventory | 41.92 Cr INR |
| Receivables | 157.81 Cr INR |
| Payables | 38.57 Cr INR |

## 13. Financial Basis

| Field | Value |
| --- | --- |
| Annual revenue | INR 18,000,000,000.00 |
| Annual operating cost | INR 6,143,068,271.54 |
| Gross profit | INR 11,856,931,728.46 |
| Working capital | INR 2,046,225,419.05 |
| Total project funding | INR 3,324,852,043.70 |
| Payback | 0.48 y |
| NPV | INR 43,665,739,825.90 |
| IRR | 60.00 |
| Profitability index | 14.13 |
| Break-even fraction | 0.341 |
| Minimum DSCR | 25.53 |
| Average DSCR | 32.41 |

### Presentation Conversion

| Financial Item | Slide Value |
| --- | --- |
| Annual revenue | 1,800.00 Cr INR/y |
| Annual operating cost | 614.31 Cr INR/y |
| Gross profit | 1,185.69 Cr INR/y |
| Total project funding | 332.49 Cr INR |
| NPV | 4,366.57 Cr INR |
| Break-even capacity | 34.10% of installed capacity |

## 14. Site, Control, And HAZOP Basis

| Item | Value |
| --- | --- |
| Selected site | Dahej |
| Site candidates currently in artifact | 1 |
| Control loop count | 8 |
| HAZOP node count | 4 |
| Critical HAZOP nodes used in chapter | R-101, PU-201, E-101, TK-301 |

## 15. Reconciliation Flags

These items must be resolved or explicitly handled before slide drafting.

| Flag ID | Issue | Action For PPT |
| --- | --- | --- |
| RF-01 | Reactor chapter narrative says glass-lined agitated reactor with external recirculation heat-removal loop, while `reactor_design.json` reports `Jacketed CSTR Train`. | Use one reactor story only. Prefer the chapter narrative for slide wording, but confirm dimensional consistency before final reactor table. |
| RF-02 | Project basis lists carrier components as water and ethanol, while market chapter lists water only. | For now, present product as 50 wt% BAC solution and avoid over-specific carrier wording unless reconciled. |
| RF-03 | Route is presented as selected and economically favorable, but also marked screening-feasible / screening-only. | Use feasibility-grade language in process and economics slides; do not overstate bankability. |
| RF-04 | `site_selection.json` currently exposes only one candidate in artifact output. | Use the chapter narrative for site justification rather than implying a broad final comparative scoring set from artifact rows alone. |

## 16. Slide-Table Quality Rules

- Every table must use the locked 50,000 TPA finished-product basis.
- Every table must label units explicitly.
- Every cost table shown in the PPT should use Cr INR unless a smaller Lakh-scale table is clearer.
- Do not mix sold-solution basis and active basis in the same summary table unless both are clearly labeled.
- Do not copy raw artifact tables directly into slides.
- Condense oversized tables into summary tables with 4-8 rows.
- If a value is still under reconciliation, mark it as a basis note in the slide draft instead of silently choosing one version.

## 17. Primary Source Files

- [project_basis.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/project_basis.json)
- [reactor_design.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/reactor_design.json)
- [storage_design.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/storage_design.json)
- [pump_design.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/pump_design.json)
- [utility_summary.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/utility_summary.json)
- [cost_model.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/cost_model.json)
- [plant_cost_summary.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/plant_cost_summary.json)
- [working_capital_model.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/working_capital_model.json)
- [financial_model.json](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/artifacts/financial_model.json)
- [market_capacity_selection.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/market_capacity_selection.md)
- [process_selection.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/process_selection.md)
- [storage_utilities.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/storage_utilities.md)
- [project_cost.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/project_cost.md)
- [working_capital.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/working_capital.md)
