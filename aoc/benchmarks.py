from __future__ import annotations

import re

from aoc.models import BenchmarkManifest, ProjectConfig, SourceDomain


DEFAULT_REQUIRED_CHAPTERS = [
    "executive_summary",
    "introduction_product_profile",
    "market_capacity_selection",
    "literature_survey",
    "process_selection",
    "site_selection",
    "thermodynamic_feasibility",
    "reaction_kinetics",
    "block_flow_diagram",
    "process_description",
    "material_balance",
    "energy_balance",
    "heat_integration_strategy",
    "equipment_design_sizing",
    "mechanical_design_moc",
    "storage_utilities",
    "instrumentation_control",
    "hazop",
    "safety_health_environment_waste",
    "layout",
    "project_cost",
    "cost_of_production",
    "working_capital",
    "financial_analysis",
    "conclusion",
]

DEFAULT_EXPECTED_DECISIONS = [
    "capacity_case",
    "operating_mode",
    "route_selection",
    "site_selection",
    "reactor_choice",
    "separation_choice",
    "utility_basis",
    "economic_basis",
]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _benchmark_definitions() -> dict[str, BenchmarkManifest]:
    common_domains = [
        SourceDomain.TECHNICAL,
        SourceDomain.SAFETY,
        SourceDomain.MARKET,
        SourceDomain.SITE,
        SourceDomain.UTILITIES,
        SourceDomain.LOGISTICS,
        SourceDomain.REGULATORY,
        SourceDomain.ECONOMICS,
    ]
    return {
        "ethylene_glycol": BenchmarkManifest(
            benchmark_id="ethylene_glycol",
            target_product="Ethylene glycol",
            archetype_family="continuous_liquid_organic_heat_integrated",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Primary benchmark for continuous liquid organic synthesis with strong utility integration pressure.",
        ),
        "acetic_acid": BenchmarkManifest(
            benchmark_id="acetic_acid",
            target_product="Acetic acid",
            archetype_family="continuous_liquid_organic_reaction_separation",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for liquid organic route choice, purification, and India cost/logistics basis.",
        ),
        "sulfuric_acid": BenchmarkManifest(
            benchmark_id="sulfuric_acid",
            target_product="Sulfuric acid",
            archetype_family="continuous_inorganic_gas_absorption_energy_recovery",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for inorganic gas handling, absorption, and energy-recovery decisions.",
        ),
        "sodium_bicarbonate": BenchmarkManifest(
            benchmark_id="sodium_bicarbonate",
            target_product="Sodium bicarbonate",
            archetype_family="solids_crystallization_filtration_drying",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for solids-heavy processing with filtration, drying, and solids handling.",
        ),
        "para_nitroanisole": BenchmarkManifest(
            benchmark_id="para_nitroanisole",
            target_product="para-Nitroanisole",
            archetype_family="specialty_aromatic_separation_intensive",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for specialty aromatic substitution routes where route logic is plausible but sparse public property coverage should force an honest evidence-lock block unless the property basis improves.",
        ),
        "phenol": BenchmarkManifest(
            benchmark_id="phenol",
            target_product="Phenol",
            archetype_family="oxidation_recovery_liquid_organic",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for oxidation-led liquid-organic service with offgas handling, recovery distillation, and route-family coverage beyond the current core benchmark set.",
        ),
        "benzalkonium_chloride": BenchmarkManifest(
            benchmark_id="benzalkonium_chloride",
            target_product="Benzalkonium chloride",
            archetype_family="continuous_quaternary_ammonium_solution_cleanup",
            required_chapters=DEFAULT_REQUIRED_CHAPTERS,
            expected_decisions=DEFAULT_EXPECTED_DECISIONS,
            required_public_source_domains=common_domains,
            notes="Benchmark for continuous benzalkonium chloride manufacture on a 50 wt% sold-solution basis, emphasizing cited route selection, purification realism, unit-train consistency, and commercial-grade economics.",
        ),
    }


def build_benchmark_manifest(config: ProjectConfig) -> BenchmarkManifest:
    definitions = _benchmark_definitions()
    key = _normalize(config.benchmark_profile or config.basis.target_product)
    if key in definitions:
        return definitions[key]
    return BenchmarkManifest(
        benchmark_id=key or "custom_benchmark",
        target_product=config.basis.target_product,
        archetype_family=config.compound_family_hint or "custom",
        required_chapters=DEFAULT_REQUIRED_CHAPTERS,
        expected_decisions=DEFAULT_EXPECTED_DECISIONS,
        required_public_source_domains=[
            SourceDomain.TECHNICAL,
            SourceDomain.SAFETY,
            SourceDomain.MARKET,
            SourceDomain.SITE,
            SourceDomain.ECONOMICS,
        ],
        notes="Custom benchmark profile derived from project config. It uses the common any-compound chapter and decision expectations.",
    )
