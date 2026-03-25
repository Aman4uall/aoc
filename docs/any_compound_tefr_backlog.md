# AoC Any-Compound TEFR Backlog

This backlog turns the current AoC system into a more general technical-economic feasibility report engine without breaking the existing CLI, chapter flow, or India/public-data constraints.

The implementation rule for every high-impact engineering choice is:

1. search
2. extract
3. generate options
4. score with hard constraints
5. critic review
6. select
7. explain

## Target State

The target is not "write a long report for anything."  
The target is "solve and defend the report for any compound when public evidence is sufficient, and block explicitly when it is not."

## Milestones

### Milestone 1: Generic Flowsheet and Convergence Core

Status: in progress

Primary goal:
- replace family-shaped stream assembly with a generic unit-sequence and recycle/purge solver

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/convergence.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/convergence.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/flowsheet_sequence.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/materials.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solver_architecture.py)

Artifacts:
- `StreamTable`
- `FlowsheetCase`
- `SolveResult`
- later extension: `FlowsheetConvergencePacket`

Acceptance:
- EG remains green
- at least one non-EG benchmark uses the same solver path
- recycle and purge streams are explicit in the stream table
- unitwise closure comes from the solved stream sequence rather than family-specific inline branches

### Milestone 2: Method and Property Kernel v3

Primary goal:
- make thermo, kinetics, and critical properties method-selected and critic-checked before design

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/evidence.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/evidence.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/methods.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/methods.py)
- new: `aoc/property_methods.py`
- new: `aoc/thermo_methods.py`
- new: `aoc/kinetics_methods.py`

Artifacts:
- `ResolvedValue`
- `PropertyEstimate`
- `ThermoMethodDecision`
- `KineticsModelDecision`

Acceptance:
- no high-sensitivity thermo or kinetics input can silently pass unresolved
- method decisions appear in both `inspect` and annexures

### Milestone 3: Deep Unit-Operation Design Modules

Primary goal:
- move from throughput-based sizing to chapter-grade equipment calculations

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/solvers/units.py)
- new: `aoc/design/reactor.py`
- new: `aoc/design/distillation.py`
- new: `aoc/design/absorption.py`
- new: `aoc/design/crystallization.py`
- new: `aoc/design/exchangers.py`
- new: `aoc/design/pumps.py`

Artifacts:
- `ReactorDesignBasis`
- `ColumnHydraulics`
- `HeatExchangerThermalDesign`
- `PumpDesign`
- `EquipmentDatasheet`

Acceptance:
- reactor and column chapters contain equations, substitutions, and datasheet rows
- sodium bicarbonate path no longer relies on liquid-organic defaults

### Milestone 4: Mechanical Design Engine

Primary goal:
- extend screening mechanical outputs into appendix-grade vessel and support design packets

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/mechanical.py)
- new: `aoc/mechanical_vessels.py`
- new: `aoc/mechanical_supports.py`
- new: `aoc/mechanical_nozzles.py`

Artifacts:
- `MechanicalDesignBasis`
- `VesselMechanicalDesign`
- `SupportDesign`
- `NozzleSchedule`

Acceptance:
- shell, head, nozzle, support, corrosion allowance, and support-basis tables appear in annexures
- critics can block clearly unrealistic geometry or loading assumptions

### Milestone 5: Heat-Network Architecture

Primary goal:
- turn heat recovery into plant architecture instead of case ranking only

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/utility_architecture.py)
- new: `aoc/heat_network.py`
- new: `aoc/heat_matching.py`

Artifacts:
- `HeatStreamSet`
- `HeatMatchCandidate`
- `HeatNetworkCase`
- `HeatNetworkArchitecture`
- `UtilityArchitectureDecision`

Acceptance:
- EG can express a defendable reactor-heat-to-reboiler style architecture when the solved duties support it
- the selected network changes both utility OPEX and exchanger basis

### Milestone 6: Industrial Cost and Finance Engine

Primary goal:
- replace mostly factor-sheet economics with itemized plant costing and schedule-driven finance

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/economics_v2.py)
- new: `aoc/costing_equipment.py`
- new: `aoc/costing_installation.py`
- new: `aoc/project_finance.py`

Artifacts:
- `EquipmentCostBreakdown`
- `PlantCostSummary`
- `DebtSchedule`
- `TaxDepreciationBasis`
- `FinancialSchedule`

Acceptance:
- alternative technical architectures can change the economic winner
- equipment-wise cost buildup and multi-year schedules are present in the report package

### Milestone 7: Chemistry-Family Adapters

Primary goal:
- improve any-compound robustness by pairing the generic kernel with family-specific adapters

Modules:
- new: `aoc/families/organic_liquid.py`
- new: `aoc/families/gas_absorption.py`
- new: `aoc/families/solids_processing.py`
- new: `aoc/families/separation_intensive.py`

Artifacts:
- `ProcessArchetype`
- `AlternativeSet`
- family-specific `OptionSet` bundles

Acceptance:
- EG, acetic acid, sulfuric acid, and sodium bicarbonate remain the benchmark gate
- new compounds are onboarded through family classification first, not one-off branching logic

### Milestone 8: Critic Expansion and Report Hardening

Primary goal:
- prevent the report layer from inventing missing engineering substance

Modules:
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/validators.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/publish.py)
- [`/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/agent_fabric.py`](/Users/ayzaman/.gemini/antigravity/scratch/AoC/aoc/agent_fabric.py)

Artifacts:
- `CriticVerdict`
- `DecisionPacket`
- `OptionSet`

Acceptance:
- blocked artifacts stay blocked all the way to the report
- annexures include enough evidence and calc traces to audit the run

## Immediate Next Work

The next coding slice after the current one should be:

1. push the generic flowsheet solver from sequence-based heuristics to explicit separator and recycle-loop packets
2. make `solver_architecture.py` derive recycle-loop closure from those packets
3. attach unitwise unresolved sensitivities to each solved unit
4. add a critic that rejects flowsheets with missing recycle or purge destinations
