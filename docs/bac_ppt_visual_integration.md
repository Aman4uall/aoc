# BAC PPT Visual Integration Plan

This file defines how visuals should be integrated into the BAC PPT.

Goal:
- use existing BAC visuals wherever they are already presentation-ready
- avoid unnecessary redrawing of solved process graphics
- identify which slides still need simplified custom visuals
- keep figure-led slides clearly visual and not crowded by tables

## 1. Visual Asset Inventory

### 1.1 Presentation-Ready PNG Assets

All four available slide-ready image assets are square `1600 x 1600` PNGs.

| Asset | Path | Intended Use |
| --- | --- | --- |
| BFD | [bfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/bfd_sheet_1.png) | High-level process overview |
| PFD Sheet 1 | [pfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_1.png) | Upstream / reaction section |
| PFD Sheet 2 | [pfd_sheet_2.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_2.png) | Cleanup / finishing section |
| Control System | [control_system_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/control_system_sheet_1.png) | Control-system / PID slide |

### 1.2 Source SVG Assets

These are useful as editable or fallback vector sources.

| Asset Type | File(s) |
| --- | --- |
| BFD | [bac_bfd_final.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/bac_bfd_final.svg), [bfd_sheet_1.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/bfd_sheet_1.svg) |
| PFD | [bac_pfd_final.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/bac_pfd_final.svg), [pfd_sheet_1.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/pfd_sheet_1.svg), [pfd_sheet_2.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/pfd_sheet_2.svg) |
| Control system | [control_system_sheet_1.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/control_system_sheet_1.svg), [control_system_sheet_2.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/control_system_sheet_2.svg) |
| Symbol library | [bac_pfd_symbol_library.svg](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/diagrams/bac_pfd_symbol_library.svg) |

## 2. Slide-by-Slide Visual Mapping

| Slide No. | Slide Title | Visual Strategy | Primary Asset | Supporting Content |
| --- | --- | --- | --- | --- |
| 11 | Block Flow Diagram | Full-width figure-led | [bfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/bfd_sheet_1.png) | 3-4 bullets only |
| 12 | Process Flow Diagram I | Full-width figure-led | [pfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_1.png) | Minimal caption only |
| 13 | Process Flow Diagram II | Full-width figure-led | [pfd_sheet_2.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_2.png) | Minimal caption only |
| 18 | Reactor Design Basis | Table-led with small visual support if needed | no current reactor-specific figure | use one short design-basis note |
| 25 | Instrumentation and Control Philosophy | Hybrid | no large figure on this slide | T-14 + 3 critical-loop bullets |
| 26 | Control System Diagram / PID | Full-width figure-led | [control_system_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/control_system_sheet_1.png) | short caption only |
| 30 | Site Selection | Hybrid | no existing map or site graphic | compact site table + 3 bullets |
| 31 | Plant Layout Basis | Custom simple schematic required | derive from layout mermaid basis | zoning visual only |
| 32 | Layout and Utility Corridors | Custom simple schematic required | derive from layout chapter matrices | utility-routing callout graphic or compact bullets |
| 29 | SHE, Waste, and ETP Basis | Custom simple schematic required | derive from SHE chapter | small waste-flow / containment / CETP logic graphic |

## 3. Ready-To-Use Visual Slides

These slides can proceed immediately with existing graphics.

### Slide 11

- use [bfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/bfd_sheet_1.png)
- place figure large and centered
- add 3-4 concise bullets:
  - feed preparation
  - quaternization reactor
  - primary flash / concentration / purification
  - storage and waste handling

### Slide 12

- use [pfd_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_1.png)
- no large table
- optional one-line caption:
  - `Feed preparation and reaction section of the selected BAC process train`

### Slide 13

- use [pfd_sheet_2.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/pfd_sheet_2.png)
- no large table
- optional one-line caption:
  - `Cleanup, finishing, storage, and waste-handling section`

### Slide 26

