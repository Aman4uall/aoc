from __future__ import annotations

import math
import re

from aoc.models import RouteOption
from aoc.properties.activity_models import activity_coefficients_binary
from aoc.properties.models import (
    BinaryInteractionParameter,
    ComponentKValue,
    PropertyPackage,
    PropertyPackageArtifact,
    RelativeVolatilityEstimate,
    SeparationThermoArtifact,
)
from aoc.properties.sources import normalize_chemical_name


def _float_value(prop) -> float | None:
    if prop is None:
        return None
    try:
        return float(prop.value)
    except Exception:
        match = re.search(r"-?\d+(?:\.\d+)?", str(prop.value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except Exception:
            return None


def _text_value(prop) -> str:
    if prop is None:
        return ""
    return str(prop.value).strip().lower()


def _bp_c(package: PropertyPackage) -> float:
    value = _float_value(package.normal_boiling_point)
    return value if value is not None else 999.0


def _mw_g_mol(package: PropertyPackage) -> float | None:
    return _float_value(package.molecular_weight)


def _hvap_kj_kg(package: PropertyPackage) -> float | None:
    return _float_value(package.heat_of_vaporization)


def _pair_id(component_a_id: str, component_b_id: str) -> str:
    pair = sorted((component_a_id, component_b_id))
    return f"{pair[0]}__{pair[1]}"


def _reoriented_bip(
    bip: BinaryInteractionParameter,
    component_a_id: str,
    component_b_id: str,
) -> BinaryInteractionParameter:
    if bip.component_a_id == component_a_id and bip.component_b_id == component_b_id:
        return bip
    return BinaryInteractionParameter(
        bip_id=bip.bip_id,
        component_a_id=component_a_id,
        component_b_id=component_b_id,
        component_a_name=bip.component_b_name,
        component_b_name=bip.component_a_name,
        model_name=bip.model_name,
        tau12=bip.tau21,
        tau21=bip.tau12,
        alpha12=bip.alpha12,
        source_ids=bip.source_ids,
        provenance_method=bip.provenance_method,
        resolution_status=bip.resolution_status,
        confidence=bip.confidence,
        notes=bip.notes,
        citations=bip.citations,
        assumptions=bip.assumptions,
    )


def _find_pair_bip(
    property_packages: PropertyPackageArtifact,
    component_a_id: str,
    component_b_id: str,
) -> BinaryInteractionParameter | None:
    pair_id = _pair_id(component_a_id, component_b_id)
    bip = next(
        (
            item
            for item in property_packages.binary_interaction_parameters
            if item.bip_id == pair_id
        ),
        None,
    )
    if bip is None:
        return None
    return _reoriented_bip(bip, component_a_id, component_b_id)


def _vapor_pressure_from_antoine(package: PropertyPackage, temperature_c: float) -> tuple[float | None, str]:
    correlation = package.antoine_correlation or package.vapor_pressure_correlation
    if correlation is None or correlation.equation_name.lower() != "antoine":
        return None, ""
    try:
        a = float(correlation.parameters["A"])
        b = float(correlation.parameters["B"])
        c = float(correlation.parameters["C"])
    except Exception:
        return None, ""
    pressure_mm_hg = 10 ** (a - (b / max(temperature_c + c, 1e-6)))
    pressure_bar = pressure_mm_hg * 1.01325 / 760.0
    in_range = True
    if correlation.temperature_min_c is not None and temperature_c < correlation.temperature_min_c:
        in_range = False
    if correlation.temperature_max_c is not None and temperature_c > correlation.temperature_max_c:
        in_range = False
    method = "antoine" if in_range else "antoine_extrapolated"
    return max(pressure_bar, 1e-6), method


def _vapor_pressure_from_clapeyron(package: PropertyPackage, temperature_c: float) -> tuple[float | None, str]:
    tb_c = _bp_c(package)
    hvap_kj_kg = _hvap_kj_kg(package)
    mw = _mw_g_mol(package)
    if hvap_kj_kg is None or mw is None or tb_c >= 900.0:
        return None, ""
    hvap_j_mol = hvap_kj_kg * mw
    t_ref_k = tb_c + 273.15
    t_k = temperature_c + 273.15
    if t_ref_k <= 0.0 or t_k <= 0.0:
        return None, ""
    exponent = -hvap_j_mol / 8.314 * ((1.0 / t_k) - (1.0 / t_ref_k))
    pressure_bar = 1.01325 * math.exp(max(min(exponent, 18.0), -18.0))
    return max(pressure_bar, 1e-6), "clausius_clapeyron"


def _vapor_pressure_from_bp_proxy(package: PropertyPackage, temperature_c: float) -> tuple[float | None, str]:
    tb_c = _bp_c(package)
    if tb_c >= 900.0:
        return None, ""
    t_k = temperature_c + 273.15
    tb_k = tb_c + 273.15
    pressure_bar = 1.01325 * math.exp(max(min(10.0 * (1.0 - tb_k / max(t_k, 1.0)), 12.0), -12.0))
    return max(pressure_bar, 1e-6), "boiling_point_proxy"


def _vapor_pressure_nonvolatile(package: PropertyPackage, temperature_c: float) -> tuple[float | None, str]:
    del temperature_c
    bp_text = _text_value(package.normal_boiling_point)
    mp_c = _float_value(package.melting_point)
    hvap_kj_kg = _hvap_kj_kg(package)
    if "decompos" in bp_text or (_bp_c(package) >= 900.0 and ((mp_c is not None and mp_c > 40.0) or hvap_kj_kg == 0.0)):
        return 1e-9, "nonvolatile_solid"
    return None, ""


def component_k_value(
    package: PropertyPackage,
    temperature_c: float,
    pressure_bar: float,
    activity_coefficient: float = 1.0,
    activity_model: str = "ideal_raoult",
) -> tuple[float, float, float, str, str]:
    for evaluator in (
        _vapor_pressure_from_antoine,
        _vapor_pressure_from_clapeyron,
        _vapor_pressure_from_bp_proxy,
        _vapor_pressure_nonvolatile,
    ):
        vapor_pressure_bar, vapor_method = evaluator(package, temperature_c)
        if vapor_pressure_bar is None:
            continue
        gamma = max(activity_coefficient, 1e-6)
        k_value = max(gamma * vapor_pressure_bar / max(pressure_bar, 1e-6), 1e-9)
        if activity_model == "nrtl_modified_raoult":
            method = f"modified_raoult_nrtl_{vapor_method}"
            resolution_status = "resolved" if vapor_method == "antoine" else "estimated"
        elif activity_model == "ideal_raoult_missing_bip_fallback":
            method = f"ideal_raoult_missing_bip_{vapor_method}"
            resolution_status = "estimated"
        else:
            method = f"ideal_raoult_{vapor_method}"
            resolution_status = "resolved" if vapor_method == "antoine" else "estimated"
        return k_value, vapor_pressure_bar, gamma, method, resolution_status
    return 0.0, 0.0, max(activity_coefficient, 1e-6), "blocked", "blocked"


def _active_route_packages(
    property_packages: PropertyPackageArtifact,
    route: RouteOption,
    target_product: str,
) -> list[PropertyPackage]:
    active_names = {normalize_chemical_name(participant.name) for participant in route.participants}
    active_names.add(normalize_chemical_name(target_product))
    packages = [
        package
        for package in property_packages.packages
        if package.identifier.identifier_id in active_names
    ]
    return packages or property_packages.packages


def _separation_family(selected_candidate_id: str | None) -> str:
    value = (selected_candidate_id or "").lower()
    if "absorption" in value or "stripping" in value:
        return "absorption"
    if "extraction" in value:
        return "extraction"
    if "crystall" in value or "filtration" in value or "drying" in value:
        return "solids"
    return "distillation"


def _select_key_packages(
    route: RouteOption,
    property_packages: PropertyPackageArtifact,
    target_product: str,
    selected_candidate_id: str | None = None,
) -> tuple[PropertyPackage, PropertyPackage, list[PropertyPackage], str]:
    packages = _active_route_packages(property_packages, route, target_product)
    family = _separation_family(selected_candidate_id)
    target_id = normalize_chemical_name(target_product)
    product_package = next((package for package in packages if package.identifier.identifier_id == target_id), None)
    if product_package is not None:
        bp_text = _text_value(product_package.normal_boiling_point)
        mp_c = _float_value(product_package.melting_point)
        if "decompos" in bp_text or (mp_c is not None and mp_c > 40.0):
            family = "solids"
    package_ids = {package.identifier.identifier_id for package in packages}
    if {"sulfur_dioxide", "sulfuric_acid"} <= package_ids:
        family = "absorption"
    sorted_by_bp = sorted(packages, key=_bp_c)
    if product_package is not None:
        heavy = product_package
    else:
        heavy = max(sorted_by_bp, key=_bp_c)
    others = [package for package in sorted_by_bp if package.package_id != heavy.package_id]
    preferred_others = [
        package
        for package in others
        if _bp_c(package) >= 25.0 and _bp_c(package) <= max(_bp_c(heavy) - 5.0, 25.0)
    ]
    water_like = [
        package
        for package in preferred_others
        if normalize_chemical_name(package.identifier.canonical_name) == "water"
    ]
    if water_like:
        light = water_like[0]
    else:
        light = (preferred_others[0] if preferred_others else others[0]) if others else heavy
    if family == "absorption" and len(sorted_by_bp) >= 2:
        light = sorted_by_bp[0]
        heavy = sorted_by_bp[-1]
    return light, heavy, packages, family


def _temperature_window(route: RouteOption, light_bp_c: float, heavy_bp_c: float, family: str) -> tuple[float, float, float]:
    if family == "distillation":
        pressure_bar = min(max(route.operating_pressure_bar * 0.18, 1.2), 4.0)
        top_temp_c = max(min(light_bp_c + 8.0, route.operating_temperature_c * 0.78), 20.0)
        bottom_temp_c = max(min(heavy_bp_c + 6.0, route.operating_temperature_c + 12.0), top_temp_c + 18.0)
    elif family == "absorption":
        pressure_bar = min(max(route.operating_pressure_bar * 0.55, 1.5), 18.0)
        top_temp_c = max(min(light_bp_c + 5.0, route.operating_temperature_c * 0.45), 20.0)
        bottom_temp_c = max(min(heavy_bp_c * 0.7, route.operating_temperature_c * 0.65), top_temp_c + 12.0)
    elif family == "extraction":
        pressure_bar = min(max(route.operating_pressure_bar * 0.28, 1.1), 6.0)
        top_temp_c = max(min(light_bp_c + 10.0, route.operating_temperature_c * 0.65), 25.0)
        bottom_temp_c = max(min(heavy_bp_c + 4.0, route.operating_temperature_c * 0.85), top_temp_c + 15.0)
    else:
        pressure_bar = max(route.operating_pressure_bar * 0.12, 1.0)
        top_temp_c = max(min(light_bp_c + 6.0, route.operating_temperature_c * 0.55), 20.0)
        bottom_temp_c = max(min(heavy_bp_c + 2.0, route.operating_temperature_c * 0.70), top_temp_c + 8.0)
    return pressure_bar, top_temp_c, bottom_temp_c


def _key_pair_activity_basis(
    light: PropertyPackage,
    heavy: PropertyPackage,
    property_packages: PropertyPackageArtifact,
) -> tuple[BinaryInteractionParameter | None, str, list[str]]:
    bip = _find_pair_bip(property_packages, light.identifier.identifier_id, heavy.identifier.identifier_id)
    if bip is None or bip.resolution_status != "resolved":
        return None, "ideal_raoult_missing_bip_fallback", [
            f"Binary interaction parameters for {light.identifier.canonical_name} / {heavy.identifier.canonical_name} were not resolved from cited/public sources.",
            "Activity coefficients defaulted to gamma=1.0 and the separation basis fell back to ideal Raoult's law for the key pair.",
        ]
    return bip, "nrtl_modified_raoult", []


def _key_pair_activity_coefficients(
    light: PropertyPackage,
    heavy: PropertyPackage,
    property_packages: PropertyPackageArtifact,
) -> tuple[dict[str, float], BinaryInteractionParameter | None, str, list[str]]:
    bip, activity_model, fallback_notes = _key_pair_activity_basis(light, heavy, property_packages)
    if bip is None:
        return {
            light.identifier.identifier_id: 1.0,
            heavy.identifier.identifier_id: 1.0,
        }, None, activity_model, fallback_notes
    gamma_light, gamma_heavy = activity_coefficients_binary(bip.model_name, 0.5, bip)
    return {
        light.identifier.identifier_id: gamma_light,
        heavy.identifier.identifier_id: gamma_heavy,
    }, bip, activity_model, []


def build_separation_thermo_artifact(
    route: RouteOption,
    property_packages: PropertyPackageArtifact,
    target_product: str,
    selected_candidate_id: str | None = None,
) -> SeparationThermoArtifact:
    light, heavy, packages, family = _select_key_packages(route, property_packages, target_product, selected_candidate_id)
    pressure_bar, top_temp_c, bottom_temp_c = _temperature_window(route, _bp_c(light), _bp_c(heavy), family)
    top_k_values: list[ComponentKValue] = []
    bottom_k_values: list[ComponentKValue] = []
    blocked_ids: list[str] = []
    method_notes: list[str] = []
    fallback_notes: list[str] = []
    key_pair_gamma, pair_bip, activity_model, pair_fallback_notes = _key_pair_activity_coefficients(light, heavy, property_packages)
    fallback_notes.extend(pair_fallback_notes)
    used_bips = [pair_bip] if pair_bip is not None else []
    missing_binary_pairs = [] if pair_bip is not None else [_pair_id(light.identifier.identifier_id, heavy.identifier.identifier_id)]
    for package in packages:
        gamma = key_pair_gamma.get(package.identifier.identifier_id, 1.0)
        package_activity_model = activity_model if package.identifier.identifier_id in key_pair_gamma else "ideal_raoult"
        top_k, top_pvap, top_gamma, top_method, top_status = component_k_value(
            package,
            top_temp_c,
            pressure_bar,
            activity_coefficient=gamma,
            activity_model=package_activity_model,
        )
        bottom_k, bottom_pvap, bottom_gamma, bottom_method, bottom_status = component_k_value(
            package,
            bottom_temp_c,
            pressure_bar,
            activity_coefficient=gamma,
            activity_model=package_activity_model,
        )
        combined_citations = package.citations + (package.antoine_correlation.citations if package.antoine_correlation else [])
        if pair_bip is not None and package.identifier.identifier_id in key_pair_gamma:
            combined_citations = combined_citations + pair_bip.citations
        top_k_values.append(
            ComponentKValue(
                estimate_id=f"{package.identifier.identifier_id}_top_k",
                identifier_id=package.identifier.identifier_id,
                component_name=package.identifier.canonical_name,
                temperature_c=round(top_temp_c, 3),
                pressure_bar=round(pressure_bar, 3),
                vapor_pressure_bar=round(top_pvap, 6),
                activity_coefficient=round(top_gamma, 6),
                k_value=round(top_k, 6),
                method=top_method,
                activity_model=package_activity_model,
                binary_pair_id=pair_bip.bip_id if pair_bip is not None and package.identifier.identifier_id in key_pair_gamma else None,
                resolution_status=top_status,
                citations=sorted(set(combined_citations)),
                assumptions=package.assumptions + (pair_bip.assumptions if pair_bip is not None and package.identifier.identifier_id in key_pair_gamma else []),
            )
        )
        bottom_k_values.append(
            ComponentKValue(
                estimate_id=f"{package.identifier.identifier_id}_bottom_k",
                identifier_id=package.identifier.identifier_id,
                component_name=package.identifier.canonical_name,
                temperature_c=round(bottom_temp_c, 3),
                pressure_bar=round(pressure_bar, 3),
                vapor_pressure_bar=round(bottom_pvap, 6),
                activity_coefficient=round(bottom_gamma, 6),
                k_value=round(bottom_k, 6),
                method=bottom_method,
                activity_model=package_activity_model,
                binary_pair_id=pair_bip.bip_id if pair_bip is not None and package.identifier.identifier_id in key_pair_gamma else None,
                resolution_status=bottom_status,
                citations=sorted(set(combined_citations)),
                assumptions=package.assumptions + (pair_bip.assumptions if pair_bip is not None and package.identifier.identifier_id in key_pair_gamma else []),
            )
        )
        if top_status == "blocked" or bottom_status == "blocked":
            blocked_ids.append(package.identifier.identifier_id)
    top_lookup = {item.identifier_id: item for item in top_k_values}
    bottom_lookup = {item.identifier_id: item for item in bottom_k_values}
    top_alpha = max(
        top_lookup.get(
            light.identifier.identifier_id,
            ComponentKValue(estimate_id="na", identifier_id="na", component_name="na", temperature_c=0, pressure_bar=0),
        ).k_value,
        1e-9,
    ) / max(
        top_lookup.get(
            heavy.identifier.identifier_id,
            ComponentKValue(estimate_id="na", identifier_id="na", component_name="na", temperature_c=0, pressure_bar=0),
        ).k_value,
        1e-9,
    )
    bottom_alpha = max(
        bottom_lookup.get(
            light.identifier.identifier_id,
            ComponentKValue(estimate_id="na", identifier_id="na", component_name="na", temperature_c=0, pressure_bar=0),
        ).k_value,
        1e-9,
    ) / max(
        bottom_lookup.get(
            heavy.identifier.identifier_id,
            ComponentKValue(estimate_id="na", identifier_id="na", component_name="na", temperature_c=0, pressure_bar=0),
        ).k_value,
        1e-9,
    )
    if family in {"distillation", "absorption"} and top_alpha < 1.0 and bottom_alpha < 1.0:
        light, heavy = heavy, light
        top_alpha = 1.0 / max(top_alpha, 1e-9)
        bottom_alpha = 1.0 / max(bottom_alpha, 1e-9)
        method_notes.append("Key orientation auto-corrected so the more volatile component is treated as the light key for separation screening.")
    feasible = (
        light.identifier.identifier_id not in blocked_ids
        and heavy.identifier.identifier_id not in blocked_ids
        and top_alpha > 1.0
        and bottom_alpha > 1.0
    )
    method_notes.append(f"Top alpha from K-values at {top_temp_c:.1f} C and {pressure_bar:.2f} bar.")
    method_notes.append(f"Bottom alpha from K-values at {bottom_temp_c:.1f} C and {pressure_bar:.2f} bar.")
    if pair_bip is not None:
        method_notes.append(
            f"Key-pair activity coefficients use {pair_bip.model_name} with cited binary interaction parameters for {light.identifier.canonical_name} / {heavy.identifier.canonical_name}."
        )
    else:
        method_notes.extend(fallback_notes)
    relative_volatility = RelativeVolatilityEstimate(
        estimate_id=f"{route.route_id}_relative_volatility",
        light_key_identifier_id=light.identifier.identifier_id,
        heavy_key_identifier_id=heavy.identifier.identifier_id,
        light_key=light.identifier.canonical_name,
        heavy_key=heavy.identifier.canonical_name,
        top_alpha=round(top_alpha, 6),
        bottom_alpha=round(bottom_alpha, 6),
        average_alpha=round(math.sqrt(max(top_alpha, 1e-9) * max(bottom_alpha, 1e-9)), 6),
        method="modified_raoult_nrtl" if pair_bip is not None else "ideal_raoult_missing_bip_fallback",
        feasible=feasible,
        notes=method_notes,
        citations=sorted(
            {
                source_id
                for item in top_k_values + bottom_k_values
                for source_id in item.citations
            }
        ),
        assumptions=[
            "Non-ideal separation thermodynamics uses modified Raoult's law when cited binary interaction parameters are available.",
            "Key-pair activity coefficients are evaluated with an equimolar liquid-phase screening basis in v1 of the non-ideal engine.",
            "When cited binary interaction parameters are unavailable, gamma defaults to 1.0 and the basis falls back to ideal Raoult's law.",
        ],
    )
    rows = [
        "| Component | Ttop (C) | Gamma top | Ktop | Method | Tbottom (C) | Gamma bottom | Kbottom | Method |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for top_item in top_k_values:
        bottom_item = bottom_lookup[top_item.identifier_id]
        rows.append(
            f"| {top_item.component_name} | {top_item.temperature_c:.1f} | {top_item.activity_coefficient:.4f} | {top_item.k_value:.4f} | {top_item.method} | "
            f"{bottom_item.temperature_c:.1f} | {bottom_item.activity_coefficient:.4f} | {bottom_item.k_value:.4f} | {bottom_item.method} |"
        )
    rows.extend(
        [
            "",
            f"Light key: `{light.identifier.canonical_name}`",
            f"Heavy key: `{heavy.identifier.canonical_name}`",
            f"Activity model: `{activity_model}`",
            f"Average relative volatility: `{relative_volatility.average_alpha:.4f}`",
            f"System pressure: `{pressure_bar:.3f}` bar",
        ]
    )
    if fallback_notes:
        rows.extend(["", "Fallback notes:"] + [f"- {note}" for note in fallback_notes])
    return SeparationThermoArtifact(
        artifact_id=f"{route.route_id}_separation_thermo",
        route_id=route.route_id,
        separation_family=family,
        system_pressure_bar=round(pressure_bar, 3),
        nominal_top_temp_c=round(top_temp_c, 3),
        nominal_bottom_temp_c=round(bottom_temp_c, 3),
        light_key=light.identifier.canonical_name,
        heavy_key=heavy.identifier.canonical_name,
        activity_model=activity_model,
        top_k_values=top_k_values,
        bottom_k_values=bottom_k_values,
        binary_interaction_parameters=used_bips,
        missing_binary_pairs=missing_binary_pairs,
        fallback_notes=fallback_notes,
        relative_volatility=relative_volatility,
        blocked_component_ids=sorted(set(blocked_ids)),
        markdown="\n".join(rows),
        citations=sorted(
            {
                source_id
                for item in top_k_values + bottom_k_values
                for source_id in item.citations
            }
        ),
        assumptions=relative_volatility.assumptions,
    )
