from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from aoc.models import (
    AlternativeOption,
    DecisionCriterion,
    DecisionRecord,
    PropertyEstimate,
    ProductProfileArtifact,
    ProjectConfig,
    PropertyRecord,
    ProvenanceTag,
    ResearchBundle,
    RouteOption,
    RouteSurveyArtifact,
    ScenarioStability,
    SensitivityLevel,
    SparseDataPolicyArtifact,
)
from aoc.properties.models import (
    BinaryInteractionParameter,
    ChemicalIdentifier,
    HenryLawConstant,
    PropertyCorrelation,
    PropertyMethodDecision,
    PropertyPackage,
    PropertyPackageArtifact,
    PureComponentProperty,
    SolubilityCurve,
)
from aoc.properties.requirements import build_property_requirement_set
from aoc.properties.sources import (
    collect_identifier_specs,
    match_benchmark_entry,
    normalize_chemical_name,
    product_profile_source_index,
    resolve_binary_interaction_entry,
    resolve_henry_entry,
    resolve_solubility_entry,
    technical_anchor_source_ids,
)
from aoc.value_engine import make_value_record


try:
    from thermo import Chemical as _ThermoChemical
except Exception:  # pragma: no cover - optional dependency
    _ThermoChemical = None


PROPERTY_FIELD_MAP = {
    "molecular weight": "molecular_weight",
    "boiling point": "normal_boiling_point",
    "normal boiling point": "normal_boiling_point",
    "melting point": "melting_point",
    "density": "liquid_density",
    "viscosity": "liquid_viscosity",
    "heat capacity": "liquid_heat_capacity",
    "heat_of_vaporization": "heat_of_vaporization",
    "heat of vaporization": "heat_of_vaporization",
    "thermal conductivity": "thermal_conductivity",
}

PROPERTY_LABELS = {
    "molecular_weight": "Molecular weight",
    "normal_boiling_point": "Normal boiling point",
    "melting_point": "Melting point",
    "liquid_density": "Liquid density",
    "liquid_viscosity": "Liquid viscosity",
    "liquid_heat_capacity": "Liquid heat capacity",
    "heat_of_vaporization": "Heat of vaporization",
    "thermal_conductivity": "Thermal conductivity",
}

PROPERTY_SENSITIVITY = {
    "molecular_weight": SensitivityLevel.HIGH,
    "normal_boiling_point": SensitivityLevel.HIGH,
    "melting_point": SensitivityLevel.MEDIUM,
    "liquid_density": SensitivityLevel.HIGH,
    "liquid_viscosity": SensitivityLevel.HIGH,
    "liquid_heat_capacity": SensitivityLevel.HIGH,
    "heat_of_vaporization": SensitivityLevel.HIGH,
    "thermal_conductivity": SensitivityLevel.MEDIUM,
}

PROPERTY_REFERENCE_TEMP_C = {
    "liquid_density": 25.0,
    "liquid_viscosity": 25.0,
    "liquid_heat_capacity": 25.0,
    "heat_of_vaporization": 100.0,
    "thermal_conductivity": 25.0,
}


@dataclass(frozen=True)
class _ResolvedPropertyCandidate:
    value: str
    units: str
    source_ids: list[str]
    provenance_method: ProvenanceTag
    resolution_status: str
    confidence: float
    reference_temperature_c: float | None = None
    reference_pressure_bar: float | None = 1.01325
    notes: str = ""


