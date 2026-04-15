# AoC — Automated Plant Design & Feasibility Engine

> **Turn a compound name, capacity, and region into a 200+ table, 25-chapter Technical-Economic Feasibility Report (TEFR) — with zero manual engineering.**

AoC is a CLI-first engine that automates end-to-end chemical plant design: from literature survey and route selection through material/energy balances, equipment sizing, HAZOP, mechanical design, and multi-year financial analysis. It produces rigorous, chapter-grade engineering reports backed by deterministic solvers, typed artifacts, and human-in-the-loop approval gates — not generic AI-generated text.

---

## What Can AoC Do?

### 🔬 Process Design & Engineering
- **Route Discovery & Selection** — Surveys multiple synthesis routes for a target compound, scores them across maturity, safety, India fit, and operability, and selects the best architecture with full justification tables.
- **Generic Flowsheet Solving** — Dynamically solves mass and energy balances using a generic unit-sequence and recycle/purge solver. No hardcoded plant structures — the flowsheet is built from the chemistry.
- **Deep Unit-Operation Sizing** — Calculates detailed reactor sizing (CSTR/PFR kinetics), distillation column hydraulics, heat exchanger thermal design, pump curves, and storage vessel design — not generic throughput heuristics.
- **Thermodynamics & Kinetics Kernel** — Resolves all high-sensitivity inputs (activity coefficients, K-values, kinetic parameters) through explicit method selection, property packages, and a "critic" system before proceeding to design.

### 🏗️ Mechanical & Safety Engineering
- **Mechanical Design Engine** — Generates appendix-grade vessel specs: shell/head thickness, corrosion allowance, nozzle schedules, support design, and MoC (material of construction) screening.
- **HAZOP Node Register** — Builds equipment-linked HAZOP nodes with deviation/cause/consequence/safeguard tables tied to actual flowsheet nodes and control loops.
- **Instrumentation & Control Plans** — Derives control loop architectures (temperature cascade, pressure override, feed ratio, level, blanketing) directly from the solved equipment list.

### 🔥 Heat Integration & Utilities
- **Heat Recovery Architecture** — Evaluates heat integration cases (no recovery, multi-effect, HTM loop) across route alternatives and recommends matchings.
- **Utility Architecture** — Designs utility islands (steam, power, cooling water, nitrogen) with header/loop topology, peak demand, and annualized cost breakdowns.

### 💰 Industrial Economics & Finance
- **Itemized CAPEX** — Equipment-wise cost buildup with installation factors, indirect costs, contingency, and procurement timing schedules.
- **Cost of Production** — Manufacturing cost breakdown: raw materials, utilities, labor, maintenance, and recurring service burdens.
- **Multi-Year Financial Analysis** — Builds complete financial schedules: debt service coverage, tax depreciation, working capital, IRR/NPV sensitivity, and scenario analysis (base/conservative/upside).

### 📄 Report Generation
- **25-Chapter TEFR** — Produces a structured Markdown + PDF report with 200+ tables, mermaid diagrams, calculation traces, and annexures.
- **Deterministic Diagram Architecture** — Builds BFD, PFD, and control diagrams through a modular `semantics -> modules -> sheet composition -> render/export` pipeline rather than single-pass freeform drawing.
- **Dual Diagram Outputs** — Publishes SVG as the source-of-truth render and Draw.io as an editable export generated from the same typed diagram artifacts.
- **Benchmark Parity System** — Validates report completeness against a chapter/support contract framework to ensure nothing is missing.
- **Report Formatting Pipeline** — Academic-style PDF rendering with styled typography, table numbering, and figure embedding.