- use [control_system_sheet_1.png](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/presentation_assets/control_system_sheet_1.png)
- no large table on the same slide
- keep table T-14 on Slide 25 only

## 4. Visuals That Still Need To Be Created Or Simplified

### 4.1 Layout Visual

Need:
- one clean zoning slide for Slide 31

Source basis:
- [layout.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/layout.md)

Recommended visual:
- a simplified left-to-right block zoning diagram using:
  - tank farm / receipt zone
  - reaction zone
  - separation and finishing zone
  - waste / recovery zone

Do not use:
- the full equipment placement matrix directly as a slide figure

### 4.2 Utility Corridor / Routing Visual

Need:
- one simplified utility routing graphic for Slide 32, or else a compact bullet layout

Source basis:
- utility corridor matrix and routing basis in [layout.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/layout.md)

Recommended visual:
- horizontal process train with utility rack at one side
- color-coded arrows for steam, cooling water, power, nitrogen

### 4.3 SHE / Waste / ETP Logic Visual

Need:
- one simple waste-and-safeguards graphic for Slide 29

Source basis:
- [safety_health_environment_waste.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/outputs/benzalkonium-chloride-benchmark-live-v26/chapters/safety_health_environment_waste.md)

Recommended visual:
- three-lane mini diagram:
  - air emissions control
  - wastewater segregation -> neutralization/equalization -> CETP
  - hazardous solid/liquid waste -> contained storage -> authorized disposal

Important text anchors:
- bunded / diked storage
- no direct discharge
- CETP at Dahej
- hazardous waste segregation

### 4.4 Reactor Visual

Currently missing:
- a simple reactor sketch specifically aligned to the adopted GLR external-loop basis

Recommended handling:
- not mandatory if Slide 18-20 remain table-led
- if added later, it should show:
  - vessel body
  - external recirculation loop
  - exchanger
  - agitation

## 5. Figure Density Rules

- Figure-led slides should not contain large tables.
- Square process graphics should be placed large enough to remain legible.
- On figure-led slides, supporting text should be capped at 1 caption line or 3-4 bullets.
- Do not put both PFD sheets on one slide.
- Do not shrink the control-system figure to make room for another table.

## 6. Visual Style Rules

- Keep all process graphics technically clean rather than decorative.
- Use one caption style throughout the deck.
- Prefer thin, readable callout text over crowded annotation boxes.
- For custom visuals, follow the established BAC visual language:
  - muted engineering palette
  - clear section separation
  - strong tag labels

## 7. Missing Visual Priority

| Priority | Visual | Why |
| --- | --- | --- |
| High | Layout zoning schematic | Needed for Slide 31 and no ready PNG currently exists |
| High | SHE / waste flow graphic | Needed to avoid a text-heavy Slide 29 |
| Medium | Utility corridor graphic | Useful for Slide 32, but can fall back to bullets |
| Low | Reactor schematic | Helpful, but non-essential if reactor slides stay table-led |

## 8. Recommended Phase 6 Close-Out

At the end of visual integration, the deck should have:
- 4 existing BAC technical graphics directly assigned to slides
- 2-3 missing custom schematic slides defined clearly
- no ambiguity about where visuals dominate versus where tables dominate

## 9. Custom Visual Specifications

This section defines the missing visuals tightly enough that they can be built later without changing slide logic.

### 9.1 Slide 29: SHE / Waste / ETP Basis Graphic

Purpose:
- prevent Slide 29 from becoming a text wall
- convert SHE chapter content into one clear visual story

Recommended layout:
- three vertical lanes or three horizontal cards

Lane 1:
- `Air and Vapor Control`
- closed handling
- vent handling / scrubber basis
- benzyl chloride vapor control

Lane 2:
- `Wastewater Handling`
- segregated collection
- neutralization / equalization
- transfer to `Dahej CETP`
- no direct discharge

