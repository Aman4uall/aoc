from __future__ import annotations

import math

from aoc.models import StreamTable
from aoc.properties.engine import active_identifier_ids_for_route
from aoc.properties.models import MixturePropertyArtifact, MixturePropertyPackage, PropertyPackageArtifact


def _float_value(raw: str | float | int | None) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (float, int)):
        return float(raw)
    try:
        return float(str(raw))
    except ValueError:
        return None


def _package_index(property_packages: PropertyPackageArtifact):
    index: dict[str, object] = {}
    for package in property_packages.packages:
        index[package.identifier.identifier_id] = package
        index[package.identifier.canonical_name.lower()] = package
        for alias in package.identifier.aliases:
            index[alias.lower()] = package
    return index


def _surrogate_property(component_name: str, property_name: str, dominant_phase: str) -> float | None:
    lowered = component_name.lower()
    if property_name == "liquid_heat_capacity":
        if dominant_phase == "gas":
            return 1.1
        if dominant_phase == "solid":
            return 1.0
        return 2.3
    if property_name == "liquid_density":
        if dominant_phase == "gas":
            return 1.3
        if dominant_phase == "solid":
            return 1600.0
        return 980.0
    if property_name == "liquid_viscosity":
        if dominant_phase == "gas":
            return 1.8e-5
        if dominant_phase == "solid":
            return 0.0045
        return 0.0022
    if property_name == "heat_of_vaporization":
        if dominant_phase == "solid":
            return 0.0
        if any(token in lowered for token in {"water", "glycol"}):
            return 1500.0
        return 500.0
    if property_name == "thermal_conductivity":
        if dominant_phase == "gas":
            return 0.025
        if dominant_phase == "solid":
            return 0.35
        return 0.18
    return None


def _component_property(package, property_name: str, dominant_phase: str, component_name: str) -> tuple[float | None, bool]:
    prop = getattr(package, property_name, None) if package is not None else None
    if prop is None:
        return _surrogate_property(component_name, property_name, dominant_phase), True
    value = _float_value(prop.value)
    if value is None:
        return _surrogate_property(component_name, property_name, dominant_phase), True
    units = str(getattr(prop, "units", "") or "").strip().lower()
    if property_name == "liquid_density" and units in {"g/cm3", "g/cc", "g/ml"}:
        value *= 1000.0
    return value, prop.resolution_status != "resolved"


def _harmonic_density(values: list[tuple[float, float]]) -> float | None:
    denominator = 0.0
    for fraction, density in values:
        if density <= 1e-9:
            continue
        denominator += fraction / density
    if denominator <= 1e-12:
        return None
    return 1.0 / denominator


def _log_viscosity(values: list[tuple[float, float]]) -> float | None:
    accumulator = 0.0
    fraction_sum = 0.0
    for fraction, viscosity in values:
        if viscosity <= 1e-12:
            continue
        accumulator += fraction * math.log(viscosity)
        fraction_sum += fraction
    if fraction_sum <= 1e-12:
        return None
    return math.exp(accumulator / fraction_sum)