### 🔒 Governance & Auditability
- **Approval Gates** — 7 built-in gates pause the pipeline for human review at critical decisions: evidence lock, heat integration, process architecture, design basis, equipment basis, HAZOP, cost basis, and final signoff.
- **Typed Artifact Store** — Every intermediate result (200+ artifact types) is persisted as versioned, typed JSON. The run is fully reproducible and auditable.
- **Critic Registry** — Cross-cutting validation system that flags warnings and blockers across thermodynamics, kinetics, separation, economics, safety, and report quality.
- **Evidence & Source Resolution** — Deterministic source ranking system that scores evidence by authority, recency, geography, domain fit, and consistency.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│                  aoc run | approve | resume | render        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                   Pipeline Runner                           │
│  30 sequential stages, artifact dependencies, gate control  │
└────┬──────────┬──────────┬──────────┬──────────┬────────────┘
     │          │          │          │          │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼──────────┐
│Reasoning│ │Decision│ │Solvers │ │Calculat│ │  Validators  │
│Service  │ │Engine  │ │& Flow- │ │ors     │ │  & Critics   │
│(Gemini/ │ │(route, │ │sheet   │ │(sizing,│ │  (200+ rules)│
│ mock)   │ │site,   │ │conver- │ │balance,│ │              │
│         │ │heat,   │ │gence)  │ │costing)│ │              │
│         │ │econ)   │ │        │ │        │ │              │
└────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └──────────────┘
     │          │          │          │