def _format_numeric(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _profile_property_lookup(product_profile: ProductProfileArtifact) -> dict[str, PropertyRecord]:
    return {normalize_chemical_name(item.name): item for item in product_profile.properties}


def _property_from_profile(
    identifier: ChemicalIdentifier,
    property_field: str,
    product_profile: ProductProfileArtifact,
) -> _ResolvedPropertyCandidate | None:
    if normalize_chemical_name(identifier.canonical_name) != normalize_chemical_name(product_profile.product_name):
        return None
    lookup = _profile_property_lookup(product_profile)
    property_record = lookup.get(property_field) or lookup.get(
        {
            "molecular_weight": "molecular_weight",
            "normal_boiling_point": "boiling_point",
            "melting_point": "melting_point",
            "liquid_density": "density",
            "liquid_viscosity": "viscosity",
            "liquid_heat_capacity": "heat_capacity",
            "heat_of_vaporization": "heat_of_vaporization",
            "thermal_conductivity": "thermal_conductivity",
        }.get(property_field, property_field)
    )
    if property_record is None:
        return None
    return _ResolvedPropertyCandidate(
        value=property_record.value,
        units=property_record.units,
        source_ids=list(dict.fromkeys(property_record.supporting_sources or property_record.citations)),
        provenance_method=property_record.method if property_record.method != ProvenanceTag.CALCULATED else ProvenanceTag.SOURCED,
        resolution_status="resolved",
        confidence=0.96,
        reference_temperature_c=PROPERTY_REFERENCE_TEMP_C.get(property_field),
        notes="Direct cited product-profile property.",
    )


def _property_from_seed(
    identifier: ChemicalIdentifier,
    property_field: str,
    bundle: ResearchBundle,
) -> _ResolvedPropertyCandidate | None:
    _, entry = match_benchmark_entry(identifier.canonical_name, identifier.formula)
    if not entry:
        return None
    properties = entry.get("properties", {})
    if property_field not in properties:
        return None
    value, units = properties[property_field]
    anchor_ids = technical_anchor_source_ids(bundle)
    return _ResolvedPropertyCandidate(
        value=_format_numeric(value),
        units=units,
        source_ids=anchor_ids,
        provenance_method=ProvenanceTag.CALCULATED,
        resolution_status="estimated",
        confidence=0.72 if anchor_ids else 0.55,
        reference_temperature_c=PROPERTY_REFERENCE_TEMP_C.get(property_field),
        notes="Benchmark property seed anchored to public technical source ids.",
    )


def _property_from_library(
    identifier: ChemicalIdentifier,
    property_field: str,
    bundle: ResearchBundle,
) -> _ResolvedPropertyCandidate | None:
    if _ThermoChemical is None:
        return None
    identity_tokens = [identifier.cas_number, identifier.canonical_name, *(identifier.aliases or [])]
    chem = None
    for token in identity_tokens:
        if not token:
            continue
        try:
            chem = _ThermoChemical(token, T=298.15, P=101325.0)
            break
        except Exception:
            continue
    if chem is None:
        return None
    value = None
    units = ""
    try:
        if property_field == "molecular_weight":
            value, units = chem.MW, "g/mol"
        elif property_field == "normal_boiling_point":
            value, units = chem.Tb - 273.15 if chem.Tb else None, "C"
        elif property_field == "melting_point":
            value, units = chem.Tm - 273.15 if chem.Tm else None, "C"
        elif property_field == "liquid_density":
            value, units = getattr(chem, "rhol", None), "kg/m3"
        elif property_field == "liquid_viscosity":
            value, units = getattr(chem, "mul", None), "Pa.s"
        elif property_field == "liquid_heat_capacity":
            cpl = getattr(chem, "Cpl", None)
            value, units = (cpl / 1000.0 if cpl is not None else None), "kJ/kg-K"
        elif property_field == "heat_of_vaporization":
            hvap = getattr(chem, "Hvap", None)
            value, units = (hvap / 1000.0 if hvap is not None else None), "kJ/kg"
        elif property_field == "thermal_conductivity":
            value, units = getattr(chem, "kl", None), "W/m-K"
    except Exception:
        value = None
    if value is None:
        return None
    anchor_ids = technical_anchor_source_ids(bundle)
    return _ResolvedPropertyCandidate(
        value=_format_numeric(value),
        units=units,
        source_ids=anchor_ids,
        provenance_method=ProvenanceTag.CALCULATED,
        resolution_status="estimated",
        confidence=0.68 if anchor_ids else 0.50,
        reference_temperature_c=PROPERTY_REFERENCE_TEMP_C.get(property_field),
        notes="Library-backed calculation anchored to a cited component identity.",
    )


def _property_by_analogy(
    identifier: ChemicalIdentifier,
    property_field: str,
) -> _ResolvedPropertyCandidate | None:
    _, entry = match_benchmark_entry(identifier.canonical_name, identifier.formula)
    if entry:
        return None
    default_units = {
        "molecular_weight": "g/mol",
        "normal_boiling_point": "C",
        "melting_point": "C",
        "liquid_density": "kg/m3",
        "liquid_viscosity": "Pa.s",
        "liquid_heat_capacity": "kJ/kg-K",
        "heat_of_vaporization": "kJ/kg",
        "thermal_conductivity": "W/m-K",
    }
    fallback_values = {
        "molecular_weight": 100.0,
        "normal_boiling_point": 160.0,
        "melting_point": 20.0,
        "liquid_density": 980.0,
        "liquid_viscosity": 0.0022,
        "liquid_heat_capacity": 2.30,
        "heat_of_vaporization": 650.0,
        "thermal_conductivity": 0.18,
    }
    if property_field not in fallback_values:
        return None
    return _ResolvedPropertyCandidate(
        value=_format_numeric(fallback_values[property_field]),
        units=default_units[property_field],
        source_ids=[],
        provenance_method=ProvenanceTag.ANALOGY,
        resolution_status="estimated",
        confidence=0.35,
        reference_temperature_c=PROPERTY_REFERENCE_TEMP_C.get(property_field),
        notes="Analogy fallback used because no direct/public benchmark match was available.",
    )


def _build_identifier(spec: dict[str, object], bundle: ResearchBundle) -> ChemicalIdentifier:
    key, entry = match_benchmark_entry(str(spec["canonical_name"]), spec.get("formula") if isinstance(spec.get("formula"), str) else None)
    cas_number = entry.get("cas_number") if entry else None
    aliases = sorted(set(spec.get("aliases", [])) | set(entry.get("aliases", []) if entry else []))
    route_ids = list(spec.get("route_ids", []))
    source_ids = technical_anchor_source_ids(bundle)
    return ChemicalIdentifier(
        identifier_id=str(spec["identifier_id"]),
        canonical_name=str(spec["canonical_name"]),
        aliases=aliases,
        formula=spec.get("formula") if isinstance(spec.get("formula"), str) else entry.get("formula") if entry else None,
        cas_number=str(cas_number) if cas_number else None,
        route_ids=route_ids,
        source_ids=source_ids,
        resolution_status="resolved" if entry or source_ids else "estimated",
        confidence=0.9 if entry else 0.65 if source_ids else 0.35,
        citations=source_ids,
        assumptions=["Chemical identifier is resolved from route participants, product profile, and benchmark/library matching."],
    )


def _build_property(
    identifier: ChemicalIdentifier,
    property_field: str,
    product_profile: ProductProfileArtifact,
    bundle: ResearchBundle,
) -> PureComponentProperty:
    candidate = _property_from_profile(identifier, property_field, product_profile)
    if candidate is None:
        candidate = _property_from_seed(identifier, property_field, bundle)
    if candidate is None:
        candidate = _property_from_library(identifier, property_field, bundle)
    if candidate is None:
        candidate = _property_by_analogy(identifier, property_field)
    blocking = candidate is None or candidate.provenance_method == ProvenanceTag.ANALOGY and PROPERTY_SENSITIVITY[property_field] == SensitivityLevel.HIGH
    if candidate is None:
        candidate = _ResolvedPropertyCandidate(
            value="n/a",
            units="-",
            source_ids=[],
            provenance_method=ProvenanceTag.ESTIMATED,
            resolution_status="blocked",
            confidence=0.0,
            reference_temperature_c=PROPERTY_REFERENCE_TEMP_C.get(property_field),
            notes="No cited, seeded, library-backed, or analogy value could be resolved.",
        )
    resolution_status = "blocked" if blocking else candidate.resolution_status
    return PureComponentProperty(
        property_id=f"{identifier.identifier_id}_{property_field}",
        identifier_id=identifier.identifier_id,
        property_name=property_field,
        value=candidate.value,
        units=candidate.units,
        reference_temperature_c=candidate.reference_temperature_c,
        reference_pressure_bar=candidate.reference_pressure_bar,
        source_ids=candidate.source_ids,
        provenance_method=candidate.provenance_method,
        blocking=blocking,
        resolution_status=resolution_status,
        confidence=candidate.confidence,
        citations=candidate.source_ids,
        assumptions=[candidate.notes] if candidate.notes else [],
    )


def _build_correlations(identifier: ChemicalIdentifier, bundle: ResearchBundle) -> list[PropertyCorrelation]:
    _, entry = match_benchmark_entry(identifier.canonical_name, identifier.formula)
    if not entry:
        return []
    antoine = entry.get("antoine")
    if not isinstance(antoine, dict):
        return []
    source_ids = technical_anchor_source_ids(bundle)
    correlation = PropertyCorrelation(
        correlation_id=f"{identifier.identifier_id}_antoine",
        identifier_id=identifier.identifier_id,
        property_name="vapor_pressure",
        equation_name="Antoine",
        parameters={key: value for key, value in antoine.items() if key in {"A", "B", "C"}},
        temperature_min_c=float(antoine.get("temperature_min_c")) if antoine.get("temperature_min_c") is not None else None,
        temperature_max_c=float(antoine.get("temperature_max_c")) if antoine.get("temperature_max_c") is not None else None,
        pressure_basis_bar=1.01325,
        source_ids=source_ids,
        provenance_method=ProvenanceTag.CALCULATED if source_ids else ProvenanceTag.ESTIMATED,
        resolution_status="estimated" if source_ids else "blocked",
        confidence=0.70 if source_ids else 0.0,
        citations=source_ids,
        assumptions=["Benchmark Antoine correlation carried for future separation-property work."],
    )
    return [correlation]


def _build_binary_interaction_parameters(
    identifiers: list[ChemicalIdentifier],
    target_identifier_ids: list[str],
    bundle: ResearchBundle,
) -> tuple[list[BinaryInteractionParameter], list[str]]:
    identifier_lookup = {identifier.identifier_id: identifier for identifier in identifiers}
    active_ids = [item for item in target_identifier_ids if item in identifier_lookup]
    parameters: list[BinaryInteractionParameter] = []
    unresolved_pairs: list[str] = []
    for component_a_id, component_b_id in combinations(sorted(set(active_ids)), 2):
        identifier_a = identifier_lookup[component_a_id]
        identifier_b = identifier_lookup[component_b_id]
        resolved = resolve_binary_interaction_entry(
            identifier_a.canonical_name,
            identifier_b.canonical_name,
            bundle,
        )
        pair_id = f"{component_a_id}__{component_b_id}"
        if not resolved:
            unresolved_pairs.append(pair_id)
            continue
        parameters.append(
            BinaryInteractionParameter(
                bip_id=pair_id,
                component_a_id=component_a_id,
                component_b_id=component_b_id,
                component_a_name=identifier_a.canonical_name,
                component_b_name=identifier_b.canonical_name,
                model_name=str(resolved.get("model_name", "NRTL")),
                tau12=float(resolved["tau12"]) if resolved.get("tau12") is not None else None,
                tau21=float(resolved["tau21"]) if resolved.get("tau21") is not None else None,
                alpha12=float(resolved["alpha12"]) if resolved.get("alpha12") is not None else None,
                source_ids=list(dict.fromkeys(resolved.get("source_ids", []))),
                provenance_method=ProvenanceTag.SOURCED if resolved.get("source_ids") else ProvenanceTag.ESTIMATED,
                resolution_status="resolved" if resolved.get("source_ids") else "estimated",
                confidence=0.90 if resolved.get("source_ids") else 0.45,
                notes=[
                    "Binary interaction parameter was resolved from a cited/public source adapter."
                    if resolved.get("source_ids")
                    else "Binary interaction parameter has no cited source id and should not outrank ideal fallback."
                ],
                citations=list(dict.fromkeys(resolved.get("source_ids", []))),
                assumptions=["Binary interaction parameters are directional and stored in the queried component order."],
            )
        )
    return parameters, unresolved_pairs


def _bp_c_from_package(package: PropertyPackage) -> float:
    try:
        return float(package.normal_boiling_point.value) if package.normal_boiling_point is not None else 999.0
    except Exception:
        return 999.0


def _mp_c_from_package(package: PropertyPackage) -> float:
    try:
        return float(package.melting_point.value) if package.melting_point is not None else 0.0
    except Exception:
        return 0.0


def _is_gas_candidate(package: PropertyPackage) -> bool:
    identifier = package.identifier.identifier_id
    return identifier in {"carbon_dioxide", "sulfur_dioxide", "oxygen", "ammonia"} or _bp_c_from_package(package) < 35.0


def _is_solid_candidate(package: PropertyPackage) -> bool:
    bp_text = str(package.normal_boiling_point.value).lower() if package.normal_boiling_point is not None else ""
    return (
        "decompos" in bp_text
        or _mp_c_from_package(package) > 40.0
        or package.identifier.identifier_id in {"sodium_bicarbonate", "soda_ash", "sodium_hydroxide", "sodium_chloride"}
    )


def _is_liquid_solvent_candidate(package: PropertyPackage) -> bool:
    return not _is_gas_candidate(package) and not _is_solid_candidate(package)


def _survey_needs_absorption(route_survey: RouteSurveyArtifact | None) -> bool:
    if route_survey is None:
        return False
    for route in route_survey.routes:
        text = " ".join(route.separations).lower()
        if "absor" in text or "strip" in text or "scrub" in text:
            return True
    return False


def _survey_needs_solids(route_survey: RouteSurveyArtifact | None) -> bool:
    if route_survey is None:
        return False
    for route in route_survey.routes:
        text = " ".join(route.separations).lower()
        if any(token in text for token in ("crystal", "filter", "dry")):
            return True
    return False


def _build_henry_law_constants(
    packages: list[PropertyPackage],
    primary_identifier_ids: list[str],
    route_survey: RouteSurveyArtifact | None,
    bundle: ResearchBundle,
) -> tuple[list[HenryLawConstant], list[str]]:
    if not _survey_needs_absorption(route_survey):
        return [], []
    package_lookup = {package.identifier.identifier_id: package for package in packages if package.identifier.identifier_id in set(primary_identifier_ids)}
    gas_packages = [package for package in package_lookup.values() if _is_gas_candidate(package)]
    solvent_packages = [
        package
        for package in package_lookup.values()
        if package.identifier.identifier_id in {"water", "sulfuric_acid", "spent_acid"} or _is_liquid_solvent_candidate(package)
    ]
    constants: list[HenryLawConstant] = []
    unresolved_pairs: list[str] = []
    for gas_package in gas_packages:
        for solvent_package in solvent_packages:
            if gas_package.identifier.identifier_id == solvent_package.identifier.identifier_id:
                continue
            pair_id = f"{gas_package.identifier.identifier_id}__{solvent_package.identifier.identifier_id}"
            resolved = resolve_henry_entry(gas_package.identifier.canonical_name, solvent_package.identifier.canonical_name, bundle)
            if not resolved:
                unresolved_pairs.append(pair_id)
                continue
            constants.append(
                HenryLawConstant(
                    constant_id=pair_id,
                    gas_component_id=gas_package.identifier.identifier_id,
                    solvent_component_id=solvent_package.identifier.identifier_id,
                    gas_component_name=gas_package.identifier.canonical_name,
                    solvent_component_name=solvent_package.identifier.canonical_name,
                    value=float(resolved["value"]),
                    units=str(resolved.get("units", "bar")),
                    reference_temperature_c=float(resolved["reference_temperature_c"]) if resolved.get("reference_temperature_c") is not None else None,
                    equation_form=str(resolved.get("equation_form", "P=H*x")),
                    source_ids=list(dict.fromkeys(resolved.get("source_ids", []))),
                    provenance_method=ProvenanceTag.SOURCED if resolved.get("source_ids") else ProvenanceTag.ESTIMATED,
                    resolution_status="resolved" if resolved.get("source_ids") else "estimated",
                    confidence=0.90 if resolved.get("source_ids") else 0.45,
                    notes=["Henry-law constant resolved for absorber/stripper equilibrium screening."],
                    citations=list(dict.fromkeys(resolved.get("source_ids", []))),
                    assumptions=["Henry's law uses the dilute-liquid form P = H*x in the current screening implementation."],
                )
            )
    return constants, unresolved_pairs


def _build_solubility_curves(
    packages: list[PropertyPackage],
    primary_identifier_ids: list[str],
    route_survey: RouteSurveyArtifact | None,
    bundle: ResearchBundle,
) -> tuple[list[SolubilityCurve], list[str]]:
    if not _survey_needs_solids(route_survey):
        return [], []
    package_lookup = {package.identifier.identifier_id: package for package in packages if package.identifier.identifier_id in set(primary_identifier_ids)}
    solute_packages = [package for package in package_lookup.values() if _is_solid_candidate(package)]
    solvent_packages = [
        package
        for package in package_lookup.values()
        if package.identifier.identifier_id == "water" or _is_liquid_solvent_candidate(package)
    ]
    curves: list[SolubilityCurve] = []
    unresolved_pairs: list[str] = []
    for solute_package in solute_packages:
        for solvent_package in solvent_packages:
            if solute_package.identifier.identifier_id == solvent_package.identifier.identifier_id:
                continue
            pair_id = f"{solute_package.identifier.identifier_id}__{solvent_package.identifier.identifier_id}"
            resolved = resolve_solubility_entry(solute_package.identifier.canonical_name, solvent_package.identifier.canonical_name, bundle)
            if not resolved:
                unresolved_pairs.append(pair_id)
                continue
            curves.append(
                SolubilityCurve(
                    curve_id=pair_id,
                    solute_component_id=solute_package.identifier.identifier_id,
                    solvent_component_id=solvent_package.identifier.identifier_id,
                    solute_component_name=solute_package.identifier.canonical_name,
                    solvent_component_name=solvent_package.identifier.canonical_name,
                    equation_name=str(resolved.get("equation_name", "linear")),
                    parameters=dict(resolved.get("parameters", {})),
                    temperature_min_c=float(resolved["temperature_min_c"]) if resolved.get("temperature_min_c") is not None else None,
                    temperature_max_c=float(resolved["temperature_max_c"]) if resolved.get("temperature_max_c") is not None else None,
                    units=str(resolved.get("units", "kg_solute_per_kg_solvent")),
                    source_ids=list(dict.fromkeys(resolved.get("source_ids", []))),
                    provenance_method=ProvenanceTag.SOURCED if resolved.get("source_ids") else ProvenanceTag.ESTIMATED,
                    resolution_status="resolved" if resolved.get("source_ids") else "estimated",
                    confidence=0.90 if resolved.get("source_ids") else 0.45,
                    notes=["Solubility curve resolved for crystallization / filtration screening."],
                    citations=list(dict.fromkeys(resolved.get("source_ids", []))),
                    assumptions=["SLE screening currently applies the resolved curve directly to the crystallization temperature basis."],
                )
            )
    return curves, unresolved_pairs


def build_property_package_artifact(
    config: ProjectConfig,
    bundle: ResearchBundle,
    product_profile: ProductProfileArtifact,
    route_survey: RouteSurveyArtifact | None = None,
) -> PropertyPackageArtifact:
    identifier_specs = collect_identifier_specs(product_profile, route_survey)
    identifiers = [_build_identifier(spec, bundle) for spec in identifier_specs]
    primary_route_ids = [route_survey.routes[0].route_id] if route_survey and route_survey.routes else []
    primary_identifier_ids = []
    packages: list[PropertyPackage] = []
    correlations: list[PropertyCorrelation] = []
    unresolved_identifier_ids: list[str] = []
    blocked_property_ids: list[str] = []
    for identifier in identifiers:
        package_correlations = _build_correlations(identifier, bundle)
        correlations.extend(package_correlations)
        package = PropertyPackage(
            package_id=f"{identifier.identifier_id}_package",
            identifier=identifier,
            molecular_weight=_build_property(identifier, "molecular_weight", product_profile, bundle),
            normal_boiling_point=_build_property(identifier, "normal_boiling_point", product_profile, bundle),
            melting_point=_build_property(identifier, "melting_point", product_profile, bundle),
            liquid_density=_build_property(identifier, "liquid_density", product_profile, bundle),
            liquid_viscosity=_build_property(identifier, "liquid_viscosity", product_profile, bundle),
            liquid_heat_capacity=_build_property(identifier, "liquid_heat_capacity", product_profile, bundle),
            heat_of_vaporization=_build_property(identifier, "heat_of_vaporization", product_profile, bundle),
            thermal_conductivity=_build_property(identifier, "thermal_conductivity", product_profile, bundle),
            vapor_pressure_correlation=package_correlations[0] if package_correlations else None,
            antoine_correlation=package_correlations[0] if package_correlations else None,
            citations=identifier.citations,
            assumptions=identifier.assumptions,
        )
        package.blocked_properties = [
            field
            for field in (
                "molecular_weight",
                "normal_boiling_point",
                "melting_point",
                "liquid_density",
                "liquid_viscosity",
                "liquid_heat_capacity",
                "heat_of_vaporization",
                "thermal_conductivity",
            )
            if getattr(package, field) is not None and getattr(package, field).blocking
        ]
        package.notes = [
            "Property package combines direct cited values, benchmark seeds, optional library calculations, and analogy fallback in that order."
        ]
        if package.blocked_properties:
            package.resolution_status = "blocked"
            blocked_property_ids.extend(f"{identifier.identifier_id}_{field}" for field in package.blocked_properties)
        elif any(
            getattr(package, field) is not None and getattr(package, field).resolution_status == "estimated"
            for field in (
                "molecular_weight",
                "normal_boiling_point",
                "melting_point",
                "liquid_density",
                "liquid_viscosity",
                "liquid_heat_capacity",
                "heat_of_vaporization",
                "thermal_conductivity",
            )
        ):
            package.resolution_status = "estimated"
        else:
            package.resolution_status = "resolved"
        if package.resolution_status == "blocked":
            unresolved_identifier_ids.append(identifier.identifier_id)
        packages.append(package)
        if not primary_route_ids or not identifier.route_ids or any(route_id in primary_route_ids for route_id in identifier.route_ids) or identifier.identifier_id == normalize_chemical_name(product_profile.product_name):
            primary_identifier_ids.append(identifier.identifier_id)
    binary_interaction_parameters, unresolved_binary_pairs = _build_binary_interaction_parameters(
        identifiers,
        sorted(set(primary_identifier_ids)),
        bundle,
    )
    henry_law_constants, unresolved_henry_pairs = _build_henry_law_constants(
        packages,
        sorted(set(primary_identifier_ids)),
        route_survey,
        bundle,
    )
    solubility_curves, unresolved_solubility_pairs = _build_solubility_curves(
        packages,
        sorted(set(primary_identifier_ids)),
        route_survey,
        bundle,
    )
    rows = [
        "| Identifier | CAS | Status | Blocked Properties | Primary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for package in packages:
        rows.append(
            f"| {package.identifier.canonical_name} | {package.identifier.cas_number or '-'} | {package.resolution_status} | {', '.join(package.blocked_properties) or '-'} | {'yes' if package.identifier.identifier_id in primary_identifier_ids else 'no'} |"
        )
    return PropertyPackageArtifact(
        identifiers=identifiers,
        packages=packages,
        primary_route_ids=primary_route_ids,
        primary_identifier_ids=sorted(set(primary_identifier_ids)),
        unresolved_identifier_ids=sorted(set(unresolved_identifier_ids)),
        blocked_property_ids=sorted(set(blocked_property_ids)),
        correlations=correlations,
        binary_interaction_parameters=binary_interaction_parameters,
        unresolved_binary_pairs=sorted(set(unresolved_binary_pairs)),
        henry_law_constants=henry_law_constants,
        unresolved_henry_pairs=sorted(set(unresolved_henry_pairs)),
        solubility_curves=solubility_curves,
        unresolved_solubility_pairs=sorted(set(unresolved_solubility_pairs)),
        markdown="\n".join(rows),
        citations=sorted(
            {
                source_id
                for package in packages
                for source_id in package.identifier.source_ids
            }
            | {
                source_id
                for bip in binary_interaction_parameters
                for source_id in bip.source_ids
            }
            | {
                source_id
                for constant in henry_law_constants
                for source_id in constant.source_ids
            }
            | {
                source_id
                for curve in solubility_curves
                for source_id in curve.source_ids
            }
        ),
        assumptions=[
            "Property Engine v1 uses cited product-profile values first, then benchmark public seeds, then optional library-backed calculations, then analogy, then block.",
            "Library-backed values are treated as estimated unless a cited source also anchors the property basis.",
            "Binary interaction parameters are only used when a cited/public source adapter resolves the specific pair; otherwise the solver falls back to ideal gamma=1.0.",
            "Henry-law constants and solubility curves are only used when the property engine resolves a cited/public basis for the active pair; otherwise separators fall back to heuristic splits with explicit warnings.",
        ],
    )


def property_value_records(property_packages: PropertyPackageArtifact) -> list:
    value_records = []
    for package in property_packages.packages:
        for field in (
            "molecular_weight",
            "normal_boiling_point",
            "melting_point",
            "liquid_density",
            "liquid_viscosity",
            "liquid_heat_capacity",
            "heat_of_vaporization",
            "thermal_conductivity",
        ):
            prop = getattr(package, field)
            if prop is None:
                continue
            value_records.append(
                make_value_record(
                    f"{package.identifier.identifier_id}_{field}",
                    f"{package.identifier.canonical_name} {PROPERTY_LABELS[field]}",
                    prop.value,
                    prop.units,
                    provenance_method=prop.provenance_method,
                    source_ids=prop.source_ids,
                    citations=prop.citations,
                    assumptions=prop.assumptions,
                    uncertainty_band="tight" if prop.resolution_status == "resolved" else "review",
                    sensitivity=PROPERTY_SENSITIVITY[field],
                    blocking=prop.blocking,
                )
            )
    return value_records


def property_estimates_from_packages(property_packages: PropertyPackageArtifact) -> list[PropertyEstimate]:
    estimates: list[PropertyEstimate] = []
    identifier_lookup = {
        item.identifier_id: item.canonical_name
        for item in property_packages.identifiers
    }
    for pair_id in property_packages.unresolved_binary_pairs:
        component_a_id, component_b_id = pair_id.split("__", 1)
        estimates.append(
            PropertyEstimate(
                estimate_id=f"{pair_id}_bip_estimate",
                property_name=f"Binary interaction parameters for {identifier_lookup.get(component_a_id, component_a_id)} / {identifier_lookup.get(component_b_id, component_b_id)}",
                selected_method=ProvenanceTag.ESTIMATED,
                candidate_methods=[
                    ProvenanceTag.SOURCED,
                    ProvenanceTag.CALCULATED,
                    ProvenanceTag.ESTIMATED,
                ],
                selected_source_id=None,
                sensitivity=SensitivityLevel.HIGH,
                blocking=False,
                rationale="No cited binary interaction parameter could be resolved for this pair; non-ideal VLE falls back to ideal gamma=1.0 until a public BIP is supplied.",
                assumptions=["Ideal modified-Raoult fallback is used when binary interaction parameters are unresolved."],
            )
        )
    for pair_id in property_packages.unresolved_henry_pairs:
        gas_id, solvent_id = pair_id.split("__", 1)
        estimates.append(
            PropertyEstimate(
                estimate_id=f"{pair_id}_henry_estimate",
                property_name=f"Henry's law constant for {identifier_lookup.get(gas_id, gas_id)} in {identifier_lookup.get(solvent_id, solvent_id)}",
                selected_method=ProvenanceTag.ESTIMATED,
                candidate_methods=[
                    ProvenanceTag.SOURCED,
                    ProvenanceTag.CALCULATED,
                    ProvenanceTag.ESTIMATED,
                ],
                selected_source_id=None,
                sensitivity=SensitivityLevel.HIGH,
                blocking=False,
                rationale="No cited Henry's-law constant could be resolved for this gas/liquid pair; absorber and stripper models fall back to heuristic/ideal partitioning.",
                assumptions=["Gas-liquid equilibrium falls back to heuristic partitioning when Henry's-law data is unresolved."],
            )
        )
    for pair_id in property_packages.unresolved_solubility_pairs:
        solute_id, solvent_id = pair_id.split("__", 1)
        estimates.append(
            PropertyEstimate(
                estimate_id=f"{pair_id}_solubility_estimate",
                property_name=f"Solubility curve for {identifier_lookup.get(solute_id, solute_id)} in {identifier_lookup.get(solvent_id, solvent_id)}",
                selected_method=ProvenanceTag.ESTIMATED,
                candidate_methods=[
                    ProvenanceTag.SOURCED,
                    ProvenanceTag.CALCULATED,
                    ProvenanceTag.ESTIMATED,
                ],
                selected_source_id=None,
                sensitivity=SensitivityLevel.HIGH,
                blocking=False,
                rationale="No cited solubility curve could be resolved for this solid/liquid pair; crystallization and filtration fall back to heuristic split logic.",
                assumptions=["Solid-liquid equilibrium falls back to heuristic crystallization yields when solubility data is unresolved."],
            )
        )
    return estimates


def active_identifier_ids_for_route(
    property_packages: PropertyPackageArtifact,
    route: RouteOption | None,
    product_name: str | None = None,
) -> list[str]:
    if route is None:
        return list(property_packages.primary_identifier_ids)
    active = {
        normalize_chemical_name(participant.name)
        for participant in route.participants
    }
    if product_name:
        active.add(normalize_chemical_name(product_name))
    return [
        package.identifier.identifier_id
        for package in property_packages.packages
        if package.identifier.identifier_id in active
    ]


def build_property_method_decision(
    route: RouteOption,
    property_packages: PropertyPackageArtifact,
) -> PropertyMethodDecision:
    active_ids = set(active_identifier_ids_for_route(property_packages, route))
    relevant_packages = [package for package in property_packages.packages if package.identifier.identifier_id in active_ids]
    direct_count = 0
    estimated_count = 0
    blocked_count = 0
    for package in relevant_packages:
        for field in (
            "molecular_weight",
            "normal_boiling_point",
            "melting_point",
            "liquid_density",
            "liquid_viscosity",
            "liquid_heat_capacity",
            "heat_of_vaporization",
            "thermal_conductivity",
        ):
            prop = getattr(package, field)
            if prop is None:
                blocked_count += 1
            elif prop.blocking or prop.resolution_status == "blocked":
                blocked_count += 1
            elif prop.provenance_method in {ProvenanceTag.SOURCED, ProvenanceTag.USER_SUPPLIED}:
                direct_count += 1
            else:
                estimated_count += 1
    alternatives = [
        AlternativeOption(
            candidate_id="direct_public_package",
            candidate_type="property_basis",
            description="Use directly cited public component properties as the primary basis.",
            total_score=round(direct_count * 4.0 - blocked_count * 10.0, 2),
            feasible=blocked_count == 0 and direct_count >= max(4, estimated_count),
            rejected_reasons=["Property coverage still depends materially on estimated values."] if direct_count < estimated_count else [],
            citations=property_packages.citations,
            assumptions=property_packages.assumptions,
        ),
        AlternativeOption(
            candidate_id="hybrid_cited_plus_library",
            candidate_type="property_basis",
            description="Use cited public anchors with library-backed calculation and benchmark seeds for missing constants.",
            total_score=round(direct_count * 3.0 + estimated_count * 2.5 - blocked_count * 12.0, 2),
            feasible=blocked_count == 0,
            citations=property_packages.citations,
            assumptions=property_packages.assumptions,
        ),
        AlternativeOption(
            candidate_id="estimation_dominant",
            candidate_type="property_basis",
            description="Use estimation-heavy property basis with conservative assumptions.",
            total_score=round(estimated_count * 2.0 - blocked_count * 6.0, 2),
            feasible=blocked_count <= 1,
            citations=property_packages.citations,
            assumptions=property_packages.assumptions,
        ),
        AlternativeOption(
            candidate_id="analogy_basis",
            candidate_type="property_basis",
            description="Use close-compound analogy as a provisional property basis.",
            total_score=round(max(10.0 - blocked_count * 4.0, 0.0), 2),
            feasible=True,
            citations=property_packages.citations,
            assumptions=property_packages.assumptions,
        ),
    ]
    feasible = [item for item in alternatives if item.feasible]
    selected = max(feasible, key=lambda item: item.total_score) if feasible else alternatives[-1]
    decision = DecisionRecord(
        decision_id="property_method_decision",
        context=f"Property-basis selection for route {route.route_id}.",
        criteria=[
            DecisionCriterion(name="Direct coverage", weight=0.45, justification="Prefer directly cited constants where available."),
            DecisionCriterion(name="Completeness", weight=0.35, justification="Required property coverage must be complete before detailed design."),
            DecisionCriterion(name="Auditability", weight=0.20, justification="Library-backed calculations must remain secondary to cited public data."),
        ],
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected for the active component set of route {route.route_id}.",
        hard_constraint_results=["High-sensitivity blocked properties are not allowed to pass into detailed design."],
        confidence=0.88 if selected.candidate_id == "direct_public_package" else 0.80 if selected.candidate_id == "hybrid_cited_plus_library" else 0.56,
        scenario_stability=ScenarioStability.STABLE if blocked_count == 0 else ScenarioStability.BORDERLINE,
        approval_required=blocked_count > 0 or selected.candidate_id in {"estimation_dominant", "analogy_basis"},
        blocked_value_ids=sorted(property_packages.blocked_property_ids),
        citations=property_packages.citations,
        assumptions=property_packages.assumptions,
    )
    rows = [
        "| Property Basis | Feasible | Score |",
        "| --- | --- | --- |",
    ]
    for item in alternatives:
        rows.append(f"| {item.candidate_id} | {'yes' if item.feasible else 'no'} | {item.total_score:.2f} |")
    return PropertyMethodDecision(
        decision=decision,
        selected_property_package_ids=[package.package_id for package in relevant_packages],
        blocked_requirement_ids=sorted(property_packages.blocked_property_ids),
        markdown="\n".join(rows),
        citations=property_packages.citations,
        assumptions=property_packages.assumptions + ["Property-method decision is scored from direct coverage, completeness, and auditability."],
    )


def build_property_requirement_artifact(
    config: ProjectConfig,
    property_packages: PropertyPackageArtifact,
    sparse_policy: SparseDataPolicyArtifact | None = None,
):
    return build_property_requirement_set(config, property_packages, sparse_policy)
