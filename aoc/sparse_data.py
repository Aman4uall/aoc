from __future__ import annotations

from aoc.models import (
    ChemistryFamilyAdapter,
    ProjectConfig,
    ProvenanceTag,
    SparseDataPolicyArtifact,
    SparseDataPolicyRule,
)
from aoc.properties.models import PropertyPackage, PropertyPackageArtifact
from aoc.properties.sources import normalize_chemical_name


_PACKAGE_SUBJECTS = {
    "molecular_weight",
    "normal_boiling_point",
    "melting_point",
    "liquid_density",
    "liquid_viscosity",
    "liquid_heat_capacity",
    "heat_of_vaporization",
    "thermal_conductivity",
}


def _rule(
    adapter: ChemistryFamilyAdapter,
    *,
    stage_id: str,
    subject: str,
    artifact_family: str,
    allow_calculated: bool = True,
    allow_estimated: bool = True,
    allow_analogy: bool = False,
    allow_heuristic_fallback: bool = False,
    minimum_confidence: float = 0.0,
    block_when_missing: bool = True,
    rationale: str,
) -> SparseDataPolicyRule:
    return SparseDataPolicyRule(
        rule_id=f"{adapter.adapter_id}_{stage_id}_{subject}",
        stage_id=stage_id,
        subject=subject,
        artifact_family=artifact_family,
        preferred_resolution_order=[
            ProvenanceTag.SOURCED,
            ProvenanceTag.CALCULATED,
            ProvenanceTag.ESTIMATED,
            ProvenanceTag.ANALOGY,
        ],
        allow_calculated=allow_calculated,
        allow_estimated=allow_estimated,
        allow_analogy=allow_analogy,
        allow_heuristic_fallback=allow_heuristic_fallback,
        minimum_confidence=minimum_confidence,
        block_when_missing=block_when_missing,
        rationale=rationale,
        citations=adapter.citations,
        assumptions=adapter.assumptions,
    )


def _primary_packages(property_packages: PropertyPackageArtifact) -> list[PropertyPackage]:
    primary_ids = set(property_packages.primary_identifier_ids)
    if not primary_ids:
        return list(property_packages.packages)
    return [package for package in property_packages.packages if package.identifier.identifier_id in primary_ids]


def _evaluate_package_rule(rule: SparseDataPolicyRule, packages: list[PropertyPackage]) -> SparseDataPolicyRule:
    status = "covered"
    triggered: list[str] = []
    for package in packages:
        prop = getattr(package, rule.subject, None)
        package_name = package.identifier.canonical_name
        if prop is None:
            if rule.block_when_missing:
                status = "blocked"
            else:
                status = "warning" if status != "blocked" else status
            triggered.append(f"{package_name}: missing")
            continue
        if prop.blocking or prop.resolution_status == "blocked":
            status = "blocked"
            triggered.append(f"{package_name}: blocked")
            continue
        if prop.provenance_method == ProvenanceTag.ANALOGY and not rule.allow_analogy:
            status = "blocked"
            triggered.append(f"{package_name}: analogy disallowed")
            continue
        if prop.provenance_method == ProvenanceTag.CALCULATED and not rule.allow_calculated:
            status = "blocked"
            triggered.append(f"{package_name}: calculated basis disallowed")
            continue
        if prop.resolution_status == "estimated":
            if not rule.allow_estimated:
                status = "blocked"
                triggered.append(f"{package_name}: estimated basis disallowed")
                continue
            if prop.confidence < rule.minimum_confidence and status != "blocked":
                status = "warning"
                triggered.append(f"{package_name}: estimated confidence {prop.confidence:.2f} < {rule.minimum_confidence:.2f}")
        elif prop.confidence < rule.minimum_confidence and status != "blocked":
            status = "warning"
            triggered.append(f"{package_name}: confidence {prop.confidence:.2f} < {rule.minimum_confidence:.2f}")
    return rule.model_copy(update={"current_status": status, "triggered_items": triggered}, deep=True)


def _evaluate_pair_rule(
    rule: SparseDataPolicyRule,
    unresolved_items: list[str],
    *,
    resolved_count: int = 0,
) -> SparseDataPolicyRule:
    if not unresolved_items:
        return rule
    status = "blocked" if resolved_count == 0 and rule.block_when_missing and not rule.allow_heuristic_fallback else "warning"
    return rule.model_copy(update={"current_status": status, "triggered_items": unresolved_items}, deep=True)


