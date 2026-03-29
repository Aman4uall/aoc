# Economics and Finance v4 Backlog

This backlog tracks Stage 7 work that moves the economics/finance layer from strong annualized feasibility screening toward timing-aware project finance.

## Scope

Primary objective:
- make procurement timing, construction funding, debt-service coverage, and outage-linked revenue effects explicit in the cost and finance path

Guardrails:
- keep the current `project_cost`, `working_capital`, and `financial_analysis` stages intact
- remain at screening / feasibility-study rigor, not lender-model or tax-law precision
- keep every new timing field deterministic and critic-friendly

## Stage 7 Slices

### V7.1 Procurement Timing and DSCR Basis

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Delivered:
- procurement profile and construction-month basis on the cost model
- milestone-based CAPEX draw schedule
- interest during construction screening
- total project funding metric
- annual debt service and DSCR on the finance schedule
- outage-linked revenue-loss visibility in the finance chapter

Acceptance:
- project cost shows procurement timing instead of one flat CAPEX number
- financial analysis shows IDC, debt service, and DSCR
- validators block missing procurement timing and missing DSCR basis when debt service exists

### V7.2 Working-Capital Timing and Pre-Commissioning Inventory

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py)

Delivered:
- procurement-linked timing factor on the working-capital model
- explicit pre-commissioning inventory days, month, and inventory value
- peak working-capital month and peak funding burden
- financial-model total funding now uses peak working capital instead of only steady-state working capital
- working-capital and financial-analysis chapters now surface the timing basis directly
- validators now block missing timing-linked working-capital basis

Acceptance:
- working capital exposes both steady-state and peak funding basis
- pre-commissioning inventory is tied to procurement/construction timing rather than a generic fixed buffer
- financial analysis shows peak working capital and timing month
- validators block missing pre-commissioning inventory or timing-linked peak basis

### V7.3 Procurement Package Timing and Import-Duty Detail

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Delivered:
- procurement package family assignment by equipment class
- equipment-level lead time, award/delivery timing, import content, and import-duty burden
- procurement schedule aggregation from package-family timing instead of one flat template
- total import-duty burden on the cost model and in the report path
- equipment-wise costing now surfaces procurement family, lead time, and import duty
- validators now block missing procurement package timing detail

Acceptance:
- procurement timing is traceable by equipment class and package family
- import-duty burden is explicit in CAPEX and surfaced in project-cost/report outputs
- equipment-cost tables show package family, lead time, and import duty
- validators block cost models with procurement timing but no package-level detail

### V7.4 Lender Coverage Screening and Covenant Warnings

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py)

Delivered:
- LLCR and PLCR screening on the financial model
- CFADS visibility in annual schedule and debt-service tables
- explicit covenant warning list on the financial model
- financial-analysis and annexure surfaces for lender-style coverage screening
- validators now block missing lender-coverage basis and warn on weak LLCR/PLCR screens

Acceptance:
- financial model exposes DSCR, LLCR, and PLCR together
- debt-service coverage tables show CFADS rather than only debt-service outputs
- covenant warnings are visible in inspect/report output
- validators block debt-backed cases that lack LLCR/PLCR basis

### V7.5 Covenant Breach Propagation and Financing-Option Ranking

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py)

Delivered:
- machine-readable covenant breach codes on the financial model
- financing-option reranking against minimum DSCR, average DSCR, LLCR, and PLCR outcomes
- financing-basis reselection from real finance results instead of static preference scores alone
- approval-required propagation when the chosen financing option still carries covenant pressure
- finance chapter and inspect output for selected financing option, covenant breaches, and option ranking
- validator coverage that blocks silent covenant-breach selections without approval

Acceptance:
- weak LLCR/PLCR can push the financing-basis decision toward a more conservative option
- financing decisions surface candidate-level coverage results instead of only one final warning list
- selected financing basis matches the basis used by the financial model
- covenant-breaching selected options require approval instead of passing silently

### V7.6 Scenario-Aware Financing Ranking

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_validators.py)

Delivered:
- downside-scenario financing screening derived from scenario economics and candidate debt structures
- candidate-level downside DSCR, LLCR, and PLCR outputs in the financing option ranking
- automatic scenario-aware financing reversal when downside resilience materially outweighs the base preference
- explicit downside scenario name, downside-preferred financing option, and reversal flag on the financial model
- validator coverage that blocks silent scenario reversals without approval

Acceptance:
- downside scenarios can overturn the base financing selection instead of only generating warnings
- inspect and report output surface downside financing pressure explicitly
- financial-model and financing-decision artifacts remain aligned after downside reranking
- reversal-driven financing selections require approval when scenario sensitivity remains material

## Stage 7 Status

Stage 7 is complete for the planned scope.
