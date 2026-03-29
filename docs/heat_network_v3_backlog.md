# Heat Network v3 Backlog

This backlog tracks the Stage 5 heat-network work that pushes utility integration from a selected train summary toward explicit plant architecture.

## Scope

Primary objective:
- turn the selected utility train into a richer network architecture with composite intervals, utility islands, and clearer downstream consequences for costing and design

Guardrails:
- keep `UtilityArchitectureDecision` compatible with the current equipment, economics, and report path
- avoid replacing the existing train synthesis until the richer architecture artifacts are stable and critic-checked

## Stage 5 Slices

### V5.1 Composite Intervals and Utility Islands

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)

Artifacts:
- `HeatCompositeInterval`
- `HeatUtilityIsland`
- `HeatStreamSet.composite_intervals`
- `HeatNetworkCase.utility_islands`
- `HeatNetworkArchitecture.selected_island_ids`
- `HeatExchangerTrainStep.island_id`
- `UtilityTrainPackageItem.island_id`

Acceptance:
- the selected utility architecture exposes composite thermal intervals and explicit utility islands
- selected train steps and package items are attached to islands instead of existing only as a flat list
- critics can block missing island assignments and missing composite intervals

### V5.2 Island-Aware Train Selection and Balancing

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py)

Artifacts:
- island-level `candidate_match_count`
- island-level `recoverable_potential_kw`
- island-level `target_recovered_duty_kw`
- island-level `selection_priority`

Acceptance:
- train selection allocates recovered-duty targets across disconnected utility islands before building train steps
- selected train steps and package items retain island assignments from the selection stage itself
- critics can block islands whose target exceeds potential or whose recovered duty exceeds allocated target

### V5.3 Island-Level Economic Coupling

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Artifacts:
- `UtilityIslandEconomicImpact`
- `UtilityIslandScenarioImpact`
- `CostModel.utility_island_costs`
- `CostModel.annual_utility_island_service_cost`
- `ScenarioResult.utility_island_impacts`

Acceptance:
- utility islands contribute explicit CAPEX burden and recurring service burden, not only train-level totals
- scenario results carry island-aware operating and service impacts
- project cost, financial analysis, `inspect()`, and annexures expose utility-island economics directly

### V5.4 Richer Network Architecture Cases

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py)

Artifacts:
- `HeatNetworkCase.base_case_id`
- `HeatNetworkCase.architecture_family`
- `HeatNetworkCase.header_count`
- `HeatNetworkCase.shared_htm_island_count`
- `HeatNetworkCase.condenser_reboiler_cluster_count`
- `HeatUtilityIsland.architecture_role`
- `HeatUtilityIsland.header_level`
- `HeatUtilityIsland.cluster_id`
- `HeatExchangerTrainStep.header_level`
- `HeatExchangerTrainStep.cluster_id`
- `UtilityTrainPackageItem.package_role="header"`

Acceptance:
- utility architecture expands richer topology variants from the same solved heat-match basis instead of only one flat case
- shared HTM islands, condenser-reboiler clusters, and staged utility headers are represented explicitly in selected cases when applicable
- critics can block missing header/cluster metadata when those richer architectures are selected

### V5.5 Island-Aware Design Package Selection

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/design_artifacts.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/design_artifacts.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Artifacts:
- `ReactorDesign.utility_architecture_family`
- `ReactorDesign.selected_utility_island_ids`
- `ReactorDesign.selected_utility_header_levels`
- `ReactorDesign.selected_utility_cluster_ids`
- `ReactorDesign.allocated_recovered_duty_target_kw`
- `ColumnDesign.utility_architecture_family`
- `ColumnDesign.selected_utility_island_ids`
- `ColumnDesign.selected_utility_header_levels`
- `ColumnDesign.selected_utility_cluster_ids`
- `ColumnDesign.allocated_reboiler_recovery_target_kw`
- `ColumnDesign.allocated_condenser_recovery_target_kw`
- `HeatExchangerDesign.utility_architecture_family`
- `HeatExchangerDesign.selected_island_id`
- `HeatExchangerDesign.selected_header_level`
- `HeatExchangerDesign.selected_cluster_id`
- `HeatExchangerDesign.allocated_recovered_duty_target_kw`

Acceptance:
- reactor, column, and exchanger design now rank utility-train steps using selected-case family, island targets, header levels, and cluster metadata instead of only flat recovered duty
- reboiler and condenser package selection prefer the package family and island role consistent with the chosen utility architecture
- chapters and datasheets expose the architecture-family and island-target basis directly

### V5.6 Island Maintenance Timing and Mechanical Consequences

Status:
- implemented

Modules:
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/models.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/pipeline.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_utility_architecture.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_calculators.py)
- [/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py](/Users/ayzaman/.gemini/antigravity/scratch/AoC/tests/test_pipeline.py)

Artifacts:
- `HeatUtilityIsland.shared_htm_inventory_m3`
- `HeatUtilityIsland.header_design_pressure_bar`
- `HeatUtilityIsland.condenser_reboiler_pair_score`
- `HeatUtilityIsland.control_complexity_factor`
- `UtilityIslandEconomicImpact.maintenance_cycle_years`
- `UtilityIslandEconomicImpact.replacement_event_cost_inr`
- `UtilityIslandEconomicImpact.annualized_replacement_cost_inr`
- `UtilityIslandEconomicImpact.planned_turnaround_days`
- `ScenarioResult.annual_utility_island_replacement_cost_inr`
- `FinancialScheduleLine.utility_island_service_cost_inr`
- `FinancialScheduleLine.utility_island_replacement_cost_inr`
- `FinancialScheduleLine.utility_island_turnaround_cost_inr`

Acceptance:
- utility islands now carry explicit HTM inventory, staged-header pressure, pair-scoring, and control-complexity metadata
- economics track island service and replacement separately, with year-specific island replacement and turnaround events in the financial schedule
- project-cost, financial-analysis, inspect, annexures, and mechanical screening all expose the richer island consequences directly

## Stage 5 Status

Stage 5 is complete for the current roadmap scope.

Delivered:
- composite intervals and explicit utility islands
- island-aware train selection
- island-level CAPEX and OPEX coupling
- richer shared-HTM, condenser-reboiler-cluster, and staged-header cases
- island-aware reactor, column, and exchanger package selection
- island maintenance timing, replacement phasing, and mechanical/control-package consequences

Next logical move:
- Stage 6, with deeper mechanical design and plant-detail coupling on top of the utility-network architecture now in place