┌────▼──────────▼──────────▼──────────▼──────────────────────┐
│                    Typed Models Layer                       │
│           200+ Pydantic models (aoc/models.py)             │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────┐
│                    Artifact Store                          │
│          JSON persistence per project under outputs/      │
└───────────────────────────────────────────────────────────┘
```

### Pipeline Stages (30 total)

The pipeline runs through 30 sequential stages, each producing typed artifacts that feed downstream stages:

| # | Stage | Key Outputs | Gate |
|---|-------|-------------|------|
| 1 | Project Intake | Research bundle, resolved sources, benchmark manifest | — |
| 2 | Product Profile | Cited properties, uses, safety notes | — |
| 3 | Market & Capacity | Market assessment, India price data, capacity decision | — |
| 4 | Literature Survey | Route survey, route chemistry, route discovery | — |
| 5 | Property Gap Resolution | Property gap analysis, resolved values, property packages | **Evidence Lock** |
| 6 | Site Selection | Scored India site candidates | — |
| 7 | Process Synthesis | Operating mode, route candidates, family adapters | — |
| 8 | Rough Alternatives | Preliminary mass/energy balance per route | — |
| 9 | Heat Integration | Heat recovery cases, HTM/multi-effect evaluation | **Heat Integration** |
| 10 | Route Selection | Final route, reactor/separation/utility decisions | **Process Architecture** |
| 11 | Thermodynamics | Thermo methods, property methods, separation thermo | — |
| 12 | Kinetics | Kinetic methods, Arrhenius fits | — |
| 13 | Block Diagram | Mermaid BFD, process narrative | — |
| 14 | Process Description | Solver-derived unit sequence and section topology | — |
| 15 | Material Balance | Reaction system, stream table, flowsheet graph | — |
| 16 | Energy Balance | Energy balance, solve result, mixture properties | **Design Basis** |
| 17 | Reactor Design | Reactor sizing, design basis traces | — |
| 18 | Distillation Design | Column hydraulics, exchanger thermal design | — |
| 19 | Equipment Sizing | Storage, pumps, equipment list, datasheets | **Equipment Basis** |
| 20 | Mechanical Design | Vessel specs, MoC, nozzle schedules | — |
| 21 | Storage & Utilities | Utility summary, utility architecture | — |
| 22 | Instrumentation | Control loops, control architecture | — |
| 23 | HAZOP & SHE | HAZOP nodes, safety/environment narrative | **HAZOP** |
| 24 | Layout | Plot plan, layout decision | — |
| 25 | Project Cost | CAPEX buildup, plant cost summary | — |
| 26 | Cost of Production | Manufacturing cost breakdown | — |
| 27 | Working Capital | Inventory/receivable/payable model | — |
| 28 | Financial Analysis | IRR, NPV, debt schedule, scenarios | **India Cost Basis** |
| 29 | Final Report | 25-chapter Markdown TEFR, 200+ tables | **Final Signoff** |

### Key Modules

| Module | Size | Purpose |
|--------|------|---------|
| `pipeline.py` | 500 KB | Pipeline orchestration, 30-stage execution, artifact wiring |
| `models.py` | 134 KB | 200+ Pydantic data models for every artifact type |
| `decision_engine.py` | 134 KB | Route selection, heat integration, process synthesis |
| `scientific_inference.py` | 172 KB | Claim graphs, scientific gate matrices, data reality audit |
| `validators.py` | 209 KB | 100+ validation rules, cross-chapter consistency checks |
| `economics_v2.py` | 159 KB | CAPEX, OPEX, financial schedules, debt, tax depreciation |
| `reasoning.py` | 127 KB | Gemini-backed and mock reasoning services |
| `publish.py` | 103 KB | Report assembly, PDF rendering, annexure generation |
| `formatter.py` | 118 KB | Academic report formatting, benchmark parity |
| `calculators.py` | 81 KB | Equipment sizing: reactor, column, exchanger, storage |
| `mechanical.py` | 35 KB | Vessel mechanical design, MoC, nozzle schedules |
| `flowsheet.py` | 41 KB | Flowsheet graph, control plans, HAZOP nodes |
| `evidence.py` | 16 KB | Source ranking, conflict resolution, value resolution |
| `llm.py` | 7 KB | Gemini/Vertex AI client with structured generation |

### Data Flow

1. **Config → Research** — A YAML config defines the compound, capacity, and region. The reasoning service discovers sources (Gemini search or mock seeds).
2. **Research → Design Basis** — Sources are ranked, properties resolved, routes surveyed and scored. Approval gates enforce human review.
3. **Design Basis → Engineering** — The selected route drives flowsheet construction, material/energy balances, and equipment sizing through deterministic solvers.
4. **Engineering → Economics** — Equipment costs, utility costs, and operating expenses feed a multi-year financial model with scenario analysis.
5. **Economics → Report** — All artifacts are assembled into a 25-chapter Markdown report, validated for benchmark parity, and rendered to PDF.
6. **Diagram Delivery Contract** — Diagram semantics, module layouts, SVG sheets, acceptance artifacts, and Draw.io exports are persisted as first-class outputs under the project artifact store.

---

## Codebase Structure

```
AoC/
├── aoc/                          # Core Python package
│   ├── __main__.py               # Entry point
│   ├── cli.py                    # CLI argument parsing (run/approve/resume/render/inspect)
│   ├── config.py                 # YAML config loading and validation
│   ├── pipeline.py               # 30-stage pipeline orchestration
│   ├── models.py                 # 200+ typed Pydantic models
│   ├── reasoning.py              # Gemini-backed + mock reasoning services
│   ├── llm.py                    # Google Gemini / Vertex AI client
│   ├── decision_engine.py        # Route, site, heat-integration decisions
│   ├── scientific_inference.py   # Claim graphs, scientific gates, data audit
│   ├── calculators.py            # Equipment sizing (reactor, column, HX, pump)
│   ├── economics_v2.py           # CAPEX, OPEX, finance, debt schedules
│   ├── validators.py             # 100+ validation and critic rules
│   ├── evidence.py               # Source ranking and value resolution
│   ├── flowsheet.py              # Flowsheet graph, control plans, HAZOP
│   ├── mechanical.py             # Vessel and mechanical design
│   ├── publish.py                # Report assembly and PDF rendering
│   ├── formatter.py              # Academic formatting and parity
│   ├── solvers/                  # Convergence, flowsheet sequence, materials
│   └── properties/               # Property packages, thermo methods
├── examples/                     # YAML project configurations
│   ├── ethylene_glycol_full_run_clean.yaml
│   ├── benzalkonium_chloride_benchmark_live.yaml
│   ├── acetone_india.yaml
│   └── ...
├── outputs/                      # Generated reports and artifacts
├── docs/                         # Design backlogs and documentation
├── tests/                        # Test suite
├── pyproject.toml                # Package configuration
├── requirements.txt              # Python dependencies
└── run_full_pipeline.sh          # End-to-end automation script
```

---

## Getting Started

### Requirements

- Python ≥ 3.11
- Dependencies: `pydantic>=2.9`, `PyYAML>=6.0`, `google-genai>=1.68.0`, `PyMuPDF>=1.24.0`, `chemicals>=1.3.2`, `thermo>=0.4.2`

### Installation

```bash
# Clone the repository
git clone https://github.com/Aman4uall/aoc.git
cd aoc

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install as an editable package
pip install -e .
```

### Environment Setup

For **live mode** (Gemini-powered):
```bash
# Option A: API key
export GEMINI_API_KEY="your-api-key"

