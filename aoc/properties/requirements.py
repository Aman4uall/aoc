from __future__ import annotations

from aoc.models import ProjectConfig, SensitivityLevel
from aoc.properties.models import (
    PropertyPackageArtifact,
    PropertyRequirement,
    PropertyRequirementCoverage,
    PropertyRequirementSet,
)


_DEFAULT_STAGE_REQUIREMENTS: dict[str, list[tuple[str, bool, bool, str]]] = {
    "thermodynamic_feasibility": [
        ("molecular_weight", True, False, "Pure-component identity and thermodynamic screening require molecular weight or a defensible estimated anchor."),
        ("normal_boiling_point", True, False, "Boiling point anchors thermodynamic feasibility and later separation screening."),
        ("melting_point", True, False, "Melting point anchors solids/liquid feasibility and handling risk."),
    ],
    "energy_balance": [
        ("liquid_heat_capacity", True, False, "Energy balance requires heat-capacity data or a defensible estimate."),
        ("heat_of_vaporization", True, False, "Latent-duty handling requires vaporization enthalpy or a defensible estimate."),
        ("liquid_density", True, False, "Density is required for flow-to-duty conversion and later equipment sizing."),
    ],
    "reactor_design": [
        ("liquid_density", True, False, "Reactor hydraulic sizing requires density."),
        ("liquid_viscosity", True, False, "Reactor Reynolds/Nusselt basis requires viscosity."),
        ("liquid_heat_capacity", True, False, "Reactor thermal design requires heat capacity."),
        ("thermal_conductivity", True, True, "Thermal conductivity improves heat-transfer estimates when available."),
    ],
    "distillation_design": [
        ("liquid_density", True, False, "Process-unit hydraulics require density."),
        ("liquid_viscosity", True, False, "Process-unit hydraulics require viscosity."),
        ("liquid_heat_capacity", True, False, "Thermal design requires heat capacity."),
    ],
    "mechanical_design_moc": [
        ("liquid_density", True, False, "Mechanical screening requires density and reference phase awareness."),
    ],
}


def build_property_requirement_set(
    config: ProjectConfig,
    property_packages: PropertyPackageArtifact,
) -> PropertyRequirementSet:
    requirements: list[PropertyRequirement] = []
    coverage: list[PropertyRequirementCoverage] = []
    blocked_requirement_ids: list[str] = []
    blocked_stage_ids: set[str] = set()
    identifier_ids = [identifier.identifier_id for identifier in property_packages.identifiers]
    package_index = {package.identifier.identifier_id: package for package in property_packages.packages}

    for stage_id, entries in _DEFAULT_STAGE_REQUIREMENTS.items():
        for property_name, allow_estimated, optional, note in entries:
            requirement = PropertyRequirement(
                requirement_id=f"{stage_id}_{property_name}",
                stage_id=stage_id,
                unit_family=stage_id,
                property_name=property_name,
                allow_estimated=allow_estimated,
                optional=optional,
                sensitivity=SensitivityLevel.HIGH if not optional else SensitivityLevel.MEDIUM,
                blocking=not optional,
                notes=note,
                citations=property_packages.citations,
                assumptions=property_packages.assumptions,
            )
            requirements.append(requirement)
            for identifier_id in sorted(identifier_ids):
                package = package_index.get(identifier_id)
                prop = getattr(package, property_name, None) if package is not None else None
                if prop is None:
                    status = "missing"
                    sources: list[str] = []
                    notes = "No property package entry exists for this requirement."
                elif prop.blocking or prop.resolution_status == "blocked":
                    status = "blocked"
                    sources = prop.source_ids
                    notes = "Property is explicitly blocked in the property package."
                elif prop.resolution_status == "estimated":
                    status = "estimated"
                    sources = prop.source_ids
                    notes = "Property is available only as an estimated/library-backed value."
                else:
                    status = "covered"
                    sources = prop.source_ids
                    notes = "Property is covered by a resolved package entry."
                coverage.append(
                    PropertyRequirementCoverage(
                        coverage_id=f"{stage_id}_{identifier_id}_{property_name}",
                        stage_id=stage_id,
                        identifier_id=identifier_id,
                        property_name=property_name,
                        status=status,
                        allow_estimated=allow_estimated,
                        blocking=not optional,
                        source_ids=sources,
                        notes=notes,
                        citations=sources,
                        assumptions=property_packages.assumptions,
                    )
                )
                if status in {"blocked", "missing"} or (status == "estimated" and not allow_estimated):
                    if not optional:
                        blocked_requirement_ids.append(requirement.requirement_id)
                        blocked_stage_ids.add(stage_id)

    rows = [
        ["Stage", "Identifier", "Property", "Status", "Allow Estimated", "Blocking"],
    ]
    for item in coverage:
        rows.append(
            [
                item.stage_id,
                item.identifier_id,
                item.property_name,
                item.status,
                "yes" if item.allow_estimated else "no",
                "yes" if item.blocking else "no",
            ]
        )
    markdown_lines = [
        "| Stage | Identifier | Property | Status | Allow Estimated | Blocking |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[1:]:
        markdown_lines.append("| " + " | ".join(row) + " |")
    return PropertyRequirementSet(
        requirements=requirements,
        coverage=coverage,
        blocked_requirement_ids=sorted(set(blocked_requirement_ids)),
        blocked_stage_ids=sorted(blocked_stage_ids),
        markdown="\n".join(markdown_lines),
        citations=property_packages.citations,
        assumptions=property_packages.assumptions + ["Property requirement coverage is evaluated against the primary route/product identifier set."],
    )


def requirement_failures_for_stage(
    requirement_set: PropertyRequirementSet,
    stage_id: str,
    active_identifier_ids: list[str],
) -> list[PropertyRequirementCoverage]:
    active_set = set(active_identifier_ids)
    failures: list[PropertyRequirementCoverage] = []
    for item in requirement_set.coverage:
        if item.stage_id != stage_id:
            continue
        if active_set and item.identifier_id not in active_set:
            continue
        if item.status in {"blocked", "missing"} or (item.status == "estimated" and not item.allow_estimated):
            failures.append(item)
    return failures