def build_sparse_data_policy(
    config: ProjectConfig,
    family_adapter: ChemistryFamilyAdapter,
    property_packages: PropertyPackageArtifact,
) -> SparseDataPolicyArtifact:
    base_rules = [
        _rule(
            family_adapter,
            stage_id="thermodynamic_feasibility",
            subject="molecular_weight",
            artifact_family="pure_component_identity",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.55,
            rationale="Thermodynamic screening may proceed on a cited or defensible estimated molecular-weight basis, but not on analogy.",
        ),
        _rule(
            family_adapter,
            stage_id="thermodynamic_feasibility",
            subject="normal_boiling_point",
            artifact_family="pure_component_thermo",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.60,
            rationale="Boiling-point basis may be estimated when public anchors exist, but low-confidence or analogy-only values should not pass silently.",
        ),
        _rule(
            family_adapter,
            stage_id="energy_balance",
            subject="liquid_heat_capacity",
            artifact_family="bulk_thermal_properties",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.55,
            rationale="Energy balance may use estimated heat capacity only above a minimum confidence threshold.",
        ),
        _rule(
            family_adapter,
            stage_id="energy_balance",
            subject="heat_of_vaporization",
            artifact_family="bulk_thermal_properties",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.55,
            rationale="Latent-duty handling may use estimated vaporization enthalpy only when the estimate remains confidence-anchored.",
        ),
        _rule(
            family_adapter,
            stage_id="reactor_design",
            subject="liquid_density",
            artifact_family="transport_properties",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.60,
            rationale="Reactor sizing may accept estimated density, but not low-confidence or analogy-only transport data.",
        ),
        _rule(
            family_adapter,
            stage_id="reactor_design",
            subject="liquid_viscosity",
            artifact_family="transport_properties",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.60,
            rationale="Reactor heat-transfer and hydraulics require viscosity with enough confidence for Reynolds/Nusselt screening.",
        ),
        _rule(
            family_adapter,
            stage_id="distillation_design",
            subject="liquid_density",
            artifact_family="separation_transport",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.60,
            rationale="Process-unit hydraulics may use estimated density only above the family policy threshold.",
        ),
        _rule(
            family_adapter,
            stage_id="distillation_design",
            subject="liquid_viscosity",
            artifact_family="separation_transport",
            allow_estimated=True,
            allow_analogy=False,
            minimum_confidence=0.60,
            rationale="Process-unit hydraulics may use estimated viscosity only above the family policy threshold.",
        ),
    ]
    if family_adapter.adapter_id == "inorganic_absorption_conversion_train":
        base_rules.append(
            _rule(
                family_adapter,
                stage_id="distillation_design",
                subject="henry_constants",
                artifact_family="gas_liquid_equilibrium",
                allow_estimated=False,
                allow_analogy=False,
                allow_heuristic_fallback=False,
                block_when_missing=True,
                rationale="Absorber-centric families must not finalize detailed absorber design on heuristic Henry-law fallback alone.",
            )
        )
    elif family_adapter.adapter_id == "solids_crystallization_train":
        base_rules.append(
            _rule(
                family_adapter,
                stage_id="distillation_design",
                subject="solubility_curve",
                artifact_family="solid_liquid_equilibrium",
                allow_estimated=False,
                allow_analogy=False,
                allow_heuristic_fallback=False,
                block_when_missing=True,
                rationale="Crystallization-centric families must not finalize solids design on heuristic SLE fallback alone.",
            )
        )
    else:
        base_rules.append(
            _rule(
                family_adapter,
                stage_id="distillation_design",
                subject="binary_interaction_parameters",
                artifact_family="vle_nonideal_basis",
                allow_estimated=False,
                allow_analogy=False,
                allow_heuristic_fallback=True,
                block_when_missing=False,
                rationale="VLE-heavy families may continue on ideal fallback when BIPs are missing, but the fallback must stay explicit and reviewable.",
            )
        )

    packages = _primary_packages(property_packages)
    product_id = normalize_chemical_name(config.basis.target_product)
    rules: list[SparseDataPolicyRule] = []
    for rule in base_rules:
        if rule.subject in _PACKAGE_SUBJECTS:
            rules.append(_evaluate_package_rule(rule, packages))
        elif rule.subject == "binary_interaction_parameters":
            rules.append(
                _evaluate_pair_rule(
                    rule,
                    property_packages.unresolved_binary_pairs,
                    resolved_count=len(property_packages.binary_interaction_parameters),
                )
            )
        elif rule.subject == "henry_constants":
            rules.append(
                _evaluate_pair_rule(
                    rule,
                    property_packages.unresolved_henry_pairs,
                    resolved_count=len(property_packages.henry_law_constants),
                )
            )
        elif rule.subject == "solubility_curve":
            product_curve_count = len(
                [
                    curve
                    for curve in property_packages.solubility_curves
                    if curve.solute_component_id == product_id
                ]
            )
            product_pair_prefix = f"{product_id}__"
            triggered_pairs = [
                pair_id
                for pair_id in property_packages.unresolved_solubility_pairs
                if pair_id.startswith(product_pair_prefix)
            ]
            if not triggered_pairs and product_curve_count > 0:
                rules.append(rule)
            else:
                rules.append(
                    _evaluate_pair_rule(
                        rule,
                        triggered_pairs or property_packages.unresolved_solubility_pairs,
                        resolved_count=product_curve_count,
                    )
                )
        else:
            rules.append(rule)

    blocked_stage_ids = sorted({rule.stage_id for rule in rules if rule.current_status == "blocked"})
    warning_stage_ids = sorted({rule.stage_id for rule in rules if rule.current_status == "warning"})
    rows = [
        "| Stage | Subject | Artifact Family | Est. | Analogy | Heuristic Fallback | Min Confidence | Status | Triggered Items |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for rule in rules:
        rows.append(
            "| "
            + " | ".join(
                [
                    rule.stage_id,
                    rule.subject,
                    rule.artifact_family,
                    "yes" if rule.allow_estimated else "no",
                    "yes" if rule.allow_analogy else "no",
                    "yes" if rule.allow_heuristic_fallback else "no",
                    f"{rule.minimum_confidence:.2f}",
                    rule.current_status,
                    ", ".join(rule.triggered_items[:3]) or "-",
                ]
            )
            + " |"
        )
    assumptions = family_adapter.assumptions + [
        "Sparse-data policy is generated from the chemistry-family adapter and current property-engine coverage.",
        "Detailed design stages may block even when screening solvers still allow explicit heuristic fallback.",
    ]
    return SparseDataPolicyArtifact(
        policy_id=f"{family_adapter.adapter_id}_sparse_data_policy",
        adapter_id=family_adapter.adapter_id,
        family_label=family_adapter.family_label,
        rules=rules,
        blocked_stage_ids=blocked_stage_ids,
        warning_stage_ids=warning_stage_ids,
        markdown="\n".join(rows),
        citations=sorted(set(family_adapter.citations + property_packages.citations)),
        assumptions=assumptions,
    )