# Option B: Vertex AI (service account)
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

For **mock mode** (no API key needed — ideal for testing):
```yaml
# In your config YAML:
model:
  backend: mock
```

---

## Usage

### 1. Starting a Run

```bash
aoc run --config examples/ethylene_glycol_full_run_clean.yaml
```

The pipeline runs until it hits an approval gate, then pauses.

### 2. Inspecting Run State

```bash
aoc inspect <PROJECT_ID>
```

Shows current stage, completed stages, gate statuses, blocking issues, and chapter progress.

### 3. Approving Gates

```bash
aoc approve <PROJECT_ID> --gate <GATE_NAME>
```

Gates in order: `evidence_lock` → `heat_integration` → `process_architecture` → `design_basis` → `equipment_basis` → `hazop` → `india_cost_basis` → `final_signoff`

### 4. Resuming the Pipeline

```bash
aoc resume <PROJECT_ID>
```

### 5. Rendering the Final PDF

```bash
aoc render <PROJECT_ID>
```

### Full Automated Run

```bash
#!/bin/bash
PROJECT_ID="eg-india-full-run-clean"
CONFIG="examples/ethylene_glycol_full_run_clean.yaml"

aoc run --config $CONFIG

GATES=("evidence_lock" "heat_integration" "process_architecture" "design_basis" "equipment_basis" "hazop" "india_cost_basis" "final_signoff")

for GATE in "${GATES[@]}"; do
    aoc approve $PROJECT_ID --gate $GATE
    aoc resume $PROJECT_ID
done

aoc render $PROJECT_ID
```

### Writing a Config

A minimal YAML config looks like:

```yaml
project_id: my-project
basis:
  target_product: Acetone
  capacity_tpa: 100000
  target_purity_wt_pct: 99.5
  operating_mode: continuous
  annual_operating_days: 330
  region: India
  currency: INR
output_root: outputs
model:
  backend: google          # or "mock" for offline testing
  model_name: gemini-3.1-pro-preview
  temperature: 0.2
```

See the `examples/` directory for fully configured projects including Ethylene Glycol, Benzalkonium Chloride, Acetone, Phenol, Sulfuric Acid, and Sodium Bicarbonate.

---

## Tested Compounds

AoC has been benchmarked against the following compound classes:

| Compound | Family | Pipeline Status |
|----------|--------|----------------|
| Ethylene Glycol | Liquid hydration train | ✅ Full runs (mock + live) |
| Benzalkonium Chloride | Quaternization liquid train | ✅ Full runs (26+ iterations) |
| Acetone | Oxidation/dehydrogenation | ✅ Config ready |
| Ibuprofen | Extraction recovery train | ✅ Multiple exploratory runs |
| Acetic Acid | Carbonylation liquid train | ✅ Mock benchmark |
| Sulfuric Acid | Gas absorption converter | ✅ Mock benchmark |
| Sodium Bicarbonate | Solids carboxylation train | ✅ Mock benchmark |
| Phenol | Oxidation recovery train | ✅ Mock benchmark |

---

## Strengths

### ✅ Engineering-First, Not AI-First
Every number in the report comes from a deterministic solver or explicitly cited source — not from language model hallucination. The LLM is used for research, narrative generation, and structured extraction, but never for critical engineering calculations.