Lane 3:
- `Hazardous Waste Management`
- off-spec liquid waste
- contaminated solids / PPE / spent media
- contained storage
- authorized disposal

Mandatory callouts:
- bunded / diked storage
- CETP linkage
- hazardous-waste segregation
- regulatory compliance basis

Do not include:
- full regulation list
- full PPE list
- long prose paragraphs

Suggested caption:
- `Waste and safeguard strategy for the feasibility-grade BAC plant at Dahej`

### 9.2 Slide 31: Plant Layout Zoning Graphic

Purpose:
- visually communicate the plant arrangement logic
- convert the layout chapter mermaid and zoning tables into a readable plot-basis slide

Recommended layout:
- left-to-right or top-to-bottom zone blocks

Required zones:
- Tank Farm / Receipt Zone
- Reaction Zone
- Separation and Finishing Zone
- Waste / Recovery Zone
- Dispatch Edge

Required relationships:
- feed receipt close to tank farm
- reaction zone buffered from dispatch / occupied areas
- separation close to reaction zone
- waste / recovery separated but connected to process train
- dispatch edge near storage

Required annotations:
- emergency vehicle access
- hazard segregation
- utility corridor direction
- maintenance access / operator movement note

Do not include:
- every equipment footprint
- every foundation dimension
- every matrix row from the layout chapter

Suggested caption:
- `Conceptual zoned plant layout based on segregated hazard-zone planning`

### 9.3 Slide 32: Utility Corridor and Routing Graphic

Purpose:
- show how utilities connect to the process train without relying on a full matrix dump

Recommended layout:
- process train shown as four simplified blocks:
  - storage / feed prep
  - reactor
  - separation / purification
  - waste / storage
- one side utility rack or corridor running parallel to the train

Utility lines to show:
- Steam
- Cooling water
- Electricity
- Nitrogen
- DM water

Recommended visual treatment:
- one color per utility
- short arrows or branch take-offs to major units
- small legend at corner

Required note:
- utility routing is separated from truck path and major hazard cluster

Do not include:
- exact pipe sizes
- exact header specs beyond broad service basis
- full utility island matrix

Suggested caption:
- `Indicative utility corridor arrangement for the selected BAC process train`

### 9.4 Optional Reactor Sketch

Purpose:
- support reactor slides only if a light visual is needed

Recommended features:
- vessel shell
- agitator
- external recirculation loop
- exchanger on loop
- feed inlet
- vent / pressure control point

Recommended use:
- only as a small supporting figure beside T-08 or T-09
- not as a separate full slide unless later needed

Do not include:
- detailed mechanical dimensions
- nozzle schedule
- fabrication detail

## 10. Slide Layout Templates For Visual Slides

### Template A: Full Figure Slide

Use for:
- Slide 11
- Slide 12
- Slide 13
- Slide 26

Structure:
- short title at top
- figure centered and dominant
- one caption line at bottom or 3 concise bullets on side

### Template B: Figure + Compact Table

Use for:
- Slide 30
- Slide 31 if a small basis table is retained
- Slide 32 if a compact routing note is retained

Structure:
- figure takes 60-70% width
- compact table or 3 bullets on the remaining side
- no second large visual

### Template C: Figure + Three Callouts

Use for:
- Slide 29

Structure:
- one central process or waste-handling schematic
- three short callout boxes:
  - safety
  - environmental control
  - waste handling

## 11. Visual Simplification Rules

- A custom visual should summarize, not reproduce, the source chapter.
- If a concept can be shown in 4 blocks, do not make it 10 blocks.
- Prefer zone labels and flow arrows over dense notes.
- Keep text inside custom figures under 25 words per region where possible.
- If the visual becomes more complex than the table it replaces, simplify again.

## 12. Priority Order For Custom Visual Creation

1. Slide 31 layout zoning graphic
2. Slide 29 SHE / waste / CETP logic graphic
3. Slide 32 utility corridor graphic
4. optional reactor sketch

