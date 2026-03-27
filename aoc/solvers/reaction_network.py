from __future__ import annotations

from aoc.models import (
    ByproductClosure,
    ByproductEstimate,
    ReactionExtent,
    ReactionExtentSet,
    RouteOption,
)


def _separation_family(route: RouteOption) -> str:
    text = " ".join(route.separations).lower()
    if any(token in text for token in {"distillation", "flash", "evaporation", "fractionation"}):
        return "distillation"
    if any(token in text for token in {"absorption", "stripper", "scrubber"}):
        return "absorption"
    if any(token in text for token in {"crystallization", "filtration", "drying"}):
        return "solids"
    if any(token in text for token in {"extraction", "solvent"}):
        return "extraction"
    return "generic"


def _family_surrogates(route: RouteOption) -> list[str]:
    family = _separation_family(route)
    if family == "solids":
        return ["Mother liquor losses"]
    if family == "absorption":
        return ["Offgas losses"]
    if family == "extraction":
        return ["Extract heavy ends"]
    if route.byproducts:
        return list(route.byproducts)
    return ["Heavy ends"]


def _estimate_component_profile(name: str, product_mw: float, family: str) -> tuple[float, str]:
    lowered = name.lower()
    if any(token in lowered for token in {"mist", "offgas", "gas", "vent"}):
        return max(product_mw * 0.7, 18.0), "gas"
    if any(token in lowered for token in {"salt", "solids", "ash", "cake"}):
        return max(product_mw * 1.1, 40.0), "solid"
    if any(token in lowered for token in {"mother liquor", "saline"}):
        return max(product_mw * 0.95, 30.0), "liquid"
    if "heavy" in lowered:
        return max(product_mw * 1.6, 40.0), "liquid"
    if "chlorinated" in lowered:
        return max(product_mw * 1.3, 35.0), "liquid"
    if family == "solids":
        return max(product_mw * 1.05, 30.0), "solid"
    return max(product_mw * 1.1, 20.0), "liquid"


