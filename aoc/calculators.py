from __future__ import annotations

import math
import re

from aoc.economics_v2 import (
    build_cost_model_v2,
    build_financial_model_v2,
    build_financing_basis_decision,
    build_logistics_basis_decision,
    build_procurement_basis_decision,
    build_working_capital_model_v2,
    evaluate_financing_basis_decision,
)
from aoc.models import (
    CalcTrace,
    ColumnDesign,
    CostModel,
    DecisionRecord,
    EnergyBalance,
    EquipmentSpec,
    FinancialModel,
    FlowsheetBlueprintArtifact,
    HeatExchangerDesign,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    MarketAssessmentArtifact,
    OperationsPlanningArtifact,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    ReactionSystem,
    ReactorDesign,
    RouteOption,
    SensitivityLevel,
    ScenarioPolicy,
    ScenarioResult,
    SiteSelectionArtifact,
    StorageDesign,
    StreamComponentFlow,
    StreamRecord,
    StreamTable,
    ThermoAssessmentArtifact,
    UnitDuty,
    UtilityBasis,
    UtilityArchitectureDecision,
    UtilityLoad,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    WorkingCapitalModel,
)
from aoc.properties.models import MixturePropertyArtifact, PropertyPackageArtifact, SeparationThermoArtifact
from aoc.solvers import (
    build_column_design_generic,
    build_energy_balance_generic,
    build_equipment_list_generic,
    build_heat_exchanger_design_generic,
    build_reactor_design_generic,
    build_storage_design_generic,
    build_stream_table_generic,
)
from aoc.solvers.reaction_network import build_reaction_network
from aoc.value_engine import make_value_record


FORMULA_RE = re.compile(r"([A-Z][a-z]?)(\d*)")


