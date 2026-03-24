from __future__ import annotations

from aoc.models import (
    AlternativeOption,
    DecisionCriterion,
    DecisionRecord,
    EnergyBalance,
    EquipmentListArtifact,
    ProcessArchetype,
    ProjectBasis,
    RouteOption,
    ScenarioStability,
    SiteSelectionArtifact,
    UtilitySummaryArtifact,
)


def _decision(
    decision_id: str,
    context: str,
    criteria: list[DecisionCriterion],
    alternatives: list[AlternativeOption],
    citations: list[str],
    assumptions: list[str],
) -> DecisionRecord:
    selected = max(alternatives, key=lambda item: item.total_score)
    approval_required = any(item.candidate_id != selected.candidate_id and abs(item.total_score - selected.total_score) <= 4.0 for item in alternatives)
    return DecisionRecord(
        decision_id=decision_id,
        context=context,
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected as the highest-ranked alternative.",
        hard_constraint_results=["Alternative must remain technically feasible for the inferred process archetype."],
        confidence=0.84 if not approval_required else 0.72,
        scenario_stability=ScenarioStability.BORDERLINE if approval_required else ScenarioStability.STABLE,
        approval_required=approval_required,
        citations=citations,
        assumptions=assumptions,
    )


def select_reactor_configuration(route: RouteOption, archetype: ProcessArchetype | None) -> DecisionRecord:
    compound_family = archetype.compound_family if archetype else "organic"
    separation_family = archetype.dominant_separation_family if archetype else "distillation"
    candidates = [
        AlternativeOption(
            candidate_id="tubular_plug_flow_hydrator",
            candidate_type="reactor_selector",
            description="Tubular or plug-flow hydrator service",
            total_score=92.0 if "hydration" in route.name.lower() or route.route_id == "eo_hydration" else 62.0,
            score_breakdown={"heat_management": 94.0, "selectivity": 90.0, "operability": 88.0},
            feasible=compound_family == "organic",
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="jacketed_cstr_train",
            candidate_type="reactor_selector",
            description="Jacketed CSTR train",
            total_score=78.0 if compound_family == "organic" and separation_family != "solids" else 64.0,
            score_breakdown={"heat_management": 76.0, "selectivity": 72.0, "operability": 82.0},
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="fixed_bed_converter",
            candidate_type="reactor_selector",
            description="Fixed-bed catalytic converter",
            total_score=93.0 if compound_family == "inorganic" else 54.0,
            score_breakdown={"heat_management": 90.0, "selectivity": 84.0, "operability": 86.0},
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="slurry_loop_reactor",
            candidate_type="reactor_selector",
            description="Slurry loop reactor",
            total_score=76.0 if separation_family == "solids" else 48.0,
            score_breakdown={"heat_management": 70.0, "selectivity": 65.0, "operability": 72.0},
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
    ]
    return _decision(
        "reactor_choice",
        f"Reactor-family selection for route {route.route_id}.",
        [
            DecisionCriterion(name="Technical feasibility", weight=0.35, justification="Reactor must match chemistry and phase system."),
            DecisionCriterion(name="Heat management", weight=0.30, justification="Thermal controllability is central to safe operation."),
            DecisionCriterion(name="Operability", weight=0.20, justification="Selected reactor should support stable production."),
            DecisionCriterion(name="Economics", weight=0.15, justification="Reactor family should not impose avoidable cost burden."),
        ],
        candidates,
        route.citations,
        route.assumptions + ["Reactor selector scored alternatives from route type and process archetype."],
    )


def select_separation_configuration(route: RouteOption, archetype: ProcessArchetype | None) -> DecisionRecord:
    family = archetype.dominant_separation_family if archetype else "distillation"
    candidates = [
        AlternativeOption(candidate_id="distillation_train", candidate_type="separation_selector", description="Distillation and flash purification train", total_score=91.0 if family == "distillation" else 58.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="absorption_train", candidate_type="separation_selector", description="Absorption and drying train", total_score=94.0 if family == "absorption" else 52.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="crystallization_filtration_drying", candidate_type="separation_selector", description="Crystallization, filtration, and drying train", total_score=95.0 if family == "solids" else 45.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="extraction_recovery_train", candidate_type="separation_selector", description="Extraction with solvent recovery", total_score=86.0 if family == "extraction" else 55.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
    ]
    return _decision(
        "separation_choice",
        f"Separation-family selection for route {route.route_id}.",
        [
            DecisionCriterion(name="Technical feasibility", weight=0.40, justification="Separation train must fit the product-phase archetype."),
            DecisionCriterion(name="Operability", weight=0.20, justification="Simple, stable trains are preferred."),
            DecisionCriterion(name="Energy burden", weight=0.20, justification="Separation duty can dominate plant economics."),
            DecisionCriterion(name="Economics", weight=0.20, justification="Separation should minimize avoidable CAPEX/OPEX."),
        ],
        candidates,
        route.citations,
        route.assumptions + ["Separation selector scored alternatives from route metadata and process archetype."],
    )


def select_exchanger_configuration(route: RouteOption, energy_balance: EnergyBalance) -> DecisionRecord:
    hot_duty = max(energy_balance.total_heating_kw, energy_balance.total_cooling_kw)
    candidates = [
        AlternativeOption(candidate_id="shell_and_tube", candidate_type="exchanger_selector", description="Shell-and-tube exchanger basis", total_score=88.0 if hot_duty >= 500.0 else 72.0, feasible=True, citations=energy_balance.citations, assumptions=energy_balance.assumptions),
        AlternativeOption(candidate_id="plate_exchanger", candidate_type="exchanger_selector", description="Plate exchanger basis", total_score=84.0 if hot_duty < 2000.0 else 70.0, feasible=True, citations=energy_balance.citations, assumptions=energy_balance.assumptions),
        AlternativeOption(candidate_id="air_cooler", candidate_type="exchanger_selector", description="Air cooler basis", total_score=68.0, feasible=True, citations=energy_balance.citations, assumptions=energy_balance.assumptions),
        AlternativeOption(candidate_id="kettle_reboiler", candidate_type="exchanger_selector", description="Kettle/thermosyphon reboiler basis", total_score=86.0 if any(duty.unit_id.startswith("D-") for duty in energy_balance.duties) else 58.0, feasible=True, citations=energy_balance.citations, assumptions=energy_balance.assumptions),
    ]
    return _decision(
        "exchanger_choice",
        "Heat-exchanger family selection from the process energy envelope.",
        [
            DecisionCriterion(name="Technical feasibility", weight=0.35, justification="Selected exchanger must handle the identified duty and service."),
            DecisionCriterion(name="Heat-management fit", weight=0.30, justification="Thermal service and fouling tendency guide exchanger choice."),
            DecisionCriterion(name="Operability", weight=0.20, justification="Maintainability and controllability matter at feasibility stage."),
            DecisionCriterion(name="Economics", weight=0.15, justification="Exchanger choice affects both CAPEX and maintenance burden."),
        ],
        candidates,
        energy_balance.citations,
        energy_balance.assumptions + ["Exchanger selector scored alternatives from gross unit duties."],
    )


def select_storage_configuration(basis: ProjectBasis, archetype: ProcessArchetype | None) -> DecisionRecord:
    phase = archetype.dominant_product_phase if archetype else "liquid"
    candidates = [
        AlternativeOption(candidate_id="vertical_tank_farm", candidate_type="storage_selector", description="Vertical atmospheric tank farm", total_score=92.0 if phase == "liquid" else 55.0, feasible=True),
        AlternativeOption(candidate_id="pressure_bullets", candidate_type="storage_selector", description="Pressurized bullet storage", total_score=86.0 if phase == "gas" else 48.0, feasible=True),
        AlternativeOption(candidate_id="silo_hopper", candidate_type="storage_selector", description="Silo and hopper storage", total_score=94.0 if phase == "solid" else 44.0, feasible=True),
    ]
    return _decision(
        "storage_choice",
        f"Storage-philosophy selection for {basis.target_product}.",
        [
            DecisionCriterion(name="Phase compatibility", weight=0.40, justification="Storage type must match the dominant product phase."),
            DecisionCriterion(name="Safety", weight=0.25, justification="Storage arrangement must respect containment and handling risk."),
            DecisionCriterion(name="Dispatch fit", weight=0.20, justification="Storage should support realistic plant dispatch practice."),
            DecisionCriterion(name="Economics", weight=0.15, justification="Inventory philosophy should avoid unnecessary capital burden."),
        ],
        candidates,
        [],
        [f"Storage selector scored alternatives from product phase `{phase}`."],
    )


def select_moc_configuration(route: RouteOption, archetype: ProcessArchetype | None) -> DecisionRecord:
    route_text = f"{route.name} {' '.join(route.byproducts)} {' '.join(route.catalysts)}".lower()
    family = archetype.dominant_separation_family if archetype else "distillation"
    candidates = [
        AlternativeOption(candidate_id="carbon_steel", candidate_type="moc_selector", description="Carbon steel construction", total_score=90.0 if "chlor" not in route_text and family not in {"absorption"} else 45.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="ss316l", candidate_type="moc_selector", description="SS316L construction", total_score=88.0 if archetype and archetype.compound_family == "organic" else 76.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="alloy_steel_converter_service", candidate_type="moc_selector", description="Alloy steel converter service", total_score=95.0 if archetype and archetype.compound_family == "inorganic" else 52.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
        AlternativeOption(candidate_id="rubber_lined_cs", candidate_type="moc_selector", description="Rubber-lined carbon steel", total_score=84.0 if "chlor" in route_text or family == "absorption" else 58.0, feasible=True, citations=route.citations, assumptions=route.assumptions),
    ]
    return _decision(
        "moc_choice",
        f"Material-of-construction selection for route {route.route_id}.",
        [
            DecisionCriterion(name="Corrosion compatibility", weight=0.45, justification="MoC must withstand route chemistry and impurities."),
            DecisionCriterion(name="Temperature/pressure fit", weight=0.20, justification="Design envelope must be mechanically credible."),
            DecisionCriterion(name="Cleanability", weight=0.15, justification="Selected material should support realistic plant maintenance."),
            DecisionCriterion(name="Economics", weight=0.20, justification="MoC should not overdesign where cheaper safe options exist."),
        ],
        candidates,
        route.citations,
        route.assumptions + ["MoC selector scored alternatives from chemistry family and corrosive cues in the route metadata."],
    )


def select_layout_configuration(
    site: SiteSelectionArtifact,
    equipment: EquipmentListArtifact,
    utilities: UtilitySummaryArtifact,
    flowsheet_graph,
    archetype: ProcessArchetype | None,
) -> DecisionRecord:
    equipment_count = len(equipment.items)
    utility_count = len(utilities.items)
    phase = archetype.dominant_product_phase if archetype else "liquid"
    candidates = [
        AlternativeOption(
            candidate_id="compact_process_core",
            candidate_type="layout_selector",
            description="Compact process core with short pipe runs",
            total_score=88.0 if equipment_count <= 6 else 78.0,
            score_breakdown={"piping": 92.0, "maintenance": 74.0, "hazard": 70.0, "utilities": 88.0},
            feasible=True,
            citations=site.citations + equipment.citations,
            assumptions=site.assumptions + equipment.assumptions,
        ),
        AlternativeOption(
            candidate_id="segregated_hazard_zones",
            candidate_type="layout_selector",
            description="Segregated hazard-zone layout",
            total_score=92.0 if phase in {"gas", "liquid"} else 80.0,
            score_breakdown={"piping": 76.0, "maintenance": 82.0, "hazard": 95.0, "utilities": 84.0},
            feasible=True,
            citations=site.citations + equipment.citations,
            assumptions=site.assumptions + equipment.assumptions,
        ),
        AlternativeOption(
            candidate_id="solids_block_layout",
            candidate_type="layout_selector",
            description="Block layout with solids handling and truck access priority",
            total_score=94.0 if phase == "solid" else 58.0,
            score_breakdown={"piping": 70.0, "maintenance": 88.0, "hazard": 82.0, "utilities": 74.0},
            feasible=True,
            citations=site.citations + equipment.citations,
            assumptions=site.assumptions + equipment.assumptions,
        ),
    ]
    return _decision(
        "layout_choice",
        f"Site-plot arrangement scored for {site.selected_site} with {equipment_count} major equipment items and {utility_count} utility services.",
        [
            DecisionCriterion(name="Piping economy", weight=0.25, justification="Compact layouts reduce pipe runs and heat loss."),
            DecisionCriterion(name="Hazard segregation", weight=0.30, justification="Process areas must respect credible hazard spacing."),
            DecisionCriterion(name="Maintenance access", weight=0.20, justification="Layout must support realistic plant upkeep."),
            DecisionCriterion(name="Utility routing", weight=0.15, justification="Layout should not complicate utility distribution."),
            DecisionCriterion(name="Dispatch/emergency access", weight=0.10, justification="Truck movement and firefighting access remain essential."),
        ],
        candidates,
        site.citations + equipment.citations + utilities.citations,
        site.assumptions + equipment.assumptions + utilities.assumptions + [f"Flowsheet graph nodes considered: {len(getattr(flowsheet_graph, 'nodes', []))}."],
    )