def build_reaction_network(route: RouteOption, selectivity_fraction: float) -> tuple[ReactionExtentSet, ByproductClosure]:
    bounded_selectivity = max(0.0, min(selectivity_fraction, 1.0))
    selectivity_gap = max(1.0 - bounded_selectivity, 0.0)
    products = [item for item in route.participants if item.role == "product"]
    product_mw = products[0].molecular_weight_g_mol if products else 100.0
    family = _separation_family(route)
    explicit_byproducts = [item for item in route.participants if item.role == "byproduct"]
    declared_byproducts = [item for item in route.byproducts if item]

    extents: list[ReactionExtent] = [
        ReactionExtent(
            extent_id=f"{route.route_id}_main_extent",
            reaction_label=route.reaction_equation,
            kind="main",
            representative_component=products[0].name if products else route.name,
            representative_formula=products[0].formula if products else None,
            representative_molecular_weight_g_mol=product_mw,
            representative_phase=products[0].phase or "" if products else "",
            extent_fraction_of_converted_feed=round(bounded_selectivity, 6),
            status="converged",
            notes=["Main-reaction extent equals selected product selectivity basis."],
            citations=route.citations,
            assumptions=route.assumptions,
        )
    ]

    closure = ByproductClosure(
        route_id=route.route_id,
        declared_byproducts=declared_byproducts,
        explicit_byproduct_components=[item.name for item in explicit_byproducts],
        selectivity_gap_fraction=round(selectivity_gap, 6),
        citations=route.citations,
        assumptions=route.assumptions,
    )

    if selectivity_gap <= 1e-9:
        extent_set = ReactionExtentSet(
            route_id=route.route_id,
            extents=extents,
            closure_status="converged",
            notes=["No side-reaction allocation required at unity selectivity."],
            citations=route.citations,
            assumptions=route.assumptions,
        )
        closure.closure_status = "converged"
        closure.notes.append("No byproduct closure required because the selected selectivity leaves no byproduct gap.")
        return extent_set, closure

    estimates: list[ByproductEstimate] = []
    unresolved: list[str] = []
    closure_notes: list[str] = []
    if explicit_byproducts:
        total_weight = sum(max(item.coefficient, 0.0) for item in explicit_byproducts) or float(len(explicit_byproducts))
        for index, item in enumerate(explicit_byproducts, start=1):
            fraction = max(item.coefficient, 0.0) / total_weight
            status = "converged" if len(explicit_byproducts) >= max(len(declared_byproducts), 1) else "estimated"
            estimates.append(
                ByproductEstimate(
                    estimate_id=f"{route.route_id}_byproduct_{index}",
                    component_name=item.name,
                    formula=item.formula,
                    molecular_weight_g_mol=item.molecular_weight_g_mol,
                    phase=item.phase or "",
                    allocation_fraction=round(fraction, 6),
                    basis="Explicit route participant list",
                    provenance="explicit_participant",
                    status=status,
                    notes=["Allocation fraction normalized from explicit byproduct stoichiometric coefficients."],
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        closure_notes.append("Byproduct closure is anchored on explicit byproduct components declared in the route definition.")
    else:
        declared_names = declared_byproducts or _family_surrogates(route)
        fraction = 1.0 / max(len(declared_names), 1)
        provenance = "declared_trace" if declared_byproducts else "family_surrogate"
        basis = "Declared route byproducts" if declared_byproducts else f"{family.title()} family surrogate"
        for index, name in enumerate(declared_names, start=1):
            mw, phase = _estimate_component_profile(name, product_mw, family)
            estimates.append(
                ByproductEstimate(
                    estimate_id=f"{route.route_id}_byproduct_{index}",
                    component_name=name,
                    formula=None,
                    molecular_weight_g_mol=round(mw, 3),
                    phase=phase,
                    allocation_fraction=round(fraction, 6),
                    basis=basis,
                    provenance=provenance,
                    status="estimated",
                    notes=["Allocation fraction distributed evenly because no explicit byproduct stoichiometry is available."],
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        if not declared_byproducts and selectivity_gap > 0.08:
            unresolved.append("Unspecified side-reaction products")
            closure_notes.append("Family-surrogate byproduct closure is too weak for the current selectivity gap and requires analyst review.")
        elif declared_byproducts and selectivity_gap > 0.20:
            unresolved.extend(declared_byproducts)
            closure_notes.append("Declared byproducts are insufficiently specific for the current selectivity gap and require analyst review.")
        else:
            closure_notes.append(f"Byproduct closure uses {provenance.replace('_', ' ')} allocation because no explicit byproduct stoichiometry is available.")

    estimate_fraction = sum(item.allocation_fraction for item in estimates)
    unallocated_fraction = round(max(1.0 - estimate_fraction, 0.0) * selectivity_gap, 6)
    blocking = bool(unresolved)
    closure_status = "blocked" if blocking else "converged" if explicit_byproducts else "estimated"
    if not blocking and unallocated_fraction > 1e-6:
        closure_status = "estimated"
    estimate_status = "blocked" if blocking else "estimated"
    for item in estimates:
        if item.provenance == "explicit_participant" and not blocking:
            continue
        item.status = estimate_status
    extents.extend(
        ReactionExtent(
            extent_id=f"{route.route_id}_side_extent_{index}",
            reaction_label=f"Byproduct allocation to {estimate.component_name}",
            kind="byproduct",
            representative_component=estimate.component_name,
            representative_formula=estimate.formula,
            representative_molecular_weight_g_mol=estimate.molecular_weight_g_mol,
            representative_phase=estimate.phase,
            extent_fraction_of_converted_feed=round(selectivity_gap * estimate.allocation_fraction, 6),
            status="blocked" if blocking else estimate.status,
            notes=list(estimate.notes),
            citations=route.citations,
            assumptions=route.assumptions,
        )
        for index, estimate in enumerate(estimates, start=1)
    )
    closure.estimates = estimates
    closure.unresolved_byproducts = unresolved
    closure.closure_status = closure_status
    closure.blocking = blocking
    closure.notes = closure_notes
    extent_set = ReactionExtentSet(
        route_id=route.route_id,
        extents=extents,
        unallocated_selectivity_fraction=unallocated_fraction,
        closure_status=closure_status,
        notes=closure_notes
        + (
            [f"Unallocated selectivity fraction remains at {unallocated_fraction:.6f} of converted feed."]
            if unallocated_fraction > 1e-6
            else []
        ),
        citations=route.citations,
        assumptions=route.assumptions,
    )
    return extent_set, closure
