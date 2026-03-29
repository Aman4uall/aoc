from __future__ import annotations

from aoc.models import (
    ChemistryFamilyAdapter,
    ProcessArchetype,
    RouteFamilyArtifact,
    RouteOption,
    UnitOperationFamilyArtifact,
    UnitOperationFamilyCandidate,
)
from aoc.route_families import build_route_family_artifact, profile_for_route


def _candidate(
    candidate_id: str,
    service_group: str,
    family_label: str,
    description: str,
    score: float,
    status: str,
    rationale: str,
    critic_flags: list[str],
    citations: list[str],
    assumptions: list[str],
) -> UnitOperationFamilyCandidate:
    return UnitOperationFamilyCandidate(
        candidate_id=candidate_id,
        service_group=service_group,
        family_label=family_label,
        description=description,
        applicability_score=score,
        applicability_status=status,
        rationale=rationale,
        critic_flags=critic_flags,
        citations=citations,
        assumptions=assumptions,
    )


def _markdown(artifact: UnitOperationFamilyArtifact) -> str:
    rows = [
        "| Service Group | Candidate | Status | Score | Rationale |",
        "| --- | --- | --- | --- | --- |",
    ]
    for candidate in [*artifact.reactor_candidates, *artifact.separation_candidates]:
        rows.append(
            f"| {candidate.service_group} | {candidate.candidate_id} | {candidate.applicability_status} | {candidate.applicability_score:.1f} | {candidate.description} |"
        )
    support = ", ".join(artifact.supporting_unit_operations) or "none"
    critics = ", ".join(artifact.applicability_critics) or "none"
    return (
        f"Route `{artifact.route_id}` is expanded into the `{artifact.route_family_label}` unit-operation family.\n\n"
        + "\n".join(rows)
        + f"\n\n- Supporting unit operations: {support}\n"
        + f"- Applicability critics: {critics}"
    )