### ✅ Full TEFR Scope
Covers the complete feasibility study lifecycle: from literature survey through 25 report chapters including material balance, equipment design, HAZOP, mechanical design, and 10-year financial projections.

### ✅ Typed & Auditable
200+ Pydantic models enforce data contracts between stages. Every intermediate artifact is persisted as JSON. Runs are fully reproducible — rerun a config to get the same report.

### ✅ Approval Gates
7 mandatory human checkpoints prevent the engine from proceeding on weak assumptions. Engineers can review and challenge decisions at each critical juncture.

### ✅ India-Grounded Economics
Built-in support for India-specific tariffs, site candidates, labor costs, logistics, and INR-normalized financial modeling. Geography-aware source ranking prioritizes India-grounded evidence.

### ✅ Multi-Route Decision Framework
Evaluates 3+ routes per compound, scoring across maturity, safety, operability, heat integration, separation complexity, and India deployment fit before selecting a winner.

### ✅ Scientific Inference Layer
Claim graphs, species resolution, scientific gate matrices, and data reality audits prevent the system from proceeding when public evidence is insufficient. It blocks explicitly rather than guessing.

### ✅ Mock Mode for Testing
A complete mock reasoning service with realistic seeded data lets you run the full pipeline offline — no API key, no network, no cost.

---

## Limitations

### ⚠️ Not a Replacement for Detailed Engineering
AoC produces **preliminary feasibility-level** reports, not detailed engineering packages. Equipment sizing uses heuristic correlations and screening methods. Outputs should be validated by professional process engineers before investment decisions.

### ⚠️ Public Data Dependency
The quality of live-mode outputs depends entirely on the availability and quality of public data for a given compound. Niche or novel compounds with sparse literature may produce incomplete or blocked reports.

### ⚠️ LLM Variability in Live Mode
When using the Gemini backend for source discovery and narrative generation, outputs can vary between runs. The mock backend provides deterministic reproducibility for benchmarking.

### ⚠️ India-Centric Financial Modeling
The economics engine is currently optimized for Indian site selection, INR-based tariffs, and India labor/utility cost structures. International projects require manual adaptation of the financial basis.

### ⚠️ Limited Compound Family Coverage
While the engine is designed for "any compound," the route family adapters are currently strongest for:
- Liquid-phase organic reactions (hydration, oxidation, quaternization)
- Gas-absorption processes (contact process style)
- Crystallization/solids processes (Solvay style)

Novel reaction families (e.g., photochemistry, electrochemistry, bioprocesses) are not yet supported.

### ⚠️ Single-Product Plants Only
The engine designs dedicated single-product facilities. Multi-product campaigns, shared infrastructure, or integrated complexes are out of scope.

### ⚠️ No Dynamic Simulation
Balances and sizing are steady-state only. No transient startup/shutdown modeling, batch scheduling optimization, or dynamic controllability analysis.

### ⚠️ Early-Stage Codebase
The codebase is actively evolving. Some modules are large (~500KB `pipeline.py`) and are in the process of being refactored into smaller, more focused components. See the `docs/` directory for active backlogs.

---

## Project Vision & Roadmap

AoC is transitioning toward a general TEFR engine capable of designing complex flowsheets for **any compound** given sufficient public data. Key roadmap items:

1. **Generic flowsheet convergence** — Replace family-shaped assembly with explicit separator and recycle-loop packets
2. **Property method kernel v3** — Make thermo/kinetics inputs method-selected and critic-checked
3. **Deep unit-operation design** — Move from screening to chapter-grade reactor, column, and exchanger calculations
4. **Heat-network architecture** — Turn heat recovery into plant architecture, not just case ranking
5. **Industrial cost engine** — Itemized plant costing with procurement-driven schedules
6. **Chemistry-family adapters** — Onboard new compounds through family classification, not one-off branching
7. **Critic expansion** — Prevent report-layer invention of missing engineering substance

See [docs/any_compound_tefr_backlog.md](docs/any_compound_tefr_backlog.md) for the full implementation backlog.

---

## License

Private repository — not currently open-source.
