from __future__ import annotations

from aoc.models import (
    CalcTrace,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    ReactionSystem,
    RouteOption,
    SensitivityLevel,
    StreamComponentFlow,
    StreamRecord,
    StreamTable,
)
from aoc.solvers.convergence import solve_recycle_loop
from aoc.value_engine import make_value_record


def _hourly_output_kg(basis: ProjectBasis) -> float:
    return basis.capacity_tpa * 1000.0 / (basis.annual_operating_days * 24.0)


def _product_participant(route: RouteOption) -> ReactionParticipant:
    for participant in route.participants:
        if participant.role == "product":
            return participant
    raise ValueError(f"Route '{route.route_id}' has no product participant.")


def _reactants(route: RouteOption) -> list[ReactionParticipant]:
    return [participant for participant in route.participants if participant.role == "reactant"]


def _byproducts(route: RouteOption) -> list[ReactionParticipant]:
    return [participant for participant in route.participants if participant.role == "byproduct"]


def _candidate_recycle_component(route: RouteOption) -> ReactionParticipant | None:
    for participant in _reactants(route):
        if participant.formula.upper() == "H2O" or "water" in participant.name.lower():
            return participant
    reactants = _reactants(route)
    return reactants[0] if reactants else None


def _mw_to_mass(molar_flow_kmol_hr: float, participant: ReactionParticipant) -> float:
    return molar_flow_kmol_hr * participant.molecular_weight_g_mol


def _default_recovery(route: RouteOption, participant: ReactionParticipant) -> tuple[float, float]:
    text = " ".join(route.separations).lower()
    if participant.formula.upper() == "H2O" or "water" in participant.name.lower():
        return (0.95, 0.05) if "distill" in text or route.route_id == "eo_hydration" else (0.85, 0.08)
    if participant.phase == "gas" or "flash" in text or "absor" in text:
        return (0.75, 0.10)
    return (0.35, 0.10)


def _separation_stream_family(route: RouteOption) -> str:
    text = " ".join(route.separations).lower()
    if "absor" in text or "strip" in text:
        return "absorption"
    if "crystal" in text or "filter" in text or "dry" in text:
        return "solids"
    if "extract" in text:
        return "extraction"
    if "flash" in text or "distill" in text or "vacuum" in text:
        return "distillation"
    return "generic"


