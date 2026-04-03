# AoC Plant Design Engine

**AoC Plant Design** is a CLI-first plant design report generator that creates detailed technical-economic feasibility reports (TEFR) with typed artifacts, architectural solvers, and approval gates. Powered by generative AI and deterministic engineering models, it turns high-level compound inputs into rigorous, chapter-grade engineering reports.

## Features

- **Generic Flowsheet & Convergence:** Dynamically solves mass and energy balances using generic unit-sequence and recycle/purge solvers without hardcoding plant structures.
- **Thermo & Kinetics Kernel:** Ensures all high-sensitivity inputs (thermodynamic properties, kinetic models) are explicitly resolved, method-selected, and checked by a "critic" system before proceeding.
- **Deep Unit-Operation Sizing:** Calculates detailed reactor sizing, column hydraulics, pump power, and heat exchanger design instead of using generic throughput heuristics.
- **Mechanical Engine:** Generates appendix-grade vessel specs, nozzle schedules, and support designs.
- **Heat Recovery Architecture:** Recommends heat matchings across the plant and accounts for utility configurations.
- **Industrial Cost & Finance:** Itemizes CAPEX estimates and builds multi-year financial schedules/debt profiles.
- **Approval Gates:** A built-in gating system that pauses the generative pipeline for human-in-the-loop review on critical decisions like *Heat Integration*, *Process Architecture*, *HAZOP*, and *Cost Basis*.

## Requirements

- Python >= 3.11
- dependencies:
  - `pydantic>=2.9`
  - `PyYAML>=6.0`
  - `google-genai>=1.68.0`
  - `PyMuPDF>=1.24.0`

## Installation

You can install this repository directly as a package. In your virtual environment, run:

```bash
pip install -e .
```

This will expose the `aoc` CLI command.

## Usage

The primary interaction with the AoC engine is through its pipeline execution CLI. The typical execution flow runs a configuration YAML file through multiple gates.

### 1. Starting a Run

Run the base configuration to generate the initial artifacts up to the first gate:

```bash
aoc run --config examples/ethylene_glycol_full_run_clean.yaml
```

### 2. Approving Gates

The pipeline pauses at predefined gates (e.g., `process_architecture`, `equipment_basis`). To review and approve a stage, use:

```bash
aoc approve <PROJECT_ID> --gate <GATE_NAME>
```

*(You can add notes during approval through the API or interactive prompts).*

### 3. Resuming the Pipeline

Once a gate is cleared, resume the pipeline to advance to the next design phase:

```bash
aoc resume <PROJECT_ID>
```

### 4. Rendering the Final Report

After passing the `final_signoff` gate, generate the completed PDF report:

```bash
aoc render <PROJECT_ID>
```

## Live BAC Mode

The repository now includes a benzalkonium chloride benchmark config that switches the source layer from mock evidence to search-backed Gemini evidence while keeping the same solver and report pipeline:

```bash
python3 -m aoc run --config examples/benzalkonium_chloride_benchmark_live.yaml
```

See [docs/bac_real_data_mode.md](/Users/ayzaman/.gemini/antigravity/scratch/AoC/docs/bac_real_data_mode.md) for the expected data split, required `GEMINI_API_KEY`, and the gate-by-gate run sequence.

## Example Pipeline Script

The repository includes a helper script `run_full_pipeline.sh` that demonstrates an end-to-end automated run:

```bash
#!/bin/bash
PROJECT_ID="eg-india-full-run-clean"
CONFIG="examples/ethylene_glycol_full_run_clean.yaml"

aoc run --config $CONFIG

GATES=("heat_integration" "process_architecture" "design_basis" "equipment_basis" "hazop" "india_cost_basis" "final_signoff")

for GATE in "${GATES[@]}"; do
    aoc approve $PROJECT_ID --gate $GATE
    aoc resume $PROJECT_ID
done

aoc render $PROJECT_ID
```

## Project Vision & Backlog

AoC is currently transitioning toward a more general TEFR engine capable of designing complex flowsheets for **any compound** given sufficient public data. 

For more details on upcoming implementation stages regarding property methods, chemistry-family adapters, mechanical engines, and Critic system expansions, please see the [Any-Compound TEFR Backlog](docs/any_compound_tefr_backlog.md).