def build_unit_operation_family_artifact(
    route: RouteOption,
    archetype: ProcessArchetype | None,
    adapter: ChemistryFamilyAdapter | None = None,
    route_families: RouteFamilyArtifact | None = None,
) -> UnitOperationFamilyArtifact:
    route_families = route_families or build_route_family_artifact(
        type("RouteSurveyShim", (), {"routes": [route], "markdown": "", "citations": route.citations, "assumptions": route.assumptions})()
    )
    profile = profile_for_route(route_families, route.route_id)
    if profile is None:
        raise ValueError(f"Missing route-family profile for route '{route.route_id}'.")

    citations = list(dict.fromkeys([*route.citations, *(adapter.citations if adapter else []), *profile.citations]))
    assumptions = list(dict.fromkeys([*route.assumptions, *(adapter.assumptions if adapter else []), *profile.assumptions]))
    reactor_candidates: list[UnitOperationFamilyCandidate] = []
    separation_candidates: list[UnitOperationFamilyCandidate] = []
    supporting_unit_operations: list[str] = []
    applicability_critics = list(profile.critic_flags)

    family_id = profile.route_family_id
    family_label = profile.family_label

    if family_id == "liquid_hydration_train":
        reactor_candidates = [
            _candidate("tubular_plug_flow_hydrator", "reactor", family_label, "Tubular hydrator with strong dehydration integration fit", 96.0, "preferred", "Hydration trains favor plug-flow hydrator geometry and steady exotherm management.", applicability_critics, citations, assumptions),
            _candidate("jacketed_cstr_train", "reactor", family_label, "CSTR fallback for liquid hydration service", 72.0, "fallback", "Agitated trains remain a fallback when plug-flow precedent is weak.", applicability_critics, citations, assumptions),
            _candidate("high_pressure_carbonylation_loop", "reactor", family_label, "High-pressure carbonylation loop", 18.0, "blocked", "Carbonylation loops do not match hydration-family chemistry.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("distillation_train", "separation", family_label, "Flash and glycol distillation train", 94.0, "preferred", "Hydration purification remains distillation-led with strong water-removal burden.", applicability_critics, citations, assumptions),
            _candidate("extractive_distillation_train", "separation", family_label, "Extractive/vacuum polishing distillation", 82.0, "fallback", "Extractive polishing can support difficult finishing service.", applicability_critics, citations, assumptions),
            _candidate("packed_absorption_train", "separation", family_label, "Packed absorption train", 20.0, "blocked", "Absorption-led trains are not the primary purification basis for this family.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = ["flash", "dehydration_column", "glycol_polishing_column", "heat_exchanger_cluster"]
    elif family_id in {"gas_absorption_converter_train", "regeneration_loop_train"}:
        reactor_candidates = [
            _candidate("fixed_bed_converter", "reactor", family_label, "Fixed-bed catalytic converter", 95.0, "preferred", "Gas conversion service favors packed catalytic converter hardware.", applicability_critics, citations, assumptions),
            _candidate("trickle_bed_oxidizer", "reactor", family_label, "Trickle-bed or oxidation converter fallback", 80.0, "fallback", "Oxidative or mixed gas-liquid converter service can use trickle-bed style hardware.", applicability_critics, citations, assumptions),
            _candidate("slurry_carboxylation_reactor", "reactor", family_label, "Slurry carboxylation reactor", 16.0, "blocked", "Slurry carbonation hardware does not fit gas absorption/converter service.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("packed_absorption_train", "separation", family_label, "Packed absorption and drying train", 96.0, "preferred", "Gas cleanup in this family is absorber-led and mass-transfer limited.", applicability_critics, citations, assumptions),
            _candidate("gas_drying_absorption_train", "separation", family_label, "Gas drying plus absorber polishing train", 90.0, "fallback", "Drying and polishing often sit beside the main absorber service.", applicability_critics, citations, assumptions),
            _candidate("distillation_train", "separation", family_label, "Distillation train", 26.0, "blocked", "Distillation is secondary to gas-liquid absorption in this family.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = ["converter", "absorber", "stripper", "mist_eliminator", "acid_cooler"]
    elif family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"}:
        reactor_candidates = [
            _candidate("slurry_carboxylation_reactor", "reactor", family_label, "Slurry carbonation or carboxylation reactor", 95.0, "preferred", "Solids families require slurry-compatible reaction service.", applicability_critics, citations, assumptions),
            _candidate("slurry_loop_reactor", "reactor", family_label, "Slurry loop reactor", 90.0, "fallback", "Looped slurry service remains a credible alternative for solids suspension and heat removal.", applicability_critics, citations, assumptions),
            _candidate("fixed_bed_converter", "reactor", family_label, "Fixed-bed converter", 18.0, "blocked", "Packed converter hardware conflicts with slurry solids service.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("crystallizer_classifier_dryer_train", "separation", family_label, "Crystallizer, classifier, filter, and dryer train", 97.0, "preferred", "The product train is explicitly solids-handling and should retain classifier/filter/dryer basis.", applicability_critics, citations, assumptions),
            _candidate("crystallization_filtration_drying", "separation", family_label, "Crystallization, filtration, and drying train", 92.0, "fallback", "Simplified solids train remains acceptable when classifier detail is light.", applicability_critics, citations, assumptions),
            _candidate("solvent_extraction_recovery_train", "separation", family_label, "Solvent extraction train", 20.0, "blocked", "Solvent extraction is not the primary solids purification basis here.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = ["crystallizer", "classifier", "pressure_filter", "dryer", "silo"]
    elif family_id == "oxidation_recovery_train":
        reactor_candidates = [
            _candidate("trickle_bed_oxidizer", "reactor", family_label, "Trickle-bed or oxidation reactor train", 94.0, "preferred", "Oxidation service benefits from dedicated oxygen-transfer or catalytic oxidation hardware.", applicability_critics, citations, assumptions),
            _candidate("fixed_bed_converter", "reactor", family_label, "Fixed-bed converter", 86.0, "fallback", "Packed converter service remains acceptable for oxidation trains with strong gas handling.", applicability_critics, citations, assumptions),
            _candidate("slurry_carboxylation_reactor", "reactor", family_label, "Slurry carboxylation reactor", 14.0, "blocked", "Slurry carboxylation is not aligned with oxidation-family service.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("distillation_train", "separation", family_label, "Recovery distillation train", 84.0, "preferred", "Oxidation recovery often closes through distillation-led purification.", applicability_critics, citations, assumptions),
            _candidate("packed_absorption_train", "separation", family_label, "Absorption-led offgas cleanup", 82.0, "fallback", "Offgas cleanup can justify absorber-led finishing for oxidation trains.", applicability_critics, citations, assumptions),
            _candidate("crystallizer_classifier_dryer_train", "separation", family_label, "Solids train", 18.0, "blocked", "Solids train is not primary for oxidation-recovery service.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = ["oxidizer", "quench", "offgas_absorber", "recovery_column"]
    elif family_id in {"carbonylation_liquid_train", "extraction_recovery_train"}:
        reactor_candidates = [
            _candidate("high_pressure_carbonylation_loop", "reactor", family_label, "High-pressure carbonylation or liquid-loop reactor", 95.0 if family_id == "carbonylation_liquid_train" else 72.0, "preferred" if family_id == "carbonylation_liquid_train" else "fallback", "High-pressure loop service matches carbonylation-heavy liquid families.", applicability_critics, citations, assumptions),
            _candidate("jacketed_cstr_train", "reactor", family_label, "Jacketed CSTR train", 90.0 if family_id == "extraction_recovery_train" else 76.0, "preferred" if family_id == "extraction_recovery_train" else "fallback", "Agitated liquid service remains practical for extraction-intensive trains.", applicability_critics, citations, assumptions),
            _candidate("tubular_plug_flow_hydrator", "reactor", family_label, "Tubular hydrator", 22.0, "blocked", "Hydrator hardware does not align with carbonylation/extraction families.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("solvent_extraction_recovery_train", "separation", family_label, "Solvent extraction and recovery train", 95.0 if family_id == "extraction_recovery_train" else 70.0, "preferred" if family_id == "extraction_recovery_train" else "fallback", "Extraction families need extractor plus solvent recovery basis.", applicability_critics, citations, assumptions),
            _candidate("extractive_distillation_train", "separation", family_label, "Extractive or specialty distillation train", 90.0 if family_id == "carbonylation_liquid_train" else 84.0, "preferred" if family_id == "carbonylation_liquid_train" else "fallback", "Difficult liquid splits justify specialty distillation or extractive polishing.", applicability_critics, citations, assumptions),
            _candidate("packed_absorption_train", "separation", family_label, "Packed absorption train", 24.0, "blocked", "Absorption-led separation is not the primary liquid purification basis here.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = ["extractor", "recovery_column", "light_ends_column", "solvent_polishing"]
    else:
        reactor_candidates = [
            _candidate("jacketed_cstr_train", "reactor", family_label, "Jacketed CSTR train", 82.0, "preferred", "Generic mixed service defaults to agitated liquid reactor service.", applicability_critics, citations, assumptions),
            _candidate("fixed_bed_converter", "reactor", family_label, "Fixed-bed converter", 66.0, "fallback", "Packed-bed service remains a fallback when gas conversion is credible.", applicability_critics, citations, assumptions),
        ]
        separation_candidates = [
            _candidate("distillation_train", "separation", family_label, "Distillation train", 82.0, "preferred", "Mixed service defaults to general distillation-led purification.", applicability_critics, citations, assumptions),
            _candidate("solvent_extraction_recovery_train", "separation", family_label, "Extraction and recovery train", 76.0, "fallback", "Extraction remains a fallback for mixed difficult splits.", applicability_critics, citations, assumptions),
        ]
        supporting_unit_operations = list(adapter.common_unit_operations[:4]) if adapter else ["reactor", "flash", "column", "exchanger"]

    if adapter:
        for candidate in reactor_candidates:
            if candidate.candidate_id in adapter.preferred_reactor_candidates:
                candidate.applicability_score = round(candidate.applicability_score + 6.0, 3)
                if candidate.applicability_status != "blocked":
                    candidate.applicability_status = "preferred"
        for candidate in separation_candidates:
            if candidate.candidate_id in adapter.preferred_separation_candidates:
                candidate.applicability_score = round(candidate.applicability_score + 6.0, 3)
                if candidate.applicability_status != "blocked":
                    candidate.applicability_status = "preferred"
        supporting_unit_operations = list(dict.fromkeys([*supporting_unit_operations, *adapter.common_unit_operations[:4]]))
        applicability_critics = list(dict.fromkeys([*applicability_critics, *adapter.critic_focus[:3]]))

    artifact = UnitOperationFamilyArtifact(
        route_id=route.route_id,
        route_family_id=profile.route_family_id,
        route_family_label=profile.family_label,
        dominant_phase_pattern=profile.dominant_phase_pattern,
        reactor_candidates=reactor_candidates,
        separation_candidates=separation_candidates,
        supporting_unit_operations=supporting_unit_operations,
        applicability_critics=applicability_critics,
        citations=citations,
        assumptions=assumptions + ["Unit-operation family expansion is derived from the selected route family, chemistry-family adapter, and archetype."],
    )
    artifact.markdown = _markdown(artifact)
    return artifact