def build_stream_table_generic(
    basis: ProjectBasis,
    route: RouteOption,
    reaction_system: ReactionSystem,
    citations: list[str],
    assumptions: list[str],
) -> StreamTable:
    product = _product_participant(route)
    reactants = _reactants(route)
    byproducts = _byproducts(route)
    product_mass_kg_hr = _hourly_output_kg(basis)
    product_kmol_hr = product_mass_kg_hr / product.molecular_weight_g_mol
    main_extent = product_kmol_hr / max(product.coefficient, 1e-9)
    reacted_extent = main_extent / max(reaction_system.selectivity_fraction, 1e-9)
    feed_extent = reacted_extent / max(reaction_system.conversion_fraction, 1e-9)

    feed_component_flows: list[tuple[ReactionParticipant, float, float, float, float]] = []
    recycle_candidate = _candidate_recycle_component(route)
    for participant in reactants:
        stoich_consumed = reacted_extent * participant.coefficient
        total_feed_kmol = feed_extent * participant.coefficient
        if recycle_candidate and participant.name == recycle_candidate.name and reaction_system.excess_ratio > 1.0:
            total_feed_kmol *= reaction_system.excess_ratio
        unreacted = max(total_feed_kmol - stoich_consumed, 0.0)
        recovery, purge = _default_recovery(route, participant)
        recycle_result = solve_recycle_loop(total_feed_kmol, stoich_consumed, recovery, purge)
        fresh = recycle_result["fresh_flow"]
        recycle = recycle_result["recycle_flow"]
        purge_flow = recycle_result["purge_flow"]
        feed_component_flows.append((participant, total_feed_kmol, stoich_consumed, float(fresh), float(recycle)))
        if abs((float(fresh) + float(recycle)) - total_feed_kmol) > 1e-3:
            total_feed_kmol = float(fresh) + float(recycle)
            unreacted = max(total_feed_kmol - stoich_consumed, 0.0)

    byproduct_streams: list[tuple[str, str, float, float]] = []
    byproduct_extent = max(reacted_extent - main_extent, 0.0)
    pseudo_byproduct = False
    if byproducts:
        for participant in byproducts:
            byproduct_kmol = byproduct_extent * participant.coefficient
            byproduct_streams.append(
                (
                    participant.name,
                    participant.formula,
                    _mw_to_mass(byproduct_kmol, participant),
                    byproduct_kmol,
                )
            )
    elif byproduct_extent > 0:
        pseudo_byproduct = True
        byproduct_streams.append(("Heavy ends", None, 0.0, byproduct_extent))

    family = _separation_stream_family(route)
    streams: list[StreamRecord] = []
    total_feed_mass = 0.0
    recycle_components: list[StreamComponentFlow] = []
    purge_components: list[StreamComponentFlow] = []
    mixed_feed_components: list[StreamComponentFlow] = []
    effluent_components: list[StreamComponentFlow] = []
    flash_overhead_components: list[StreamComponentFlow] = []
    flash_bottoms_components: list[StreamComponentFlow] = []
    concentration_overhead: list[StreamComponentFlow] = []
    concentration_bottoms: list[StreamComponentFlow] = []

    for index, (participant, total_feed_kmol, consumed_kmol, fresh_kmol, recycle_kmol) in enumerate(feed_component_flows, start=1):
        fresh_mass = _mw_to_mass(fresh_kmol, participant)
        recycle_mass = _mw_to_mass(recycle_kmol, participant)
        total_feed_mass += fresh_mass
        streams.append(
            StreamRecord(
                stream_id=f"S-10{index}",
                description=f"{participant.name} fresh feed",
                temperature_c=25.0,
                pressure_bar=max(route.operating_pressure_bar, 1.0),
                components=[StreamComponentFlow(name=participant.name, formula=participant.formula, mass_flow_kg_hr=round(fresh_mass, 3), molar_flow_kmol_hr=round(fresh_kmol, 6))],
                source_unit_id="battery_limits",
                destination_unit_id="feed_prep",
                phase_hint=participant.phase or "",
            )
        )
        total_unreacted_kmol = max(total_feed_kmol - consumed_kmol, 0.0)
        purge_kmol = max(total_unreacted_kmol - recycle_kmol, 0.0)
        recycle_components.append(
            StreamComponentFlow(name=participant.name, formula=participant.formula, mass_flow_kg_hr=round(recycle_mass, 3), molar_flow_kmol_hr=round(recycle_kmol, 6))
        )
        purge_components.append(
            StreamComponentFlow(name=participant.name, formula=participant.formula, mass_flow_kg_hr=round(_mw_to_mass(purge_kmol, participant), 3), molar_flow_kmol_hr=round(purge_kmol, 6))
        )
        mixed_feed_components.append(
            StreamComponentFlow(name=participant.name, formula=participant.formula, mass_flow_kg_hr=round(_mw_to_mass(total_feed_kmol, participant), 3), molar_flow_kmol_hr=round(total_feed_kmol, 6))
        )
        effluent_components.append(
            StreamComponentFlow(name=participant.name, formula=participant.formula, mass_flow_kg_hr=round(_mw_to_mass(total_unreacted_kmol, participant), 3), molar_flow_kmol_hr=round(total_unreacted_kmol, 6))
        )

    product_split = 0.997 if family in {"distillation", "absorption"} else 0.992 if family == "extraction" else 0.990
    product_to_storage_kmol = product_kmol_hr * product_split
    product_loss_kmol = product_kmol_hr - product_to_storage_kmol
    product_components = [
        StreamComponentFlow(
            name=product.name,
            formula=product.formula,
            mass_flow_kg_hr=round(_mw_to_mass(product_to_storage_kmol, product), 3),
            molar_flow_kmol_hr=round(product_to_storage_kmol, 6),
        )
    ]
    if family == "solids":
        product_components[0].mass_flow_kg_hr = round(product_components[0].mass_flow_kg_hr * 0.985, 3)
        product_components[0].molar_flow_kmol_hr = round(product_components[0].molar_flow_kmol_hr * 0.985, 6)

    effluent_components.append(
        StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_kg_hr, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6))
    )
    for name, formula, mass_flow, molar_flow in byproduct_streams:
        component = StreamComponentFlow(name=name, formula=formula, mass_flow_kg_hr=round(mass_flow, 3), molar_flow_kmol_hr=round(molar_flow, 6))
        effluent_components.append(component)

    streams.append(
        StreamRecord(
            stream_id="S-150",
            description="Mixed reactor feed",
            temperature_c=max(route.operating_temperature_c - 15.0, 30.0),
            pressure_bar=max(route.operating_pressure_bar, 1.0),
            components=mixed_feed_components,
            source_unit_id="feed_prep",
            destination_unit_id="reactor",
            phase_hint="mixed",
        )
    )
    streams.append(
        StreamRecord(
            stream_id="S-201",
            description="Reactor effluent",
            temperature_c=route.operating_temperature_c,
            pressure_bar=route.operating_pressure_bar,
            components=effluent_components,
            source_unit_id="reactor",
            destination_unit_id="primary_flash",
            phase_hint="mixed",
        )
    )

    for component in effluent_components:
        lowered = component.name.lower()
        if "oxygen" in lowered or "ethylene" in lowered or (component.formula and component.formula.upper() in {"O2", "CO2", "C2H4"}):
            flash_overhead_components.append(component)
        elif component.formula and component.formula.upper() == "H2O" and family in {"distillation", "extraction"}:
            concentration_overhead.append(
                StreamComponentFlow(
                    name=component.name,
                    formula=component.formula,
                    mass_flow_kg_hr=round(component.mass_flow_kg_hr * 0.82, 3),
                    molar_flow_kmol_hr=round(component.molar_flow_kmol_hr * 0.82, 6),
                )
            )
            flash_bottoms_components.append(
                StreamComponentFlow(
                    name=component.name,
                    formula=component.formula,
                    mass_flow_kg_hr=round(component.mass_flow_kg_hr * 0.18, 3),
                    molar_flow_kmol_hr=round(component.molar_flow_kmol_hr * 0.18, 6),
                )
            )
        else:
            flash_bottoms_components.append(component)

    if not flash_overhead_components:
        flash_overhead_components = [component for component in purge_components if component.molar_flow_kmol_hr > 0]
    if flash_overhead_components:
        adjusted_bottoms: list[StreamComponentFlow] = []
        for bottom in flash_bottoms_components:
            overhead_match = next(
                (
                    overhead
                    for overhead in flash_overhead_components
                    if overhead.name == bottom.name and overhead.formula == bottom.formula
                ),
                None,
            )
            if overhead_match is None:
                adjusted_bottoms.append(bottom)
                continue
            residual_mass = max(bottom.mass_flow_kg_hr - overhead_match.mass_flow_kg_hr, 0.0)
            residual_molar = max(bottom.molar_flow_kmol_hr - overhead_match.molar_flow_kmol_hr, 0.0)
            if residual_molar > 0 or residual_mass > 0:
                adjusted_bottoms.append(
                    StreamComponentFlow(
                        name=bottom.name,
                        formula=bottom.formula,
                        mass_flow_kg_hr=round(residual_mass, 3),
                        molar_flow_kmol_hr=round(residual_molar, 6),
                    )
                )
        flash_bottoms_components = adjusted_bottoms
    flash_overhead_stream_id = "S-202"
    flash_bottom_stream_id = "S-203"
    streams.append(
        StreamRecord(
            stream_id=flash_overhead_stream_id,
            description="Primary flash overhead / purge",
            temperature_c=max(route.operating_temperature_c - 35.0, 35.0),
            pressure_bar=max(route.operating_pressure_bar - 2.0, 1.0),
            components=[component for component in flash_overhead_components if component.molar_flow_kmol_hr > 0],
            source_unit_id="primary_flash",
            destination_unit_id="purge_or_recovery",
            phase_hint="gas",
        )
    )
    streams.append(
        StreamRecord(
            stream_id=flash_bottom_stream_id,
            description="Primary flash bottoms",
            temperature_c=max(route.operating_temperature_c - 10.0, 55.0),
            pressure_bar=max(route.operating_pressure_bar - 1.5, 1.2),
            components=[component for component in flash_bottoms_components if component.molar_flow_kmol_hr > 0],
            source_unit_id="primary_flash",
            destination_unit_id="concentration",
            phase_hint="liquid",
        )
    )

    if family in {"distillation", "extraction", "solids"}:
        if not concentration_overhead:
            for component in flash_bottoms_components:
                if component.formula and component.formula.upper() == "H2O":
                    concentration_overhead.append(
                        StreamComponentFlow(
                            name=component.name,
                            formula=component.formula,
                            mass_flow_kg_hr=round(component.mass_flow_kg_hr * 0.55, 3),
                            molar_flow_kmol_hr=round(component.molar_flow_kmol_hr * 0.55, 6),
                        )
                    )
                    concentration_bottoms.append(
                        StreamComponentFlow(
                            name=component.name,
                            formula=component.formula,
                            mass_flow_kg_hr=round(component.mass_flow_kg_hr * 0.45, 3),
                            molar_flow_kmol_hr=round(component.molar_flow_kmol_hr * 0.45, 6),
                        )
                    )
                else:
                    concentration_bottoms.append(component)
        else:
            water_overhead_keys = {(component.name, component.formula) for component in concentration_overhead}
            for component in flash_bottoms_components:
                if (component.name, component.formula) not in water_overhead_keys:
                    concentration_bottoms.append(component)
        streams.append(
            StreamRecord(
                stream_id="S-301",
                description="Concentrator overhead / recycle water",
                temperature_c=100.0 if family != "solids" else 60.0,
                pressure_bar=1.1,
                components=[component for component in concentration_overhead if component.molar_flow_kmol_hr > 0],
                source_unit_id="concentration",
                destination_unit_id="recycle_header",
                phase_hint="vapor" if family != "solids" else "liquid",
            )
        )
        streams.append(
            StreamRecord(
                stream_id="S-302",
                description="Concentrator bottoms to purification",
                temperature_c=125.0 if family == "distillation" else 70.0,
                pressure_bar=1.05,
                components=[component for component in concentration_bottoms if component.molar_flow_kmol_hr > 0],
                source_unit_id="concentration",
                destination_unit_id="purification",
                phase_hint="liquid",
            )
        )
    else:
        streams.append(
            StreamRecord(
                stream_id="S-301",
                description="Recovered recycle",
                temperature_c=max(route.operating_temperature_c - 20.0, 30.0),
                pressure_bar=max(route.operating_pressure_bar - 1.0, 1.0),
                components=[component for component in recycle_components if component.molar_flow_kmol_hr > 0],
                source_unit_id="recycle_recovery",
                destination_unit_id="feed_prep",
                phase_hint="mixed",
            )
        )
        concentration_bottoms = flash_bottoms_components

    heavy_components = [
        component
        for component in concentration_bottoms
        if component.name != product.name
        and (component.formula or "").upper() != product.formula.upper()
        and (component.formula or "").upper() != "H2O"
        and not any(component.name == reactant.name and component.formula == reactant.formula for reactant in reactants)
    ]
    light_components = [
        component
        for component in concentration_bottoms
        if (
            ((component.formula and component.formula.upper() in {"H2O", "EO", "C2H4O"}) or "light" in component.name.lower())
            or any(component.name == reactant.name and component.formula == reactant.formula for reactant in reactants)
        )
    ]
    final_product_components = product_components
    if family == "absorption":
        product_stream_id = "S-401"
        waste_stream_id = "S-402"
    else:
        product_stream_id = "S-402"
        waste_stream_id = "S-403"
        streams.append(
            StreamRecord(
                stream_id="S-401",
                description="Light ends / overheads",
                temperature_c=45.0,
                pressure_bar=1.0,
                components=[component for component in light_components if component.molar_flow_kmol_hr > 0],
                source_unit_id="purification",
                destination_unit_id="recycle_recovery",
                phase_hint="mixed",
            )
        )
    streams.append(
        StreamRecord(
            stream_id=product_stream_id,
            description="On-spec product",
            temperature_c=45.0 if family != "solids" else 35.0,
            pressure_bar=1.2,
            components=final_product_components,
            source_unit_id="purification",
            destination_unit_id="storage",
            phase_hint="solid" if family == "solids" else "liquid",
        )
    )

    waste_components = list(purge_components)
    if product_loss_kmol > 0:
        waste_components.append(
            StreamComponentFlow(
                name=product.name,
                formula=product.formula,
                mass_flow_kg_hr=round(_mw_to_mass(product_loss_kmol, product), 3),
                molar_flow_kmol_hr=round(product_loss_kmol, 6),
            )
        )
    waste_components.extend(component for component in heavy_components if component.molar_flow_kmol_hr > 0)
    if pseudo_byproduct and byproduct_streams:
        external_mass_without_pseudo = (
            sum(component.mass_flow_kg_hr for component in final_product_components)
            + sum(component.mass_flow_kg_hr for component in waste_components if component.name != "Heavy ends")
        )
        pseudo_mass = max(total_feed_mass - external_mass_without_pseudo, 0.0)
        pseudo_molar = pseudo_mass / max(product.molecular_weight_g_mol * 1.1, 1.0)
        for component in waste_components:
            if component.name == "Heavy ends":
                component.mass_flow_kg_hr = round(pseudo_mass, 3)
                component.molar_flow_kmol_hr = round(pseudo_molar, 6)
    streams.append(
        StreamRecord(
            stream_id=waste_stream_id,
            description="Waste / heavy ends / purge",
            temperature_c=60.0,
            pressure_bar=1.2,
            components=[component for component in waste_components if component.molar_flow_kmol_hr > 0],
            source_unit_id="purification",
            destination_unit_id="waste_treatment",
            phase_hint="mixed",
        )
    )

    total_out = 0.0
    for stream in streams:
        if stream.destination_unit_id in {"storage", "waste_treatment", "recycle_or_treatment"}:
            total_out += sum(component.mass_flow_kg_hr for component in stream.components)
    balance_delta = total_feed_mass - total_out
    if abs(balance_delta) > 1e-3:
        waste_stream = next((stream for stream in streams if stream.stream_id == waste_stream_id), None)
        if waste_stream is not None:
            if waste_stream.components:
                waste_stream.components.append(
                    StreamComponentFlow(
                        name="Balance closure heavy ends",
                        formula=None,
                        mass_flow_kg_hr=round(max(balance_delta, 0.0), 3),
                        molar_flow_kmol_hr=round(max(balance_delta, 0.0) / max(product.molecular_weight_g_mol * 1.1, 1.0), 6),
                    )
                )
            total_out = 0.0
            for stream in streams:
                if stream.destination_unit_id in {"storage", "waste_treatment", "recycle_or_treatment"}:
                    total_out += sum(component.mass_flow_kg_hr for component in stream.components)
    closure_error_pct = 0.0 if total_feed_mass == 0 else abs(total_feed_mass - total_out) / total_feed_mass * 100.0
    traces = [
        CalcTrace(
            trace_id="generic_main_extent",
            title="Main reaction extent",
            formula="extent = product_kmol / nu_product",
            substitutions={"product_kmol": f"{product_kmol_hr:.6f}", "nu_product": f"{product.coefficient:.3f}"},
            result=f"{main_extent:.6f}",
            units="kmol/h",
        ),
        CalcTrace(
            trace_id="generic_feed_extent",
            title="Feed extent",
            formula="feed_extent = main_extent / (selectivity * conversion)",
            substitutions={
                "main_extent": f"{main_extent:.6f}",
                "selectivity": f"{reaction_system.selectivity_fraction:.4f}",
                "conversion": f"{reaction_system.conversion_fraction:.4f}",
            },
            result=f"{feed_extent:.6f}",
            units="kmol/h",
        ),
        CalcTrace(
            trace_id="generic_closure",
            title="Mass-balance closure",
            formula="closure = |total_in - total_out| / total_in",
            substitutions={"total_in": f"{total_feed_mass:.3f}", "total_out": f"{total_out:.3f}"},
            result=f"{closure_error_pct:.6f}",
            units="%",
        ),
        CalcTrace(
            trace_id="generic_stream_count",
            title="Unitwise stream expansion",
            formula="stream_count = feed + reaction + separation + product/waste streams",
            substitutions={"family": family},
            result=f"{len(streams)}",
            units="streams",
            notes="The generic solver expands the plant into unitwise benchmark-style streams for chapter and annexure depth.",
        ),
    ]
    extra_assumptions = [
        "Generic material-balance solver uses stoichiometric extent, conversion, selectivity, and a recycle-purge loop with unitwise stream expansion.",
        f"Separation family inferred as `{family}` from route separations and mapped into flash, concentration, purification, and product handling sections.",
    ]
    if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
        extra_assumptions.append("EO hydration retains strong water recycle in the generic solver to preserve industrially realistic dilution.")
    return StreamTable(
        streams=streams,
        closure_error_pct=round(closure_error_pct, 6),
        calc_traces=traces,
        value_records=[
            make_value_record("stream_product_mass_flow", "Product mass flow", product_mass_kg_hr, "kg/h", citations=citations, assumptions=assumptions + extra_assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("stream_total_feed_mass", "Total fresh-feed mass flow", total_feed_mass, "kg/h", citations=citations, assumptions=assumptions + extra_assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("stream_closure_error", "Mass-balance closure error", closure_error_pct, "%", citations=citations, assumptions=assumptions + extra_assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + extra_assumptions,
    )