def build_mixture_property_artifact(
    stream_table: StreamTable,
    property_packages: PropertyPackageArtifact,
) -> MixturePropertyArtifact:
    package_index = _package_index(property_packages)
    packages: list[MixturePropertyPackage] = []
    blocked_unit_ids: list[str] = []

    for state in stream_table.composition_states:
        fractions = state.outlet_component_mass_fraction or state.inlet_component_mass_fraction
        dominant_phase = state.dominant_outlet_phase or state.dominant_inlet_phase or "liquid"
        component_package_ids: dict[str, str] = {}
        cp_terms: list[tuple[float, float]] = []
        density_terms: list[tuple[float, float]] = []
        viscosity_terms: list[tuple[float, float]] = []
        hvap_terms: list[tuple[float, float]] = []
        conductivity_terms: list[tuple[float, float]] = []
        estimated_properties: set[str] = set()
        blocking_properties: set[str] = set()
        notes: list[str] = []

        for component_name, fraction in fractions.items():
            lookup_key = component_name.lower()
            package = package_index.get(lookup_key)
            if package is None:
                normalized = component_name.lower().replace("-", " ").replace("/", " ").strip()
                package = package_index.get(normalized)
            if package is not None:
                component_package_ids[component_name] = package.package_id
            cp_value, cp_estimated = _component_property(package, "liquid_heat_capacity", dominant_phase, component_name)
            density_value, density_estimated = _component_property(package, "liquid_density", dominant_phase, component_name)
            viscosity_value, viscosity_estimated = _component_property(package, "liquid_viscosity", dominant_phase, component_name)
            hvap_value, hvap_estimated = _component_property(package, "heat_of_vaporization", dominant_phase, component_name)
            conductivity_value, conductivity_estimated = _component_property(package, "thermal_conductivity", dominant_phase, component_name)
            if cp_value is not None:
                cp_terms.append((fraction, cp_value))
            else:
                blocking_properties.add("liquid_heat_capacity")
            if density_value is not None:
                density_terms.append((fraction, density_value))
            else:
                blocking_properties.add("liquid_density")
            if viscosity_value is not None:
                viscosity_terms.append((fraction, viscosity_value))
            else:
                blocking_properties.add("liquid_viscosity")
            if hvap_value is not None:
                hvap_terms.append((fraction, hvap_value))
            else:
                blocking_properties.add("heat_of_vaporization")
            if conductivity_value is not None:
                conductivity_terms.append((fraction, conductivity_value))
            if cp_estimated:
                estimated_properties.add("liquid_heat_capacity")
            if density_estimated:
                estimated_properties.add("liquid_density")
            if viscosity_estimated:
                estimated_properties.add("liquid_viscosity")
            if hvap_estimated:
                estimated_properties.add("heat_of_vaporization")
            if conductivity_estimated:
                estimated_properties.add("thermal_conductivity")
            if package is None:
                notes.append(f"{component_name} uses a surrogate property estimate because no dedicated component package is available.")

        cp = sum(fraction * value for fraction, value in cp_terms) if cp_terms else None
        density = _harmonic_density(density_terms)
        viscosity = _log_viscosity(viscosity_terms)
        hvap = sum(fraction * value for fraction, value in hvap_terms) if hvap_terms else None
        conductivity = sum(fraction * value for fraction, value in conductivity_terms) if conductivity_terms else None
        resolution_status = "resolved"
        if blocking_properties:
            resolution_status = "blocked"
            blocked_unit_ids.append(state.unit_id)
        elif estimated_properties:
            resolution_status = "estimated"
        packages.append(
            MixturePropertyPackage(
                mixture_id=f"{state.unit_id}_mixture_properties",
                unit_id=state.unit_id,
                state_id=state.state_id,
                dominant_phase=dominant_phase,
                component_mass_fraction=fractions,
                component_package_ids=component_package_ids,
                liquid_heat_capacity_kj_kg_k=round(cp, 6) if cp is not None else None,
                liquid_density_kg_m3=round(density, 6) if density is not None else None,
                liquid_viscosity_pa_s=round(viscosity, 8) if viscosity is not None else None,
                heat_of_vaporization_kj_kg=round(hvap, 6) if hvap is not None else None,
                thermal_conductivity_w_m_k=round(conductivity, 6) if conductivity is not None else None,
                resolution_status=resolution_status,
                estimated_properties=sorted(estimated_properties),
                blocking_properties=sorted(blocking_properties),
                notes=notes,
                citations=sorted({source_id for package_id in component_package_ids.values() for source_id in property_packages.citations}),
                assumptions=property_packages.assumptions + ["Mixture properties are built from mass-fraction weighting and simple density/viscosity mixing rules in Property Engine v1."],
            )
        )
    lines = [
        "| Unit | Dominant Phase | Cp (kJ/kg-K) | Density (kg/m3) | Viscosity (Pa.s) | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for package in packages:
        lines.append(
            f"| {package.unit_id} | {package.dominant_phase or '-'} | {package.liquid_heat_capacity_kj_kg_k if package.liquid_heat_capacity_kj_kg_k is not None else '-'} | {package.liquid_density_kg_m3 if package.liquid_density_kg_m3 is not None else '-'} | {package.liquid_viscosity_pa_s if package.liquid_viscosity_pa_s is not None else '-'} | {package.resolution_status} |"
        )
    return MixturePropertyArtifact(
        packages=packages,
        blocked_unit_ids=sorted(set(blocked_unit_ids)),
        markdown="\n".join(lines),
        citations=property_packages.citations,
        assumptions=property_packages.assumptions,
    )


def mixture_property_for_unit(
    mixture_artifact: MixturePropertyArtifact | None,
    *,
    unit_ids: tuple[str, ...] = (),
    state_ids: tuple[str, ...] = (),
) -> MixturePropertyPackage | None:
    if mixture_artifact is None:
        return None
    for package in mixture_artifact.packages:
        if unit_ids and package.unit_id in unit_ids:
            return package
        if state_ids and package.state_id in state_ids:
            return package
    return None
