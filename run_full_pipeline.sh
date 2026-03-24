#!/bin/bash
set -e
PROJECT_ID="eg-india-full-run-clean"
CONFIG="examples/ethylene_glycol_full_run_clean.yaml"

echo "Starting first run..."
aoc run --config $CONFIG

GATES=("heat_integration" "process_architecture" "design_basis" "equipment_basis" "hazop" "india_cost_basis" "final_signoff")

for GATE in "${GATES[@]}"; do
    echo "Approving gate: $GATE"
    aoc approve $PROJECT_ID --gate $GATE
    echo "Resuming pipeline..."
    aoc resume $PROJECT_ID
done

echo "Rendering final PDF..."
aoc render $PROJECT_ID