def parse_formula(formula: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for symbol, count in FORMULA_RE.findall(formula):
        counts[symbol] = counts.get(symbol, 0) + int(count or "1")
    return counts


def reaction_balance_delta(route: RouteOption) -> dict[str, float]:
    delta: dict[str, float] = {}
    for participant in route.participants:
        sign = -1.0 if participant.role == "reactant" else 1.0
        for symbol, count in parse_formula(participant.formula).items():
            delta[symbol] = delta.get(symbol, 0.0) + sign * participant.coefficient * count
    return delta


def reaction_is_balanced(route: RouteOption, tolerance: float = 1e-6) -> bool:
    return all(abs(value) <= tolerance for value in reaction_balance_delta(route).values())


def annual_output_kg(basis: ProjectBasis) -> float:
    return basis.capacity_tpa * 1000.0


def operating_hours_per_year(basis: ProjectBasis) -> float:
    return basis.annual_operating_days * 24.0


def hourly_output_kg(basis: ProjectBasis) -> float:
    return annual_output_kg(basis) / operating_hours_per_year(basis)


def sensible_duty_kw(mass_flow_kg_hr: float, cp_kj_kg_k: float, delta_t_k: float) -> float:
    return (mass_flow_kg_hr * cp_kj_kg_k * delta_t_k) / 3600.0


def latent_duty_kw(mass_flow_kg_hr: float, latent_heat_kj_kg: float) -> float:
    return (mass_flow_kg_hr * latent_heat_kj_kg) / 3600.0


def pump_power_kw(flow_m3_hr: float, head_m: float, density_kg_m3: float = 1000.0, efficiency: float = 0.7) -> float:
    if efficiency <= 0:
        raise ValueError("Efficiency must be positive.")
    return (density_kg_m3 * 9.81 * (flow_m3_hr / 3600.0) * head_m) / (1000.0 * efficiency)


def _selected_utility_case(utility_network_decision: UtilityNetworkDecision | None):
    if utility_network_decision is None or not utility_network_decision.selected_case_id:
        return None
    for item in utility_network_decision.cases:
        if item.case_id == utility_network_decision.selected_case_id:
            return item
    return None


def _participant(route: RouteOption, role: str, name_fragment: str | None = None) -> ReactionParticipant:
    participants = [item for item in route.participants if item.role == role]
    if name_fragment:
        lowered = name_fragment.lower()
        for participant in participants:
            if lowered in participant.name.lower():
                return participant
    if not participants:
        raise ValueError(f"No participant found for role '{role}'.")
    return participants[0]


def build_reaction_system(
    basis: ProjectBasis,
    route: RouteOption,
    kinetics: KineticAssessmentArtifact,
    citations: list[str],
    assumptions: list[str],
) -> ReactionSystem:
    extent_set, byproduct_closure = build_reaction_network(route, min(max(route.selectivity_fraction, 0.0), 1.0))
    if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA and route.route_id == "eo_hydration":
        conversion = 0.985
        selectivity = min(max(route.selectivity_fraction, 0.85), 0.98)
        excess_ratio = 20.0
        extent_set, byproduct_closure = build_reaction_network(route, selectivity)
        traces = [
            CalcTrace(
                trace_id="rxn_conv",
                title="Ethylene oxide conversion basis",
                formula="X = 0.985",
                result=f"{conversion:.4f}",
                units="fraction",
                notes="High water excess suppresses oligomer formation in direct hydration service.",
            ),
            CalcTrace(
                trace_id="rxn_sel",
                title="Monoethylene glycol selectivity basis",
                formula="S = route_selectivity",
                substitutions={"route_selectivity": f"{route.selectivity_fraction:.4f}"},
                result=f"{selectivity:.4f}",
                units="fraction",
                notes="Selectivity is capped into a conservative industrial window for preliminary design.",
            ),
            CalcTrace(
                trace_id="rxn_excess",
                title="Water excess ratio",
                formula="Excess water ratio = 20 mol H2O / mol EO feed",
                result=f"{excess_ratio:.1f}",
                units="mol/mol",
                notes="Chosen to reflect dilute hydration conditions used to favor MEG over higher glycols.",
            ),
            CalcTrace(
                trace_id="rxn_byproduct_gap",
                title="Byproduct selectivity gap",
                formula="Gap = 1 - S",
                substitutions={"S": f"{selectivity:.4f}"},
                result=f"{byproduct_closure.selectivity_gap_fraction:.4f}",
                units="fraction of converted feed",
                notes="Gap is allocated explicitly across side products through the reaction-network closure artifact.",
            ),
        ]
        return ReactionSystem(
            route_id=route.route_id,
            main_reaction=route.reaction_equation,
            side_reactions=["2 EO + H2O -> DEG", "DEG + EO -> TEG"],
            conversion_fraction=conversion,
            selectivity_fraction=selectivity,
            excess_ratio=excess_ratio,
            notes="EG template uses direct hydration with high water dilution to limit heavy glycol formation.",
            reaction_extent_set=extent_set,
            byproduct_closure=byproduct_closure,
            calc_traces=traces,
            value_records=[
                make_value_record("rxn_conversion", "Reaction conversion", conversion, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("rxn_selectivity", "Reaction selectivity", selectivity, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("rxn_water_excess_ratio", "Water excess ratio", excess_ratio, "mol/mol", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record(
                    "rxn_byproduct_gap_fraction",
                    "Byproduct selectivity gap",
                    byproduct_closure.selectivity_gap_fraction,
                    "fraction",
                    citations=citations,
                    assumptions=assumptions,
                    sensitivity=SensitivityLevel.HIGH,
                    blocking=byproduct_closure.blocking,
                ),
            ],
            citations=citations,
            assumptions=assumptions
            + [f"Residence time basis retained at {kinetics.design_residence_time_hr:.2f} h."]
            + byproduct_closure.notes,
        )
    conversion = min(max(route.yield_fraction, 0.5), 0.98)
    selectivity = min(max(route.selectivity_fraction, 0.5), 0.99)
    extent_set, byproduct_closure = build_reaction_network(route, selectivity)
    return ReactionSystem(
        route_id=route.route_id,
        main_reaction=route.reaction_equation,
        side_reactions=[f"Byproduct allocation to {item.component_name}" for item in byproduct_closure.estimates],
        conversion_fraction=conversion,
        selectivity_fraction=selectivity,
        excess_ratio=1.05,
        notes="Fallback reaction system uses route yield/selectivity as preliminary conversion basis.",
        reaction_extent_set=extent_set,
        byproduct_closure=byproduct_closure,
        calc_traces=[
            CalcTrace(
                trace_id="rxn_byproduct_gap",
                title="Byproduct selectivity gap",
                formula="Gap = 1 - S",
                substitutions={"S": f"{selectivity:.4f}"},
                result=f"{byproduct_closure.selectivity_gap_fraction:.4f}",
                units="fraction of converted feed",
                notes="Gap is allocated explicitly across the reaction-network closure artifact before stream solving.",
            ),
        ],
        value_records=[
            make_value_record("rxn_conversion", "Reaction conversion", conversion, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("rxn_selectivity", "Reaction selectivity", selectivity, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("rxn_excess_ratio", "Excess ratio", 1.05, "mol/mol", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record(
                "rxn_byproduct_gap_fraction",
                "Byproduct selectivity gap",
                byproduct_closure.selectivity_gap_fraction,
                "fraction",
                citations=citations,
                assumptions=assumptions,
                sensitivity=SensitivityLevel.HIGH,
                blocking=byproduct_closure.blocking,
            ),
        ],
        citations=citations,
        assumptions=assumptions
        + [f"Residence time basis retained at {kinetics.design_residence_time_hr:.2f} h."]
        + byproduct_closure.notes,
    )


def build_stream_table(
    basis: ProjectBasis,
    route: RouteOption,
    reaction_system: ReactionSystem,
    citations: list[str],
    assumptions: list[str],
    property_packages: PropertyPackageArtifact | None = None,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None = None,
) -> StreamTable:
    return build_stream_table_generic(
        basis,
        route,
        reaction_system,
        citations,
        assumptions,
        property_packages,
        flowsheet_blueprint,
    )

    if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA and route.route_id == "eo_hydration":
        product = _participant(route, "product", "ethylene glycol")
        eo = _participant(route, "reactant", "ethylene oxide")
        water = _participant(route, "reactant", "water")

        product_mass_kg_hr = hourly_output_kg(basis)
        product_kmol_hr = product_mass_kg_hr / product.molecular_weight_g_mol
        eo_converted_kmol_hr = product_kmol_hr / reaction_system.selectivity_fraction
        eo_feed_kmol_hr = eo_converted_kmol_hr / reaction_system.conversion_fraction
        eo_unreacted_kmol_hr = eo_feed_kmol_hr - eo_converted_kmol_hr
        eo_to_deg_equivalent_kmol_hr = eo_converted_kmol_hr - product_kmol_hr
        deg_mol_hr = eo_to_deg_equivalent_kmol_hr / 2.0
        deg_mass_kg_hr = deg_mol_hr * 106.12
        water_feed_kmol_hr = eo_feed_kmol_hr * reaction_system.excess_ratio * water.coefficient
        water_consumed_kmol_hr = product_kmol_hr + deg_mol_hr
        water_recovered_kmol_hr = max(water_feed_kmol_hr - water_consumed_kmol_hr, 0.0)

        eo_feed_mass_kg_hr = eo_feed_kmol_hr * eo.molecular_weight_g_mol
        water_feed_mass_kg_hr = water_feed_kmol_hr * water.molecular_weight_g_mol
        eo_unreacted_mass_kg_hr = eo_unreacted_kmol_hr * eo.molecular_weight_g_mol
        water_recovered_mass_kg_hr = water_recovered_kmol_hr * water.molecular_weight_g_mol

        total_in = eo_feed_mass_kg_hr + water_feed_mass_kg_hr
        total_out = product_mass_kg_hr + deg_mass_kg_hr + eo_unreacted_mass_kg_hr + water_recovered_mass_kg_hr
        closure_error_pct = abs(total_in - total_out) / max(total_in, 1.0) * 100.0

        traces = [
            CalcTrace(
                trace_id="mb_prod_kmol",
                title="Product molar flow",
                formula="n_MEG = m_MEG / MW_MEG",
                substitutions={"m_MEG": f"{product_mass_kg_hr:.3f} kg/h", "MW_MEG": f"{product.molecular_weight_g_mol:.3f} kg/kmol"},
                result=f"{product_kmol_hr:.6f}",
                units="kmol/h",
            ),
            CalcTrace(
                trace_id="mb_eo_feed",
                title="Ethylene oxide feed",
                formula="n_EO,feed = n_MEG / (S * X)",
                substitutions={"n_MEG": f"{product_kmol_hr:.6f}", "S": f"{reaction_system.selectivity_fraction:.4f}", "X": f"{reaction_system.conversion_fraction:.4f}"},
                result=f"{eo_feed_kmol_hr:.6f}",
                units="kmol/h",
            ),
            CalcTrace(
                trace_id="mb_water_feed",
                title="Water feed",
                formula="n_H2O,feed = Excess * n_EO,feed",
                substitutions={"Excess": f"{reaction_system.excess_ratio:.1f}", "n_EO,feed": f"{eo_feed_kmol_hr:.6f}"},
                result=f"{water_feed_kmol_hr:.6f}",
                units="kmol/h",
            ),
        ]

        streams = [
            StreamRecord(
                stream_id="S-101",
                description="Ethylene oxide feed",
                temperature_c=25.0,
                pressure_bar=8.0,
                components=[StreamComponentFlow(name=eo.name, formula=eo.formula, mass_flow_kg_hr=round(eo_feed_mass_kg_hr, 3), molar_flow_kmol_hr=round(eo_feed_kmol_hr, 6))],
            ),
            StreamRecord(
                stream_id="S-102",
                description="Process water feed",
                temperature_c=30.0,
                pressure_bar=8.0,
                components=[StreamComponentFlow(name=water.name, formula=water.formula, mass_flow_kg_hr=round(water_feed_mass_kg_hr, 3), molar_flow_kmol_hr=round(water_feed_kmol_hr, 6))],
            ),
            StreamRecord(
                stream_id="S-201",
                description="Hydrator outlet",
                temperature_c=route.operating_temperature_c,
                pressure_bar=route.operating_pressure_bar,
                components=[
                    StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_kg_hr, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6)),
                    StreamComponentFlow(name="Diethylene glycol", formula="C4H10O3", mass_flow_kg_hr=round(deg_mass_kg_hr, 3), molar_flow_kmol_hr=round(deg_mol_hr, 6)),
                    StreamComponentFlow(name=eo.name, formula=eo.formula, mass_flow_kg_hr=round(eo_unreacted_mass_kg_hr, 3), molar_flow_kmol_hr=round(eo_unreacted_kmol_hr, 6)),
                    StreamComponentFlow(name=water.name, formula=water.formula, mass_flow_kg_hr=round(water_recovered_mass_kg_hr, 3), molar_flow_kmol_hr=round(water_recovered_kmol_hr, 6)),
                ],
            ),
            StreamRecord(
                stream_id="S-301",
                description="Column feed after EO flash",
                temperature_c=110.0,
                pressure_bar=1.5,
                components=[
                    StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_kg_hr, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6)),
                    StreamComponentFlow(name="Diethylene glycol", formula="C4H10O3", mass_flow_kg_hr=round(deg_mass_kg_hr, 3), molar_flow_kmol_hr=round(deg_mol_hr, 6)),
                    StreamComponentFlow(name=water.name, formula=water.formula, mass_flow_kg_hr=round(water_recovered_mass_kg_hr, 3), molar_flow_kmol_hr=round(water_recovered_kmol_hr, 6)),
                ],
            ),
            StreamRecord(
                stream_id="S-401",
                description="Monoethylene glycol product",
                temperature_c=40.0,
                pressure_bar=1.1,
                components=[StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_kg_hr, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6))],
            ),
            StreamRecord(
                stream_id="S-402",
                description="Heavy glycol bottoms",
                temperature_c=150.0,
                pressure_bar=0.3,
                components=[StreamComponentFlow(name="Diethylene glycol", formula="C4H10O3", mass_flow_kg_hr=round(deg_mass_kg_hr, 3), molar_flow_kmol_hr=round(deg_mol_hr, 6))],
            ),
            StreamRecord(
                stream_id="S-403",
                description="Recovered process water",
                temperature_c=90.0,
                pressure_bar=1.1,
                components=[StreamComponentFlow(name=water.name, formula=water.formula, mass_flow_kg_hr=round(water_recovered_mass_kg_hr, 3), molar_flow_kmol_hr=round(water_recovered_kmol_hr, 6))],
            ),
            StreamRecord(
                stream_id="S-404",
                description="EO flash purge",
                temperature_c=35.0,
                pressure_bar=1.0,
                components=[StreamComponentFlow(name=eo.name, formula=eo.formula, mass_flow_kg_hr=round(eo_unreacted_mass_kg_hr, 3), molar_flow_kmol_hr=round(eo_unreacted_kmol_hr, 6))],
            ),
        ]
        return StreamTable(
            streams=streams,
            closure_error_pct=round(closure_error_pct, 6),
            calc_traces=traces,
            value_records=[
                make_value_record("stream_product_mass_flow", "Product mass flow", product_mass_kg_hr, "kg/h", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("stream_eo_feed_kmol", "EO feed rate", eo_feed_kmol_hr, "kmol/h", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("stream_water_feed_kmol", "Water feed rate", water_feed_kmol_hr, "kmol/h", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("stream_closure_error", "Mass-balance closure error", closure_error_pct, "%", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            ],
            citations=citations,
            assumptions=assumptions + ["Heavy glycol side-product is represented as DEG for closure and preliminary purification sizing."],
        )

    product = _participant(route, "product")
    reactants = [participant for participant in route.participants if participant.role == "reactant"]
    product_mass_flow = hourly_output_kg(basis)
    product_kmol_hr = product_mass_flow / product.molecular_weight_g_mol
    extent_kmol_hr = product_kmol_hr / max(route.yield_fraction, 0.01)
    feed_components: list[StreamComponentFlow] = []
    total_feed_mass = 0.0
    for reactant in reactants:
        molar = reactant.coefficient * extent_kmol_hr
        mass = molar * reactant.molecular_weight_g_mol
        total_feed_mass += mass
        feed_components.append(
            StreamComponentFlow(
                name=reactant.name,
                formula=reactant.formula,
                mass_flow_kg_hr=round(mass, 3),
                molar_flow_kmol_hr=round(molar, 6),
            )
        )
    waste_mass = max(total_feed_mass - product_mass_flow, 0.0)
    waste_kmol = waste_mass / max(product.molecular_weight_g_mol, 1.0)
    streams = [
        StreamRecord(stream_id="S-101", description="Combined reactant feed", temperature_c=25.0, pressure_bar=1.0, components=feed_components),
        StreamRecord(
            stream_id="S-201",
            description="Reactor outlet",
            temperature_c=route.operating_temperature_c,
            pressure_bar=route.operating_pressure_bar,
            components=[
                StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_flow, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6)),
                StreamComponentFlow(name="Unreacted feed and byproducts", mass_flow_kg_hr=round(waste_mass, 3), molar_flow_kmol_hr=round(waste_kmol, 6)),
            ],
        ),
        StreamRecord(stream_id="S-301", description="Final product stream", temperature_c=40.0, pressure_bar=1.0, components=[StreamComponentFlow(name=product.name, formula=product.formula, mass_flow_kg_hr=round(product_mass_flow, 3), molar_flow_kmol_hr=round(product_kmol_hr, 6))]),
        StreamRecord(stream_id="S-401", description="Waste and purge stream", temperature_c=35.0, pressure_bar=1.0, components=[StreamComponentFlow(name="Unreacted feed and byproducts", mass_flow_kg_hr=round(waste_mass, 3), molar_flow_kmol_hr=round(waste_kmol, 6))]),
    ]
    closure_error_pct = 0.0 if total_feed_mass == 0 else abs(total_feed_mass - (product_mass_flow + waste_mass)) / total_feed_mass * 100.0
    return StreamTable(
        streams=streams,
        closure_error_pct=round(closure_error_pct, 6),
        value_records=[
            make_value_record("stream_product_mass_flow", "Product mass flow", product_mass_flow, "kg/h", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("stream_total_feed_mass", "Total feed mass flow", total_feed_mass, "kg/h", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("stream_closure_error", "Mass-balance closure error", closure_error_pct, "%", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions,
    )


def build_energy_balance(
    route: RouteOption,
    stream_table: StreamTable,
    thermo: ThermoAssessmentArtifact,
    mixture_properties: MixturePropertyArtifact | None = None,
) -> EnergyBalance:
    return build_energy_balance_generic(route, stream_table, thermo, mixture_properties)

    if route.route_id == "eo_hydration":
        eo_feed = next(stream for stream in stream_table.streams if stream.stream_id == "S-101")
        water_feed = next(stream for stream in stream_table.streams if stream.stream_id == "S-102")
        reactor_out = next(stream for stream in stream_table.streams if stream.stream_id == "S-201")
        product_stream = next(stream for stream in stream_table.streams if stream.stream_id == "S-401")
        water_recycle = next(stream for stream in stream_table.streams if stream.stream_id == "S-403")

        eo_mass = sum(component.mass_flow_kg_hr for component in eo_feed.components)
        water_mass = sum(component.mass_flow_kg_hr for component in water_feed.components)
        product_mass = sum(component.mass_flow_kg_hr for component in product_stream.components)
        recovered_water_mass = sum(component.mass_flow_kg_hr for component in water_recycle.components)
        product_kmol_hr = sum(component.molar_flow_kmol_hr for component in product_stream.components)

        preheat_eo_kw = sensible_duty_kw(eo_mass, 2.25, max(route.operating_temperature_c - 25.0, 0.0))
        preheat_water_kw = sensible_duty_kw(water_mass, 4.18, max(route.operating_temperature_c - 30.0, 0.0))
        reaction_kw = abs(product_kmol_hr * 1000.0 * thermo.estimated_reaction_enthalpy_kj_per_mol / 3600.0)
        dehydration_reboiler_kw = latent_duty_kw(recovered_water_mass * 0.55, 2200.0)
        dehydration_condenser_kw = dehydration_reboiler_kw * 0.92
        product_cooler_kw = sensible_duty_kw(product_mass, 2.8, max(reactor_out.temperature_c - product_stream.temperature_c, 0.0))

        duties = [
            UnitDuty(unit_id="E-101", heating_kw=round(preheat_eo_kw + preheat_water_kw, 3), cooling_kw=0.0, notes="Combined EO and water preheat to reactor inlet conditions."),
            UnitDuty(unit_id="R-102", heating_kw=0.0, cooling_kw=round(reaction_kw, 3), notes="Hydrator heat-removal duty for exothermic EO hydration."),
            UnitDuty(unit_id="D-101", heating_kw=round(dehydration_reboiler_kw, 3), cooling_kw=round(dehydration_condenser_kw, 3), notes="Primary dehydration / MEG concentration duty."),
            UnitDuty(unit_id="E-201", heating_kw=0.0, cooling_kw=round(product_cooler_kw, 3), notes="Final product cooling before storage."),
        ]
        traces = [
            CalcTrace(
                trace_id="eb_preheat",
                title="Feed preheat duty",
                formula="Q = m * Cp * dT / 3600",
                substitutions={"m_total": f"{eo_mass + water_mass:.3f} kg/h", "Cp_mix": "weighted EO/water average", "dT": f"{max(route.operating_temperature_c - 25.0, 0.0):.1f} K"},
                result=f"{preheat_eo_kw + preheat_water_kw:.3f}",
                units="kW",
            ),
            CalcTrace(
                trace_id="eb_rxn",
                title="Reaction heat release",
                formula="Q_rxn = |n_MEG * dH_rxn| / 3600",
                substitutions={"n_MEG": f"{product_kmol_hr:.6f} kmol/h", "dH_rxn": f"{thermo.estimated_reaction_enthalpy_kj_per_mol:.3f} kJ/mol"},
                result=f"{reaction_kw:.3f}",
                units="kW",
            ),
            CalcTrace(
                trace_id="eb_d101",
                title="D-101 reboiler duty",
                formula="Q = m_evap * latent_heat / 3600",
                substitutions={"m_evap": f"{recovered_water_mass * 0.55:.3f} kg/h", "latent_heat": "2200 kJ/kg"},
                result=f"{dehydration_reboiler_kw:.3f}",
                units="kW",
            ),
        ]
        return EnergyBalance(
            duties=duties,
            total_heating_kw=round(sum(item.heating_kw for item in duties), 3),
            total_cooling_kw=round(sum(item.cooling_kw for item in duties), 3),
            calc_traces=traces,
            value_records=[
                make_value_record("energy_total_heating", "Total heating duty", sum(item.heating_kw for item in duties), "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("energy_total_cooling", "Total cooling duty", sum(item.cooling_kw for item in duties), "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
                make_value_record("energy_reaction_release", "Reaction heat release", reaction_kw, "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
            ],
            citations=thermo.citations,
            assumptions=thermo.assumptions + ["Dehydration duty assumes 55% of recovered water is vaporized in the principal concentration step for preliminary sizing."],
        )

    feed_stream = next(stream for stream in stream_table.streams if stream.stream_id == "S-101")
    feed_mass = sum(component.mass_flow_kg_hr for component in feed_stream.components)
    preheat_kw = sensible_duty_kw(feed_mass, cp_kj_kg_k=2.2, delta_t_k=max(route.operating_temperature_c - 25.0, 0.0))
    product_component = next(component for component in next(stream for stream in stream_table.streams if stream.stream_id == "S-301").components)
    reaction_kw = abs(product_component.molar_flow_kmol_hr * 1000.0 * thermo.estimated_reaction_enthalpy_kj_per_mol / 3600.0)
    cooling_kw = reaction_kw if thermo.estimated_reaction_enthalpy_kj_per_mol < 0 else 0.0
    heating_kw = preheat_kw if thermo.estimated_reaction_enthalpy_kj_per_mol <= 0 else preheat_kw + reaction_kw
    duties = [
        UnitDuty(unit_id="R-101", heating_kw=round(preheat_kw, 3), cooling_kw=round(cooling_kw, 3), notes="Feed preheat and reaction heat management."),
        UnitDuty(unit_id="E-201", heating_kw=0.0, cooling_kw=round(max(cooling_kw * 0.25, 5.0), 3), notes="Product cooling and condensation duty."),
    ]
    return EnergyBalance(
        duties=duties,
        total_heating_kw=round(heating_kw, 3),
        total_cooling_kw=round(sum(item.cooling_kw for item in duties), 3),
        value_records=[
            make_value_record("energy_total_heating", "Total heating duty", heating_kw, "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("energy_total_cooling", "Total cooling duty", sum(item.cooling_kw for item in duties), "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=thermo.citations,
        assumptions=thermo.assumptions + ["Average liquid heat capacity assumed as 2.2 kJ/kg-K for preheat estimation."],
    )


def build_reactor_design(
    basis: ProjectBasis,
    route: RouteOption,
    reaction_system: ReactionSystem,
    stream_table: StreamTable,
    energy_balance: EnergyBalance,
    mixture_properties: MixturePropertyArtifact | None = None,
    reactor_choice: DecisionRecord | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    kinetics: KineticAssessmentArtifact | None = None,
) -> ReactorDesign:
    return build_reactor_design_generic(
        basis,
        route,
        reaction_system,
        stream_table,
        energy_balance,
        mixture_properties,
        reactor_choice,
        utility_architecture,
        kinetics,
    )

    feed_mass = sum(sum(component.mass_flow_kg_hr for component in stream.components) for stream in stream_table.streams if stream.stream_id in {"S-101", "S-102"})
    density = 1030.0 if route.route_id == "eo_hydration" else 950.0
    volumetric_flow_m3_hr = max(feed_mass / density, 0.1)
    liquid_holdup_m3 = volumetric_flow_m3_hr * route.residence_time_hr
    design_volume_m3 = liquid_holdup_m3 * 1.2
    reactor_duty_kw = max((duty.cooling_kw for duty in energy_balance.duties if duty.unit_id.startswith("R-")), default=energy_balance.total_cooling_kw)
    heat_transfer_area_m2 = max((reactor_duty_kw * 1000.0) / (700.0 * 25.0), 1.0)
    traces = [
        CalcTrace(
            trace_id="rd_holdup",
            title="Reactor liquid holdup",
            formula="V_holdup = Qv * tau",
            substitutions={"Qv": f"{volumetric_flow_m3_hr:.3f} m3/h", "tau": f"{route.residence_time_hr:.3f} h"},
            result=f"{liquid_holdup_m3:.3f}",
            units="m3",
        ),
        CalcTrace(
            trace_id="rd_design_volume",
            title="Reactor design volume",
            formula="V_design = 1.2 * V_holdup",
            substitutions={"V_holdup": f"{liquid_holdup_m3:.3f} m3"},
            result=f"{design_volume_m3:.3f}",
            units="m3",
        ),
        CalcTrace(
            trace_id="rd_area",
            title="Heat transfer area",
            formula="A = Q / (U * dTlm)",
            substitutions={"Q": f"{reactor_duty_kw * 1000.0:.3f} W", "U": "700 W/m2-K", "dTlm": "25 K"},
            result=f"{heat_transfer_area_m2:.3f}",
            units="m2",
        ),
    ]
    return ReactorDesign(
        reactor_id="R-102" if route.route_id == "eo_hydration" else "R-101",
        reactor_type="Plug-flow hydrator" if route.route_id == "eo_hydration" else "Jacketed stirred reactor",
        design_basis=f"{route.residence_time_hr:.2f} h residence time at {route.operating_temperature_c:.1f} C with conversion {reaction_system.conversion_fraction:.3f}",
        residence_time_hr=route.residence_time_hr,
        liquid_holdup_m3=round(liquid_holdup_m3, 3),
        design_volume_m3=round(design_volume_m3, 3),
        design_temperature_c=round(route.operating_temperature_c + 20.0, 1),
        design_pressure_bar=round(max(route.operating_pressure_bar + 3.0, 4.0), 2),
        heat_duty_kw=round(reactor_duty_kw, 3),
        heat_transfer_area_m2=round(heat_transfer_area_m2, 3),
        calc_traces=traces,
        value_records=[
            make_value_record("reactor_liquid_holdup", "Reactor liquid holdup", liquid_holdup_m3, "m3", citations=route.citations + reaction_system.citations, assumptions=route.assumptions + reaction_system.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("reactor_design_volume", "Reactor design volume", design_volume_m3, "m3", citations=route.citations + reaction_system.citations, assumptions=route.assumptions + reaction_system.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("reactor_heat_duty", "Reactor heat duty", reactor_duty_kw, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("reactor_heat_transfer_area", "Reactor heat-transfer area", heat_transfer_area_m2, "m2", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=sorted(set(route.citations + reaction_system.citations + energy_balance.citations)),
        assumptions=route.assumptions + reaction_system.assumptions + energy_balance.assumptions + ["Liquid density estimated from dilute aqueous glycol service."],
    )


def build_column_design(
    basis: ProjectBasis,
    route: RouteOption,
    stream_table: StreamTable,
    energy_balance: EnergyBalance,
    mixture_properties: MixturePropertyArtifact | None = None,
    separation_choice: DecisionRecord | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    separation_thermo: SeparationThermoArtifact | None = None,
    property_packages: PropertyPackageArtifact | None = None,
) -> ColumnDesign:
    return build_column_design_generic(
        basis,
        route,
        stream_table,
        energy_balance,
        mixture_properties,
        separation_choice,
        utility_architecture,
        separation_thermo,
        property_packages,
    )

    column_feed = next(stream for stream in stream_table.streams if stream.stream_id in {"S-301", "S-201"})
    total_mass = sum(component.mass_flow_kg_hr for component in column_feed.components)
    meg_mass = sum(component.mass_flow_kg_hr for component in column_feed.components if "glycol" in component.name.lower() and "diethylene" not in component.name.lower())
    x_f = min(max(meg_mass / max(total_mass, 1.0), 0.05), 0.95)
    x_d = min(max(basis.target_purity_wt_pct / 100.0, 0.9), 0.999)
    x_b = 0.05
    relative_volatility = 2.2 if route.route_id == "eo_hydration" else 1.8
    min_stages = math.log((x_d / (1.0 - x_d)) * ((1.0 - x_b) / x_b)) / math.log(relative_volatility)
    min_stages = max(min_stages, 3.0)
    r_min = max((x_d - x_f) / max(relative_volatility - 1.0, 0.2), 0.4)
    reflux_ratio = r_min * 1.35 + 0.4
    design_stages = max(math.ceil(min_stages * 1.6 + 6), 10)
    reboiler_kw = max((duty.heating_kw for duty in energy_balance.duties if duty.unit_id == "D-101"), default=energy_balance.total_heating_kw * 0.6)
    condenser_kw = max((duty.cooling_kw for duty in energy_balance.duties if duty.unit_id == "D-101"), default=energy_balance.total_cooling_kw * 0.5)
    vapor_mass_kg_hr = max(reboiler_kw * 3600.0 / 2257.0, 1000.0)
    vapor_density = 1.6 if route.route_id == "eo_hydration" else 2.0
    allowable_velocity = 1.1
    area_m2 = vapor_mass_kg_hr / (3600.0 * vapor_density * allowable_velocity * 0.75)
    diameter_m = math.sqrt(max(4.0 * area_m2 / math.pi, 0.05))
    height_m = design_stages * 0.75 + 4.0
    traces = [
        CalcTrace(
            trace_id="cd_fenske",
            title="Minimum theoretical stages",
            formula="Nmin = ln[(xD/(1-xD))*((1-xB)/xB)] / ln(alpha)",
            substitutions={"xD": f"{x_d:.4f}", "xB": f"{x_b:.4f}", "alpha": f"{relative_volatility:.3f}"},
            result=f"{min_stages:.3f}",
            units="stages",
        ),
        CalcTrace(
            trace_id="cd_design_stages",
            title="Design stages",
            formula="N = ceil(1.6 * Nmin + 6)",
            substitutions={"Nmin": f"{min_stages:.3f}"},
            result=f"{design_stages:d}",
            units="stages",
        ),
        CalcTrace(
            trace_id="cd_diameter",
            title="Column diameter",
            formula="D = sqrt(4A/pi)",
            substitutions={"A": f"{area_m2:.3f} m2"},
            result=f"{diameter_m:.3f}",
            units="m",
        ),
    ]
    return ColumnDesign(
        column_id="D-101",
        service="MEG purification and dehydration" if route.route_id == "eo_hydration" else "Primary product purification",
        light_key="Water" if route.route_id == "eo_hydration" else "Light component",
        heavy_key="Monoethylene glycol" if route.route_id == "eo_hydration" else "Heavy component",
        relative_volatility=round(relative_volatility, 3),
        min_stages=round(min_stages, 3),
        design_stages=design_stages,
        reflux_ratio=round(reflux_ratio, 3),
        column_diameter_m=round(diameter_m, 3),
        column_height_m=round(height_m, 3),
        condenser_duty_kw=round(condenser_kw, 3),
        reboiler_duty_kw=round(reboiler_kw, 3),
        calc_traces=traces,
        value_records=[
            make_value_record("column_relative_volatility", "Relative volatility", relative_volatility, "ratio", citations=route.citations + stream_table.citations, assumptions=route.assumptions + stream_table.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("column_design_stages", "Design stages", design_stages, "stages", citations=route.citations + stream_table.citations, assumptions=route.assumptions + stream_table.assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("column_diameter", "Column diameter", diameter_m, "m", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("column_reboiler_duty", "Column reboiler duty", reboiler_kw, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=sorted(set(route.citations + stream_table.citations + energy_balance.citations)),
        assumptions=route.assumptions + stream_table.assumptions + energy_balance.assumptions + ["Column sizing uses Fenske-style minimum stages and a conservative tray efficiency allowance."],
    )


def build_heat_exchanger_design(
    route: RouteOption,
    energy_balance: EnergyBalance,
    exchanger_choice: DecisionRecord | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> HeatExchangerDesign:
    return build_heat_exchanger_design_generic(route, energy_balance, exchanger_choice, utility_architecture)

    preheater = next((duty for duty in energy_balance.duties if duty.unit_id == "E-101"), None)
    if preheater is None:
        heat_load_kw = max(energy_balance.total_heating_kw, 100.0)
        service = "Generic feed preheat"
    else:
        heat_load_kw = preheater.heating_kw or preheater.cooling_kw
        service = preheater.notes
    lmtd_k = 32.0 if route.route_id == "eo_hydration" else 28.0
    overall_u = 550.0
    area_m2 = max(heat_load_kw * 1000.0 / (overall_u * lmtd_k), 1.0)
    traces = [
        CalcTrace(
            trace_id="hx_area",
            title="Heat exchanger area",
            formula="A = Q / (U * dTlm)",
            substitutions={"Q": f"{heat_load_kw * 1000.0:.3f} W", "U": f"{overall_u:.1f} W/m2-K", "dTlm": f"{lmtd_k:.1f} K"},
            result=f"{area_m2:.3f}",
            units="m2",
        )
    ]
    return HeatExchangerDesign(
        exchanger_id="E-101",
        service=service,
        heat_load_kw=round(heat_load_kw, 3),
        lmtd_k=lmtd_k,
        overall_u_w_m2_k=overall_u,
        area_m2=round(area_m2, 3),
        calc_traces=traces,
        value_records=[
            make_value_record("hx_heat_load", "Heat-exchanger heat load", heat_load_kw, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("hx_lmtd", "LMTD", lmtd_k, "K", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("hx_area", "Heat-exchanger area", area_m2, "m2", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=energy_balance.citations,
        assumptions=energy_balance.assumptions + ["Overall U assumes shell-and-tube preheat service with aqueous-organic process fluid."],
    )


def build_storage_design(
    basis: ProjectBasis,
    product_density_kg_m3: float,
    citations: list[str],
    assumptions: list[str],
    storage_choice: DecisionRecord | None = None,
    operations_planning: OperationsPlanningArtifact | None = None,
) -> StorageDesign:
    return build_storage_design_generic(basis, product_density_kg_m3, citations, assumptions, storage_choice, operations_planning)

    inventory_days = 7.0 if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA else 3.0
    working_volume_m3 = hourly_output_kg(basis) * inventory_days * 24.0 / product_density_kg_m3
    total_volume_m3 = working_volume_m3 * 1.1
    traces = [
        CalcTrace(
            trace_id="sd_volume",
            title="Storage tank working volume",
            formula="V = m * days * 24 / density",
            substitutions={"m": f"{hourly_output_kg(basis):.3f} kg/h", "days": f"{inventory_days:.1f}", "density": f"{product_density_kg_m3:.1f} kg/m3"},
            result=f"{working_volume_m3:.3f}",
            units="m3",
        )
    ]
    return StorageDesign(
        storage_id="TK-301",
        service=f"{basis.target_product} product storage",
        inventory_days=inventory_days,
        working_volume_m3=round(working_volume_m3, 3),
        total_volume_m3=round(total_volume_m3, 3),
        material_of_construction="SS304",
        calc_traces=traces,
        value_records=[
            make_value_record("storage_inventory_days", "Finished-product inventory days", inventory_days, "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("storage_working_volume", "Storage working volume", working_volume_m3, "m3", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("storage_total_volume", "Storage total volume", total_volume_m3, "m3", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=citations,
        assumptions=assumptions + ["Finished-product storage sized for dispatch buffering and weekly scheduling."],
    )


def build_equipment_list(
    route: RouteOption,
    reactor: ReactorDesign,
    column: ColumnDesign,
    exchanger: HeatExchangerDesign,
    storage: StorageDesign,
    energy_balance: EnergyBalance,
    moc_decision: DecisionRecord | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> list[EquipmentSpec]:
    return build_equipment_list_generic(route, reactor, column, exchanger, storage, energy_balance, moc_decision, utility_architecture)

    flash_volume = max(reactor.design_volume_m3 * 0.12, 5.0) if route.route_id == "eo_hydration" else max(reactor.design_volume_m3 * 0.3, 1.0)
    return [
        EquipmentSpec(
            equipment_id=reactor.reactor_id,
            equipment_type="Reactor",
            service="Ethylene oxide hydration" if route.route_id == "eo_hydration" else f"Primary synthesis of {route.name}",
            design_basis=reactor.design_basis,
            volume_m3=reactor.design_volume_m3,
            design_temperature_c=reactor.design_temperature_c,
            design_pressure_bar=reactor.design_pressure_bar,
            material_of_construction="SS316L",
            duty_kw=reactor.heat_duty_kw,
            notes="Preliminary process reactor sizing with heat-removal allowance.",
            citations=reactor.citations,
            assumptions=reactor.assumptions,
        ),
        EquipmentSpec(
            equipment_id=column.column_id,
            equipment_type="Distillation column",
            service=column.service,
            design_basis=f"{column.design_stages} stages at reflux ratio {column.reflux_ratio:.2f}",
            volume_m3=round(math.pi * (column.column_diameter_m / 2.0) ** 2 * column.column_height_m, 3),
            design_temperature_c=205.0 if route.route_id == "eo_hydration" else 140.0,
            design_pressure_bar=1.5 if route.route_id == "eo_hydration" else 2.0,
            material_of_construction="SS316L",
            duty_kw=column.reboiler_duty_kw,
            notes="Preliminary vacuum-column envelope from tray-count and vapor-load basis.",
            citations=column.citations,
            assumptions=column.assumptions,
        ),
        EquipmentSpec(
            equipment_id="V-101",
            equipment_type="Flash drum",
            service="EO flash and vapor disengagement" if route.route_id == "eo_hydration" else "Primary phase disengagement",
            design_basis="0.12x reactor volume hold-up" if route.route_id == "eo_hydration" else "0.30x reactor volume hold-up",
            volume_m3=round(flash_volume, 3),
            design_temperature_c=80.0,
            design_pressure_bar=3.0 if route.route_id == "eo_hydration" else 2.0,
            material_of_construction="SS316L",
            notes="Provides vapor disengagement upstream of purification and recycle handling.",
            citations=reactor.citations,
            assumptions=reactor.assumptions,
        ),
        EquipmentSpec(
            equipment_id=exchanger.exchanger_id,
            equipment_type="Heat exchanger",
            service=exchanger.service,
            design_basis=f"LMTD {exchanger.lmtd_k:.1f} K, U {exchanger.overall_u_w_m2_k:.1f} W/m2-K",
            volume_m3=round(exchanger.area_m2 * 0.08, 3),
            design_temperature_c=200.0 if route.route_id == "eo_hydration" else 120.0,
            design_pressure_bar=10.0 if route.route_id == "eo_hydration" else 3.0,
            material_of_construction="SS316L",
            duty_kw=exchanger.heat_load_kw,
            notes="Shell-and-tube basis used for preliminary exchanger sizing.",
            citations=exchanger.citations,
            assumptions=exchanger.assumptions,
        ),
        EquipmentSpec(
            equipment_id=storage.storage_id,
            equipment_type="Storage tank",
            service=storage.service,
            design_basis=f"{storage.inventory_days:.1f} days inventory",
            volume_m3=storage.total_volume_m3,
            design_temperature_c=50.0,
            design_pressure_bar=1.2,
            material_of_construction=storage.material_of_construction,
            notes="Product storage with nitrogen blanketing provision.",
            citations=storage.citations,
            assumptions=storage.assumptions,
        ),
    ]


def build_utility_basis(basis: ProjectBasis, citations: list[str], assumptions: list[str]) -> UtilityBasis:
    traces = [
        CalcTrace(trace_id="ub_steam_cost", title="Steam tariff basis", formula="Steam cost = 1.80 INR/kg", result="1.80", units="INR/kg"),
        CalcTrace(trace_id="ub_cw_cost", title="Cooling water tariff basis", formula="CW cost = 8.00 INR/m3", result="8.00", units="INR/m3"),
        CalcTrace(trace_id="ub_power_cost", title="Power tariff basis", formula="Power cost = 8.50 INR/kWh", result="8.50", units="INR/kWh"),
    ]
    return UtilityBasis(
        steam_pressure_bar=20.0,
        steam_cost_inr_per_kg=1.8,
        cooling_water_cost_inr_per_m3=8.0,
        power_cost_inr_per_kwh=8.5,
        calc_traces=traces,
        value_records=[
            make_value_record("utility_steam_pressure", "Steam pressure", 20.0, "bar", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("utility_steam_cost", "Steam cost", 1.8, "INR/kg", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("utility_cw_cost", "Cooling-water cost", 8.0, "INR/m3", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("utility_power_cost", "Power cost", 8.5, "INR/kWh", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + [f"Utility tariffs normalized to {basis.utility_basis_year} India basis."],
    )


def compute_utilities(
    basis: ProjectBasis,
    energy_balance: EnergyBalance,
    equipment: list[EquipmentSpec],
    utility_basis: UtilityBasis,
    citations: list[str],
    assumptions: list[str],
    utility_network_decision: UtilityNetworkDecision | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    column_design: ColumnDesign | None = None,
) -> UtilitySummaryArtifact:
    selected_case = _selected_utility_case(utility_network_decision)
    selected_train_steps = utility_architecture.architecture.selected_train_steps if utility_architecture is not None else []
    selected_package_items = utility_architecture.architecture.selected_package_items if utility_architecture is not None else []
    effective_heating_kw = selected_case.residual_hot_utility_kw if selected_case else energy_balance.total_heating_kw
    effective_cooling_kw = selected_case.residual_cold_utility_kw if selected_case else energy_balance.total_cooling_kw
    major_volume = sum(item.volume_m3 for item in equipment if item.equipment_type in {"Reactor", "Distillation column", "Flash drum"})
    electrical_kw = max(major_volume * 0.9, 35.0) + pump_power_kw(flow_m3_hr=hourly_output_kg(basis) / 1100.0, head_m=45.0)
    if selected_case and selected_case.case_id.endswith("pinch_htm"):
        electrical_kw += max(selected_case.recovered_duty_kw / 3500.0, 15.0)
    train_aux_power_kw = 0.0
    if selected_package_items:
        train_aux_power_kw += sum(item.power_kw for item in selected_package_items)
        train_aux_power_kw += len([item for item in selected_package_items if item.package_role == "controls"]) * 0.35
    elif selected_train_steps:
        direct_steps = [step for step in selected_train_steps if step.medium.lower() == "direct"]
        indirect_steps = [step for step in selected_train_steps if step.medium.lower() != "direct"]
        train_aux_power_kw += len(direct_steps) * 1.5
        train_aux_power_kw += len(indirect_steps) * 4.5 + sum(step.recovered_duty_kw for step in indirect_steps) / 5000.0
    if train_aux_power_kw > 0.0:
        electrical_kw += train_aux_power_kw
    transport_loads: list[UtilityLoad] = []
    if column_design is not None and "distillation" in column_design.service.lower():
        effective_heating_kw = max(effective_heating_kw, column_design.reboiler_duty_kw)
        effective_cooling_kw = max(effective_cooling_kw, column_design.condenser_duty_kw)
        reflux_pump_kw = max(column_design.reflux_ratio * max(column_design.rectifying_liquid_load_m3_hr, column_design.liquid_load_m3_hr * 0.45) / 18.0, 0.0)
        if reflux_pump_kw > 0.0:
            electrical_kw += reflux_pump_kw
            transport_loads.append(
                UtilityLoad(
                    utility_id="UT-DIST-REFLUX",
                    utility_type="Electricity - distillation reflux circulation",
                    load=round(reflux_pump_kw, 3),
                    units="kW",
                    basis="Column reflux circulation power tied to the duty-adjusted liquid load and selected reflux ratio.",
                    citations=citations,
                    assumptions=assumptions,
                )
            )
    steam_kg_hr = effective_heating_kw * 3600.0 / 2200.0
    cooling_water_m3_hr = effective_cooling_kw * 3600.0 / (4.18 * 10.0 * 1000.0)
    if column_design is not None and "absorption" in column_design.service.lower():
        absorber_area_m2 = math.pi * (column_design.column_diameter_m / 2.0) ** 2 * max(1.0 - column_design.downcomer_area_fraction, 0.25)
        absorber_gas_q_m3_s = absorber_area_m2 * max(column_design.absorber_operating_velocity_m_s, 0.1)
        packing_family_factor = 1.10 if column_design.absorber_packing_family.startswith("structured") else 0.96
        absorber_window_factor = (
            1.0
            + max(0.20 - column_design.absorber_flooding_margin_fraction, 0.0) * 1.40
            + max(1.0 - column_design.absorber_wetting_ratio, 0.0) * 0.20
        )
        absorber_hydraulic_power_kw = max(
            column_design.absorber_total_pressure_drop_kpa * absorber_gas_q_m3_s / 0.62 * packing_family_factor * absorber_window_factor,
            0.0,
        )
        if absorber_hydraulic_power_kw > 0.0:
            electrical_kw += absorber_hydraulic_power_kw
            transport_loads.append(
                UtilityLoad(
                    utility_id="UT-ABS-HYD",
                    utility_type="Electricity - absorber hydraulics",
                    load=round(absorber_hydraulic_power_kw, 3),
                    units="kW",
                    basis=(
                        "Packed-bed pressure-drop penalty and gas handling power from absorber transport screening, "
                        f"including {column_design.absorber_packing_family} packing-family and operating-window factors"
                    ),
                    citations=citations,
                    assumptions=assumptions,
                )
            )
    if column_design is not None and "crystallizer" in column_design.service.lower():
        classifier_kw = max(
            column_design.slurry_circulation_rate_m3_hr
            * 0.10
            * (
                1.0
                + max(0.30 - column_design.crystal_classifier_cut_size_mm, 0.0) / 0.30 * 0.30
                + max(column_design.crystal_classified_product_fraction - 0.75, 0.0) * 0.20
            ),
            0.0,
        )
        filter_kw = max(
            (column_design.filter_specific_cake_resistance_m_kg / 1.5e9)
            * (1.0 + min(column_design.filter_medium_resistance_1_m / 5.0e10, 2.0) * 0.20),
            0.0,
        )
        dryer_fan_kw = max(
            column_design.dryer_dry_air_flow_kg_hr
            / 9000.0
            * (1.0 + column_design.dryer_exhaust_saturation_fraction)
            * (
                1.0
                + max(
                    column_design.dryer_exhaust_humidity_ratio_kg_kg - column_design.dryer_inlet_humidity_ratio_kg_kg,
                    0.0,
                )
                / 0.06
                * 0.15
            ),
            0.0,
        )
        solids_aux_power_kw = classifier_kw + filter_kw + dryer_fan_kw
        dryer_endpoint_heat_kw = max(
            column_design.dryer_refined_duty_kw
            * (
                0.18
                * max(
                    column_design.dryer_target_moisture_fraction - column_design.dryer_equilibrium_moisture_fraction,
                    0.0,
                )
                / max(column_design.dryer_target_moisture_fraction, 1e-6)
                + 0.08 * max(column_design.dryer_exhaust_saturation_fraction - 0.60, 0.0)
            ),
            0.0,
        )
        if solids_aux_power_kw > 0.0:
            electrical_kw += solids_aux_power_kw
            transport_loads.append(
                UtilityLoad(
                    utility_id="UT-SOLIDS-AUX",
                    utility_type="Electricity - solids auxiliaries",
                    load=round(solids_aux_power_kw, 3),
                    units="kW",
                    basis=(
                        "Classifier sharpness, filter resistance, and dryer-gas transport penalties from solids-unit screening"
                    ),
                    citations=citations,
                    assumptions=assumptions,
                )
            )
        if dryer_endpoint_heat_kw > 0.0:
            steam_penalty_kg_hr = dryer_endpoint_heat_kw * 3600.0 / 2200.0
            steam_kg_hr += steam_penalty_kg_hr
            transport_loads.append(
                UtilityLoad(
                    utility_id="UT-DRY-ENDPT",
                    utility_type="Steam - dryer endpoint penalty",
                    load=round(steam_penalty_kg_hr, 3),
                    units="kg/h",
                    basis="Dryer endpoint polish duty tied to exhaust humidity and endpoint transport screening",
                    citations=citations,
                    assumptions=assumptions,
                )
            )
    dm_water_m3_hr = max(hourly_output_kg(basis) / 25000.0, 2.0)
    nitrogen_nm3_hr = max(hourly_output_kg(basis) / 7000.0, 3.0)
    loads = [
        UtilityLoad(utility_id="UT-STEAM", utility_type="Steam", load=round(steam_kg_hr, 3), units="kg/h", basis=f"{utility_basis.steam_pressure_bar:.1f} bar saturated steam equivalent", citations=citations, assumptions=assumptions),
        UtilityLoad(utility_id="UT-CW", utility_type="Cooling water", load=round(cooling_water_m3_hr, 3), units="m3/h", basis="10 C cooling-water rise", citations=citations, assumptions=assumptions),
        UtilityLoad(utility_id="UT-POWER", utility_type="Electricity", load=round(electrical_kw, 3), units="kW", basis="Agitation, pumps, vacuum auxiliaries, and transfer drives", citations=citations, assumptions=assumptions),
        UtilityLoad(utility_id="UT-DMW", utility_type="DM water", load=round(dm_water_m3_hr, 3), units="m3/h", basis="Boiler and wash service allowance", citations=citations, assumptions=assumptions),
        UtilityLoad(utility_id="UT-N2", utility_type="Nitrogen", load=round(nitrogen_nm3_hr, 3), units="Nm3/h", basis="Inerting and blanketing", citations=citations, assumptions=assumptions),
    ]
    if train_aux_power_kw > 0.0:
        loads.append(
            UtilityLoad(
                utility_id="UT-HTM-AUX",
                utility_type="Heat-integration auxiliaries",
                load=round(train_aux_power_kw, 3),
                units="kW",
                basis="Selected utility train circulation, HTM pumping, and exchanger-network auxiliaries",
                citations=citations,
                assumptions=assumptions,
            )
        )
    utility_assumptions = list(assumptions)
    if selected_case:
        utility_assumptions.append(
            f"Utility loads are net of selected heat-integration case `{selected_case.case_id}` with {selected_case.recovered_duty_kw:.1f} kW recovered duty."
        )
    if selected_train_steps:
        utility_assumptions.append(
            f"Utility loads include {len(selected_train_steps)} selected train steps with {sum(step.recovered_duty_kw for step in selected_train_steps):.1f} kW packet-derived recovery basis."
        )
    if selected_package_items:
        utility_assumptions.append(
            f"Utility auxiliary power includes {len(selected_package_items)} selected package items with {sum(item.power_kw for item in selected_package_items):.1f} kW explicit package power."
        )
    if transport_loads:
        utility_assumptions.append(
            f"Process-unit transport penalties add {sum(item.load for item in transport_loads if item.utility_type.startswith('Electricity')):.1f} kW electricity and "
            f"{sum(item.load for item in transport_loads if item.utility_type.startswith('Steam')):.1f} kg/h steam equivalent."
        )
    utility_assumptions.append("Cooling water rise fixed at 10 K and steam latent heat at 2200 kJ/kg for preliminary utility sizing.")
    loads.extend(transport_loads)
    return UtilitySummaryArtifact(
        items=loads,
        utility_basis=utility_basis,
        citations=citations,
        assumptions=utility_assumptions,
        selected_heat_integration_case_id=selected_case.case_id if selected_case else None,
        recovered_duty_kw=round(selected_case.recovered_duty_kw, 3) if selected_case else 0.0,
        selected_train_step_count=len(selected_train_steps),
        selected_train_recovered_duty_kw=round(sum(step.recovered_duty_kw for step in selected_train_steps), 3),
        value_records=[
            make_value_record("utility_steam_load", "Steam load", steam_kg_hr, "kg/h", citations=citations, assumptions=utility_assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("utility_cw_load", "Cooling-water load", cooling_water_m3_hr, "m3/h", citations=citations, assumptions=utility_assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("utility_power_load", "Electrical load", electrical_kw, "kW", citations=citations, assumptions=utility_assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("utility_recovered_duty", "Recovered duty", selected_case.recovered_duty_kw if selected_case else 0.0, "kW", citations=citations, assumptions=utility_assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
    )


def _find_price(price_data: list[IndianPriceDatum], item_name: str, default: float) -> float:
    for datum in price_data:
        if datum.item_name.lower() == item_name.lower():
            return datum.value_inr
    return default


def build_cost_model(
    basis: ProjectBasis,
    equipment: list[EquipmentSpec],
    utilities: UtilitySummaryArtifact,
    stream_table: StreamTable,
    market: MarketAssessmentArtifact,
    site: SiteSelectionArtifact,
    citations: list[str],
    assumptions: list[str],
    utility_network_decision: UtilityNetworkDecision | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    scenario_policy: ScenarioPolicy | None = None,
    procurement_basis: DecisionRecord | None = None,
    logistics_basis: DecisionRecord | None = None,
    route_site_fit=None,
    route_economic_basis=None,
    column_design: ColumnDesign | None = None,
) -> CostModel:
    scenario_policy = scenario_policy or ScenarioPolicy()
    procurement_basis = procurement_basis or build_procurement_basis_decision(
        site,
        equipment,
        route_site_fit=route_site_fit,
        route_economic_basis=route_economic_basis,
    )
    logistics_basis = logistics_basis or build_logistics_basis_decision(
        site,
        market,
        route_site_fit=route_site_fit,
        route_economic_basis=route_economic_basis,
    )
    model = build_cost_model_v2(
        basis,
        equipment,
        utilities,
        stream_table,
        market,
        site,
        scenario_policy,
        citations,
        assumptions,
        procurement_basis,
        logistics_basis,
        route_site_fit=route_site_fit,
        route_economic_basis=route_economic_basis,
        utility_architecture=utility_architecture,
        column_design=column_design,
    )
    selected_case = _selected_utility_case(utility_network_decision)
    if utility_network_decision is not None:
        model.selected_route_id = utility_network_decision.route_id
        model.selected_heat_integration_case_id = selected_case.case_id if selected_case else None
        if model.integration_capex_inr <= 0.0:
            model.integration_capex_inr = round(selected_case.added_capex_inr, 2) if selected_case else 0.0
    return model

    price_data = list(market.india_price_data)
    if not price_data:
        price_data = [
            IndianPriceDatum(datum_id="eo_price", category="raw_material", item_name="Ethylene oxide", region=site.selected_site, units="INR/kg", value_inr=62.0, reference_year=basis.economic_reference_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="water_price", category="raw_material", item_name="Process water", region=site.selected_site, units="INR/kg", value_inr=0.02, reference_year=basis.economic_reference_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="labor_price", category="labor", item_name="Operating labour", region=site.selected_site, units="INR/person-year", value_inr=650000.0, reference_year=basis.economic_reference_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="power_price", category="utility", item_name="Electricity", region=site.selected_site, units="INR/kWh", value_inr=utilities.utility_basis.power_cost_inr_per_kwh if utilities.utility_basis else 8.5, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="steam_price", category="utility", item_name="Steam", region=site.selected_site, units="INR/kg", value_inr=utilities.utility_basis.steam_cost_inr_per_kg if utilities.utility_basis else 1.8, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="cw_price", category="utility", item_name="Cooling water", region=site.selected_site, units="INR/m3", value_inr=utilities.utility_basis.cooling_water_cost_inr_per_m3 if utilities.utility_basis else 8.0, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
        ]

    reactor = next(item for item in equipment if item.equipment_type == "Reactor")
    column = next(item for item in equipment if item.equipment_type == "Distillation column")
    exchanger = next(item for item in equipment if item.equipment_type == "Heat exchanger")
    storage = next(item for item in equipment if item.equipment_type == "Storage tank")

    reactor_purchase = 8_000_000.0 + reactor.volume_m3 * 600_000.0 + reactor.duty_kw * 2_000.0
    column_purchase = 12_000_000.0 + column.volume_m3 * 190_000.0 + column.duty_kw * 1_000.0
    exchanger_purchase = 1_500_000.0 + exchanger.volume_m3 * 450_000.0 + exchanger.duty_kw * 1_200.0
    storage_purchase = 3_000_000.0 + storage.volume_m3 * 110_000.0
    flash_purchase = sum(3_500_000.0 + item.volume_m3 * 150_000.0 for item in equipment if item.equipment_type == "Flash drum")
    equipment_purchase = reactor_purchase + column_purchase + exchanger_purchase + storage_purchase + flash_purchase
    selected_case = _selected_utility_case(utility_network_decision)
    integration_capex = selected_case.added_capex_inr if selected_case else 0.0
    installed_cost = equipment_purchase * 2.35
    direct_cost = installed_cost * 1.18
    indirect_cost = direct_cost * 0.22
    contingency = direct_cost * 0.10
    total_capex = direct_cost + indirect_cost + contingency + integration_capex

    annual_hours = operating_hours_per_year(basis)
    eo_stream = next((stream for stream in stream_table.streams if stream.stream_id == "S-101"), None)
    water_stream = next((stream for stream in stream_table.streams if stream.stream_id == "S-102"), None)
    eo_annual_kg = sum(component.mass_flow_kg_hr for component in eo_stream.components) * annual_hours if eo_stream else 0.0
    water_annual_kg = sum(component.mass_flow_kg_hr for component in water_stream.components) * annual_hours if water_stream else 0.0
    eo_price = _find_price(price_data, "Ethylene oxide", 62.0)
    water_price = _find_price(price_data, "Process water", 0.02)
    steam_price = _find_price(price_data, "Steam", utilities.utility_basis.steam_cost_inr_per_kg if utilities.utility_basis else 1.8)
    cw_price = _find_price(price_data, "Cooling water", utilities.utility_basis.cooling_water_cost_inr_per_m3 if utilities.utility_basis else 8.0)
    power_price = _find_price(price_data, "Electricity", utilities.utility_basis.power_cost_inr_per_kwh if utilities.utility_basis else 8.5)
    labor_price = _find_price(price_data, "Operating labour", 650000.0)

    annual_raw_material_cost = eo_annual_kg * eo_price + water_annual_kg * water_price
    steam_load = sum(load.load for load in utilities.items if load.utility_type.lower().startswith("steam"))
    cw_load = sum(load.load for load in utilities.items if load.utility_type.lower().startswith("cooling water"))
    power_load = sum(load.load for load in utilities.items if load.utility_type.lower().startswith("electricity"))
    annual_utility_cost = steam_load * annual_hours * steam_price + cw_load * annual_hours * cw_price + power_load * annual_hours * power_price
    annual_labor_cost = 220.0 * labor_price
    annual_maintenance_cost = total_capex * 0.03
    annual_overheads = 0.18 * (annual_labor_cost + annual_maintenance_cost)
    annual_opex = annual_raw_material_cost + annual_utility_cost + annual_labor_cost + annual_maintenance_cost + annual_overheads
    scenario_results: list[ScenarioResult] = []
    if scenario_policy is not None:
        for scenario in scenario_policy.cases:
            scenario_utility_cost = (
                steam_load * annual_hours * steam_price * scenario.steam_price_multiplier
                + cw_load * annual_hours * cw_price * scenario.power_price_multiplier
                + power_load * annual_hours * power_price * scenario.power_price_multiplier
            )
            scenario_raw_material_cost = annual_raw_material_cost * scenario.feedstock_price_multiplier
            scenario_maintenance = annual_maintenance_cost * scenario.capex_multiplier
            scenario_overheads = 0.18 * (annual_labor_cost + scenario_maintenance)
            scenario_opex = scenario_raw_material_cost + scenario_utility_cost + annual_labor_cost + scenario_maintenance + scenario_overheads
            scenario_revenue = annual_output_kg(basis) * market.estimated_price_per_kg * scenario.selling_price_multiplier
            scenario_results.append(
                ScenarioResult(
                    scenario_name=scenario.name,
                    annual_utility_cost_inr=round(scenario_utility_cost, 2),
                    annual_operating_cost_inr=round(scenario_opex, 2),
                    annual_revenue_inr=round(scenario_revenue, 2),
                    gross_margin_inr=round(scenario_revenue - scenario_opex, 2),
                    selected=scenario.name == "base",
                )
            )

    traces = [
        CalcTrace(trace_id="cm_eqp", title="Equipment purchase cost", formula="Ceq = Cr + Cd + Cx + Cs + Cf", result=f"{equipment_purchase:.2f}", units="INR"),
        CalcTrace(trace_id="cm_capex", title="Total CAPEX", formula="CAPEX = Direct + Indirect + Contingency", substitutions={"Direct": f"{direct_cost:.2f}", "Indirect": f"{indirect_cost:.2f}", "Contingency": f"{contingency:.2f}"}, result=f"{total_capex:.2f}", units="INR"),
        CalcTrace(trace_id="cm_rm", title="Annual raw material cost", formula="CRM = m_EO * P_EO + m_water * P_water", substitutions={"m_EO": f"{eo_annual_kg:.2f} kg/y", "P_EO": f"{eo_price:.2f} INR/kg", "m_water": f"{water_annual_kg:.2f} kg/y", "P_water": f"{water_price:.4f} INR/kg"}, result=f"{annual_raw_material_cost:.2f}", units="INR/y"),
    ]
    return CostModel(
        currency=basis.currency,
        equipment_purchase_cost=round(equipment_purchase, 2),
        installed_cost=round(installed_cost, 2),
        direct_cost=round(direct_cost, 2),
        indirect_cost=round(indirect_cost, 2),
        contingency=round(contingency, 2),
        total_capex=round(total_capex, 2),
        annual_opex=round(annual_opex, 2),
        annual_raw_material_cost=round(annual_raw_material_cost, 2),
        annual_utility_cost=round(annual_utility_cost, 2),
        annual_labor_cost=round(annual_labor_cost, 2),
        annual_maintenance_cost=round(annual_maintenance_cost, 2),
        annual_overheads=round(annual_overheads, 2),
        calc_traces=traces,
        india_price_data=price_data,
        selected_route_id=utility_network_decision.route_id if utility_network_decision else None,
        selected_heat_integration_case_id=selected_case.case_id if selected_case else None,
        integration_capex_inr=round(integration_capex, 2),
        scenario_results=scenario_results,
        value_records=[
            make_value_record("cost_equipment_purchase", "Equipment purchase cost", equipment_purchase, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_total_capex", "Total CAPEX", total_capex, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_annual_raw_material", "Annual raw-material cost", annual_raw_material_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_annual_utility", "Annual utility cost", annual_utility_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_annual_opex", "Annual operating cost", annual_opex, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + [
            "Installed-cost, indirect-cost, and contingency factors reflect preliminary India feasibility-study level estimating.",
            f"Labor burden normalized to {basis.labor_basis_year} India basis.",
        ],
    )


def build_working_capital_model(
    basis: ProjectBasis,
    cost_model: CostModel,
    market_price_per_kg: float,
    citations: list[str],
    assumptions: list[str],
    operations_planning: OperationsPlanningArtifact | None = None,
) -> WorkingCapitalModel:
    return build_working_capital_model_v2(basis, cost_model, market_price_per_kg, citations, assumptions, operations_planning)

    revenue = annual_output_kg(basis) * market_price_per_kg
    raw_material_days = 20.0
    product_inventory_days = 12.0
    receivable_days = 30.0
    payable_days = 20.0
    raw_material_inventory = cost_model.annual_raw_material_cost * raw_material_days / 365.0
    product_inventory = revenue * product_inventory_days / 365.0
    receivables = revenue * receivable_days / 365.0
    payables = cost_model.annual_raw_material_cost * payable_days / 365.0
    cash_buffer = cost_model.annual_opex * 10.0 / 365.0
    working_capital = raw_material_inventory + product_inventory + receivables + cash_buffer - payables
    traces = [
        CalcTrace(trace_id="wc_formula", title="Working capital", formula="WC = RM inv + FG inv + receivables + cash buffer - payables", substitutions={"RM inv": f"{raw_material_inventory:.2f}", "FG inv": f"{product_inventory:.2f}", "Receivables": f"{receivables:.2f}", "Cash buffer": f"{cash_buffer:.2f}", "Payables": f"{payables:.2f}"}, result=f"{working_capital:.2f}", units="INR"),
    ]
    return WorkingCapitalModel(
        raw_material_days=raw_material_days,
        product_inventory_days=product_inventory_days,
        receivable_days=receivable_days,
        payable_days=payable_days,
        working_capital_inr=round(working_capital, 2),
        calc_traces=traces,
        value_records=[
            make_value_record("wc_raw_material_days", "Raw-material inventory days", raw_material_days, "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("wc_receivable_days", "Receivable days", receivable_days, "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("wc_working_capital", "Working capital", working_capital, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + ["Working-capital basis uses a petrochemical-style receivables and inventory cycle for a continuous India plant."],
    )


def _npv(rate: float, initial_investment: float, annual_cashflow: float, years: int = 12) -> float:
    return -initial_investment + sum(annual_cashflow / ((1.0 + rate) ** year) for year in range(1, years + 1))


def _irr(initial_investment: float, annual_cashflow: float, years: int = 12) -> float:
    low, high = 0.0001, 1.5
    mid = 0.15
    for _ in range(100):
        mid = (low + high) / 2.0
        value = _npv(mid, initial_investment, annual_cashflow, years)
        if abs(value) < 1e-6:
            return mid
        if value > 0:
            low = mid
        else:
            high = mid
    return mid


def build_financial_model(
    basis: ProjectBasis,
    market_price_per_kg: float,
    cost_model: CostModel,
    working_capital: WorkingCapitalModel,
    citations: list[str],
    assumptions: list[str],
    financing_basis: DecisionRecord | None = None,
) -> FinancialModel:
    if financing_basis is None:
        financing_seed = build_financing_basis_decision(
            basis,
            SiteSelectionArtifact(candidates=[], selected_site="India", markdown="", citations=citations, assumptions=assumptions),
        )
        _, financial_model = evaluate_financing_basis_decision(
            basis,
            market_price_per_kg,
            cost_model,
            working_capital,
            citations,
            assumptions,
            financing_seed,
        )
        return financial_model
    return build_financial_model_v2(basis, market_price_per_kg, cost_model, working_capital, citations, assumptions, financing_basis)

    annual_revenue = annual_output_kg(basis) * market_price_per_kg
    gross_profit = annual_revenue - cost_model.annual_opex
    total_investment = cost_model.total_capex + working_capital.working_capital_inr
    payback_years = total_investment / max(gross_profit, 1.0)
    irr = _irr(total_investment, gross_profit)
    npv = _npv(0.12, total_investment, gross_profit)
    profitability_index = (npv + total_investment) / max(total_investment, 1.0)
    break_even_fraction = min(max(cost_model.annual_opex / max(annual_revenue, 1.0), 0.0), 1.5)
    traces = [
        CalcTrace(trace_id="fm_revenue", title="Annual revenue", formula="Revenue = annual output * selling price", substitutions={"annual output": f"{annual_output_kg(basis):.2f} kg/y", "selling price": f"{market_price_per_kg:.2f} INR/kg"}, result=f"{annual_revenue:.2f}", units="INR/y"),
        CalcTrace(trace_id="fm_payback", title="Simple payback", formula="Payback = (CAPEX + WC) / gross profit", substitutions={"CAPEX": f"{cost_model.total_capex:.2f}", "WC": f"{working_capital.working_capital_inr:.2f}", "gross profit": f"{gross_profit:.2f}"}, result=f"{payback_years:.3f}", units="y"),
    ]
    return FinancialModel(
        currency=basis.currency,
        annual_revenue=round(annual_revenue, 2),
        annual_operating_cost=round(cost_model.annual_opex, 2),
        gross_profit=round(gross_profit, 2),
        working_capital=round(working_capital.working_capital_inr, 2),
        payback_years=round(payback_years, 3),
        npv=round(npv, 2),
        irr=round(irr * 100.0, 2),
        profitability_index=round(profitability_index, 3),
        break_even_fraction=round(break_even_fraction, 3),
        calc_traces=traces,
        scenario_results=cost_model.scenario_results,
        value_records=[
            make_value_record("financial_annual_revenue", "Annual revenue", annual_revenue, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_gross_profit", "Gross profit", gross_profit, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_payback", "Simple payback", payback_years, "y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_irr", "IRR", irr * 100.0, "%", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + ["12-year project life and 12% discount rate assumed for India financial screening."],
    )
