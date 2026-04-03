# BAC Real-Data Mode

This run mode is the clean path for moving benzalkonium chloride off the mock evidence backend and onto fetched/search-backed evidence while keeping the same solver and report pipeline.

## What changes

- `model.backend: google`
- `benchmark_profile: benzalkonium_chloride`
- `strict_citation_policy: true`
- `throughput_basis: finished_product`
- `nominal_active_wt_pct: 50.0`
- optional local evidence in `user_documents`
- optional India market inputs in `india_market_sheets`

The reference config is:

- [examples/benzalkonium_chloride_benchmark_live.yaml](/Users/ayzaman/.gemini/antigravity/scratch/AoC/examples/benzalkonium_chloride_benchmark_live.yaml)

## What becomes live/fetched

- source discovery
- product-profile drafting
- market and price basis
- route survey
- site selection
- thermo and kinetics narrative assessments

These come from the `GeminiReasoningService` through search-backed source discovery and structured generation with citations.

## What remains solver-derived

- route chemistry graph
- property-demand planning
- scientific gates
- flowsheet synthesis
- material and energy balance
- reactor / separation sizing
- utilities
- mechanical design
- economics and finance

## Requirements

- `GEMINI_API_KEY` must be set
- `google-genai` installed
- if you provide local BAC PDFs/CSVs, use absolute paths in the config

## Suggested BAC live run

```bash
python3 -m aoc run --config examples/benzalkonium_chloride_benchmark_live.yaml
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate evidence_lock
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate heat_integration
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate process_architecture
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate design_basis
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate equipment_basis
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate hazop
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate india_cost_basis
python3 -m aoc resume benzalkonium-chloride-benchmark-live
python3 -m aoc approve benzalkonium-chloride-benchmark-live --gate final_signoff
python3 -m aoc render benzalkonium-chloride-benchmark-live
```

## Current BAC realism targets for live mode

- replace seeded BAC route evidence with cited route evidence
- replace seeded price/site basis with fetched India-specific evidence
- preserve the current 50 wt% sold-solution benchmark contract
- keep solver warnings visible when live evidence is still incomplete
