import copy
import unittest

from aoc.calculators import (
    _irr,
    build_column_design,
    build_cost_model,
    build_energy_balance,
    build_equipment_list,
    build_financial_model,
    build_heat_exchanger_design,
    build_reaction_system,
    build_reactor_design,
    build_storage_design,
    build_stream_table,
    build_utility_basis,
    build_working_capital_model,
    compute_utilities,
    parse_formula,
    reaction_is_balanced,
    sensible_duty_kw,
)
from aoc.economics_v2 import (
    build_financing_basis_decision,
    build_route_economic_basis_artifact,
    build_route_site_fit_artifact,
    evaluate_financing_basis_decision,
)
from aoc.utility_architecture import build_utility_architecture_decision
from aoc.models import (
    DecisionRecord,
    FlowsheetBlueprintArtifact,
    FlowsheetBlueprintStep,
    GeographicScope,
    HeatIntegrationCase,
    HeatMatch,
    HeatStream,
    IndianLocationDatum,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    MarketAssessmentArtifact,
    OperationsPlanningArtifact,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    RouteSelectionArtifact,
    RouteOption,
    ScenarioCase,
    ScenarioPolicy,
    SiteOption,
    SiteSelectionArtifact,
    ThermoAssessmentArtifact,
    UtilityNetworkDecision,
    UtilityTarget,
)


class CalculatorTests(unittest.TestCase):
    def _basis(self) -> ProjectBasis:
        return ProjectBasis(
            target_product="Ethylene Glycol",
            capacity_tpa=200000,
            target_purity_wt_pct=99.9,
            process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
            india_only=True,
        )

    def _route(self) -> RouteOption:
        return RouteOption(
            route_id="eo_hydration",
            name="Ethylene oxide hydration",
            reaction_equation="C2H4O + H2O -> C2H6O2",
            participants=[
                ReactionParticipant(name="Ethylene oxide", formula="C2H4O", coefficient=1, role="reactant", molecular_weight_g_mol=44.05),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1, role="reactant", molecular_weight_g_mol=18.015),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1, role="product", molecular_weight_g_mol=62.07),
            ],
            operating_temperature_c=190,
            operating_pressure_bar=14,
            residence_time_hr=0.75,
            yield_fraction=0.92,
            selectivity_fraction=0.93,
            scale_up_notes="",
            route_score=9.5,
            rationale="",
            citations=["s1", "s2"],
        )

    def test_parse_formula(self):
        self.assertEqual(parse_formula("C7H7NO3"), {"C": 7, "H": 7, "N": 1, "O": 3})

    def test_reaction_balance(self):
        self.assertTrue(reaction_is_balanced(self._route()))

    def test_energy_reactor_column_and_finance_helpers(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy, kinetics=kinetics)
        column = build_column_design(basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        storage = build_storage_design(basis, 1113.0, ["s1"], [])
        equipment_list = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        utility_basis = build_utility_basis(basis, ["s1"], [])
        utilities = compute_utilities(
            basis,
            energy,
            equipment_list,
            utility_basis,
            ["s1"],
            [],
        )
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=63.0,
            price_range="INR 58-70/kg",
            competitor_notes=["seed"],
            demand_drivers=["seed"],
            capacity_rationale="seed",
            india_price_data=[
                IndianPriceDatum(datum_id="eo", category="raw_material", item_name="Ethylene oxide", region="India", units="INR/kg", value_inr=62.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="water", category="raw_material", item_name="Process water", region="India", units="INR/kg", value_inr=0.02, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region="India", units="INR/kg", value_inr=1.8, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="cw", category="utility", item_name="Cooling water", region="India", units="INR/m3", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
            ],
            markdown="seed",
            citations=["s1"],
        )
        site = SiteSelectionArtifact(
            candidates=[
                SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="seed", citations=["s1"])
            ],
            selected_site="Dahej",
            india_location_data=[
                IndianLocationDatum(location_id="loc1", site_name="Dahej", state="Gujarat", country="India", port_access="seed", utility_note="seed", logistics_note="seed", regulatory_note="seed", reference_year=2025, citations=["s1"])
            ],
            markdown="seed",
            citations=["s1"],
        )
        cost_model = build_cost_model(basis, equipment=equipment_list, utilities=utilities, stream_table=stream_table, market=market, site=site, citations=["s1"], assumptions=[])
        operations_planning = OperationsPlanningArtifact(
            planning_id="ops",
            service_family="continuous_liquid_purification",
            recommended_operating_mode="continuous",
            availability_policy_label="continuous_liquid_train",
            raw_material_buffer_days=16.0,
            finished_goods_buffer_days=7.0,
            operating_stock_days=2.5,
            restart_buffer_days=1.5,
            startup_ramp_days=2.0,
            campaign_length_days=170.0,
            cleaning_cycle_days=150.0,
            cleaning_downtime_days=2.0,
            turnaround_buffer_factor=1.05,
            throughput_loss_fraction=0.02,
            restart_loss_fraction=0.005,
            annual_restart_loss_kg=1200.0,
            buffer_basis_note="test",
            markdown="test",
            citations=["s1"],
        )
        storage = build_storage_design(basis, 1113.0, ["s1"], [], operations_planning=operations_planning)
        wc_model = build_working_capital_model(basis, cost_model, market.estimated_price_per_kg, ["s1"], [], operations_planning)
        financial = build_financial_model(basis, market.estimated_price_per_kg, cost_model, wc_model, ["s1"], [])

        self.assertAlmostEqual(sensible_duty_kw(3600, 4.0, 10.0), 40.0)
        self.assertGreater(_irr(100.0, 30.0, years=10), 0.0)
        self.assertLess(stream_table.closure_error_pct, 0.01)
        self.assertGreater(energy.total_heating_kw, 0.0)
        self.assertTrue(energy.unit_thermal_packets)
        self.assertTrue(energy.network_candidates)
        self.assertGreater(reactor.design_volume_m3, 0.0)
        self.assertTrue(any(trace.trace_id == "reactor_packet_basis" for trace in reactor.calc_traces))
        self.assertTrue(any(trace.trace_id == "reactor_kinetic_basis" for trace in reactor.calc_traces))
        self.assertTrue(any(trace.trace_id == "reactor_thermal_stability_basis" for trace in reactor.calc_traces))
        self.assertGreater(reactor.kinetic_rate_constant_1_hr, 0.0)
        self.assertGreater(reactor.kinetic_space_time_hr, 0.0)
        self.assertGreaterEqual(reactor.kinetic_damkohler_number, 0.0)
        self.assertGreater(reactor.heat_release_density_kw_m3, 0.0)
        self.assertGreater(reactor.adiabatic_temperature_rise_c, 0.0)
        self.assertGreater(reactor.heat_removal_capacity_kw, reactor.heat_duty_kw)
        self.assertIn(reactor.runaway_risk_label, {"low", "moderate", "high"})
        self.assertGreater(column.design_stages, 0)
        self.assertGreater(column.theoretical_stages, 0.0)
        self.assertGreaterEqual(column.reflux_ratio, column.minimum_reflux_ratio)
        self.assertGreater(column.allowable_vapor_velocity_m_s, 0.0)
        self.assertTrue(any(trace.trace_id == "column_packet_basis" for trace in column.calc_traces))
        self.assertTrue(any(trace.trace_id == "column_vle_basis" for trace in column.calc_traces))
        self.assertTrue(any(trace.trace_id == "column_fenske_min_stages" for trace in column.calc_traces))
        self.assertTrue(any(trace.trace_id == "column_reboiler_package_basis" for trace in column.calc_traces))
        self.assertTrue(any(trace.trace_id == "exchanger_packet_basis" for trace in exchanger.calc_traces))
        self.assertTrue(exchanger.selected_package_roles is not None)
        self.assertGreater(storage.total_volume_m3, 0.0)
        self.assertGreater(storage.dispatch_buffer_days, 0.0)
        self.assertGreater(storage.restart_buffer_days, 0.0)
        self.assertGreater(wc_model.restart_loss_inventory_inr, 0.0)
        self.assertGreater(wc_model.outage_buffer_inventory_inr, 0.0)
        self.assertGreater(wc_model.procurement_timing_factor, 1.0)
        self.assertGreater(wc_model.precommissioning_inventory_days, 0.0)
        self.assertGreater(wc_model.precommissioning_inventory_month, 0.0)
        self.assertGreater(wc_model.precommissioning_inventory_inr, 0.0)
        self.assertGreater(wc_model.peak_working_capital_month, 0.0)
        self.assertGreaterEqual(wc_model.peak_working_capital_inr, wc_model.working_capital_inr)
        self.assertTrue(any(trace.trace_id == "wc_procurement_timing" for trace in wc_model.calc_traces))
        self.assertGreater(wc_model.working_capital_inr, 0.0)
        self.assertTrue(cost_model.procurement_profile_label)
        self.assertGreater(cost_model.construction_months, 0)
        self.assertGreater(cost_model.total_import_duty_inr, 0.0)
        self.assertTrue(cost_model.procurement_schedule)
        self.assertTrue(cost_model.procurement_package_impacts)
        self.assertAlmostEqual(sum(float(item["draw_fraction"]) for item in cost_model.procurement_schedule), 1.0, places=2)
        self.assertTrue(any(item.procurement_package_family for item in cost_model.equipment_cost_items))
        self.assertTrue(any(item.import_duty_inr > 0.0 for item in cost_model.equipment_cost_items))
        self.assertGreater(financial.annual_revenue, 0.0)
        self.assertGreater(financial.irr, 0.0)
        self.assertGreater(financial.construction_interest_during_construction_inr, 0.0)
        self.assertGreater(financial.total_project_funding_inr, cost_model.total_capex)
        self.assertGreaterEqual(financial.peak_working_capital_inr, wc_model.peak_working_capital_inr)
        self.assertGreater(financial.peak_working_capital_month, 0.0)
        self.assertGreater(financial.minimum_dscr, 0.0)
        self.assertGreater(financial.average_dscr, 0.0)
        self.assertGreaterEqual(financial.llcr, 0.0)
        self.assertGreaterEqual(financial.plcr, 0.0)
        self.assertGreaterEqual(financial.plcr, financial.llcr)
        self.assertTrue(financial.selected_financing_candidate_id)
        self.assertIsInstance(financial.covenant_breach_codes, list)
        self.assertIsInstance(financial.covenant_warnings, list)

    def test_route_site_fit_and_route_economic_basis_flow_into_cost_model(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy, kinetics=kinetics)
        column = build_column_design(basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        operations_planning = OperationsPlanningArtifact(
            planning_id="ops",
            service_family="continuous_liquid_purification",
            recommended_operating_mode="batch",
            availability_policy_label="campaign_batch_train",
            raw_material_buffer_days=14.0,
            finished_goods_buffer_days=6.0,
            operating_stock_days=3.0,
            restart_buffer_days=1.0,
            startup_ramp_days=2.0,
            campaign_length_days=45.0,
            cleaning_cycle_days=30.0,
            cleaning_downtime_days=3.5,
            turnaround_buffer_factor=1.10,
            throughput_loss_fraction=0.03,
            restart_loss_fraction=0.008,
            annual_restart_loss_kg=900.0,
            buffer_basis_note="test",
            markdown="test",
            citations=["s1"],
        )
        storage = build_storage_design(basis, 1113.0, ["s1"], [], operations_planning=operations_planning)
        equipment_list = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        utilities = compute_utilities(basis, energy, equipment_list, build_utility_basis(basis, ["s1"], []), ["s1"], [])
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=63.0,
            price_range="INR 58-70/kg",
            competitor_notes=["seed"],
            demand_drivers=["seed"],
            capacity_rationale="seed",
            india_price_data=[
                IndianPriceDatum(datum_id="eo", category="raw_material", item_name="Ethylene oxide", region="India", units="INR/kg", value_inr=62.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="water", category="raw_material", item_name="Process water", region="India", units="INR/kg", value_inr=0.02, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region="India", units="INR/kg", value_inr=1.8, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="cw", category="utility", item_name="Cooling water", region="India", units="INR/m3", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
            ],
            markdown="seed",
            citations=["s1"],
        )
        site = SiteSelectionArtifact(
            candidates=[SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="seed", citations=["s1"])],
            selected_site="Dahej",
            india_location_data=[
                IndianLocationDatum(location_id="loc1", site_name="Dahej", state="Gujarat", country="India", port_access="Near port-based chemical cluster", utility_note="seed", logistics_note="seed", regulatory_note="seed", reference_year=2025, citations=["s1"])
            ],
            markdown="seed",
            citations=["s1"],
        )
        route_selection = RouteSelectionArtifact(
            selected_route_id=route.route_id,
            justification="seed",
            comparison_markdown="seed",
            citations=["s1"],
            assumptions=[],
        )
        blueprint = FlowsheetBlueprintArtifact(
            blueprint_id="bp-1",
            route_id=route.route_id,
            route_name=route.name,
            route_origin="hybrid",
            steps=[
                FlowsheetBlueprintStep(
                    step_id="s1",
                    route_id=route.route_id,
                    section_id="react",
                    section_label="Reaction",
                    step_role="reaction",
                    unit_id="R-101",
                    unit_tag="R001",
                    unit_type="reactor",
                    service="Catalytic reactor",
                ),
                FlowsheetBlueprintStep(
                    step_id="s2",
                    route_id=route.route_id,
                    section_id="purify",
                    section_label="Purification",
                    step_role="separation",
                    unit_id="D-101",
                    unit_tag="DC001",
                    unit_type="distillation column",
                    service="Primary purification",
                    upstream_step_ids=["s1"],
                ),
            ],
            separation_duties=[],
            recycle_intents=[],
            batch_capable=True,
            selected_unit_tags=["R001", "DC001"],
            markdown="seed",
            citations=["s1"],
            assumptions=[],
        )
        route_site_fit = build_route_site_fit_artifact(
            basis,
            site,
            route_selection,
            blueprint,
            operations_planning,
            ["s1"],
            [],
        )
        route_economic_basis = build_route_economic_basis_artifact(
            basis,
            site,
            route_selection,
            stream_table,
            market,
            blueprint,
            operations_planning,
            route_site_fit,
            ["s1"],
            [],
        )
        cost_model = build_cost_model(
            basis,
            equipment=equipment_list,
            utilities=utilities,
            stream_table=stream_table,
            market=market,
            site=site,
            citations=["s1"],
            assumptions=[],
            route_site_fit=route_site_fit,
            route_economic_basis=route_economic_basis,
            column_design=column,
        )

        self.assertGreater(route_site_fit.overall_fit_score, 0.0)
        self.assertGreaterEqual(route_economic_basis.raw_material_complexity_factor, 1.0)
        self.assertGreaterEqual(route_economic_basis.site_input_cost_factor, 1.0)
        self.assertGreaterEqual(route_economic_basis.logistics_intensity_factor, 1.0)
        self.assertGreaterEqual(cost_model.route_site_fit_score, route_site_fit.overall_fit_score - 0.01)
        self.assertGreaterEqual(cost_model.route_feedstock_cluster_factor, 1.0)
        self.assertGreaterEqual(cost_model.route_logistics_penalty_factor, 1.0)
        self.assertGreaterEqual(cost_model.route_batch_penalty_fraction, 0.0)
        self.assertGreaterEqual(cost_model.route_solvent_recovery_service_cost_inr, 0.0)
        self.assertGreaterEqual(cost_model.route_catalyst_service_cost_inr, 0.0)
        self.assertGreaterEqual(cost_model.route_waste_treatment_burden_inr, 0.0)
        self.assertTrue(any(trace.trace_id == "route_site_fit_cost_basis" for trace in cost_model.calc_traces))
        self.assertTrue(any(trace.trace_id == "route_economic_basis" for trace in cost_model.calc_traces))

    def test_financing_basis_reranking_responds_to_covenant_pressure(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy, kinetics=kinetics)
        column = build_column_design(basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        operations_planning = OperationsPlanningArtifact(
            planning_id="ops",
            service_family="continuous_liquid_purification",
            recommended_operating_mode="continuous",
            availability_policy_label="continuous_liquid_train",
            raw_material_buffer_days=16.0,
            finished_goods_buffer_days=7.0,
            operating_stock_days=2.5,
            restart_buffer_days=1.5,
            startup_ramp_days=2.0,
            campaign_length_days=170.0,
            cleaning_cycle_days=150.0,
            cleaning_downtime_days=2.0,
            turnaround_buffer_factor=1.05,
            throughput_loss_fraction=0.02,
            restart_loss_fraction=0.005,
            annual_restart_loss_kg=1200.0,
            buffer_basis_note="test",
            markdown="test",
            citations=["s1"],
        )
        storage = build_storage_design(basis, 1113.0, ["s1"], [], operations_planning=operations_planning)
        equipment_list = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=28.0,
            price_range="INR 26-30/kg",
            competitor_notes=["seed"],
            demand_drivers=["seed"],
            capacity_rationale="seed",
            india_price_data=[
                IndianPriceDatum(datum_id="eo", category="raw_material", item_name="Ethylene oxide", region="India", units="INR/kg", value_inr=62.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="water", category="raw_material", item_name="Process water", region="India", units="INR/kg", value_inr=0.02, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region="India", units="INR/kg", value_inr=1.8, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="cw", category="utility", item_name="Cooling water", region="India", units="INR/m3", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
            ],
            markdown="seed",
            citations=["s1"],
        )
        site = SiteSelectionArtifact(
            candidates=[
                SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="seed", citations=["s1"])
            ],
            selected_site="Dahej",
            india_location_data=[
                IndianLocationDatum(location_id="loc1", site_name="Dahej", state="Gujarat", country="India", port_access="seed", utility_note="seed", logistics_note="seed", regulatory_note="seed", reference_year=2025, citations=["s1"])
            ],
            markdown="seed",
            citations=["s1"],
        )
        cost_model = build_cost_model(basis, equipment=equipment_list, utilities=compute_utilities(basis, energy, equipment_list, build_utility_basis(basis, ["s1"], []), ["s1"], []), stream_table=stream_table, market=market, site=site, citations=["s1"], assumptions=[])
        wc_model = build_working_capital_model(basis, cost_model, market.estimated_price_per_kg, ["s1"], [], operations_planning)
        financing_seed = build_financing_basis_decision(basis, site)

        financing_decision, financial_model = evaluate_financing_basis_decision(
            basis,
            market.estimated_price_per_kg,
            cost_model,
            wc_model,
            ["s1"],
            [],
            financing_seed,
        )

        self.assertEqual(financing_decision.selected_candidate_id, financial_model.selected_financing_candidate_id)
        self.assertTrue(all(option.outputs.get("llcr") for option in financing_decision.alternatives))
        self.assertTrue(all(option.outputs.get("plcr") for option in financing_decision.alternatives))
        self.assertTrue(all(option.outputs.get("coverage_status") in {"pass", "warning"} for option in financing_decision.alternatives))
        self.assertIn("reranking", financing_decision.selected_summary.lower())
        self.assertTrue(any(option.score_breakdown.get("coverage", 0.0) >= 0.0 for option in financing_decision.alternatives))
        if financial_model.covenant_breach_codes:
            self.assertTrue(financing_decision.approval_required)

    def test_financing_basis_can_reverse_under_downside_scenario(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy, kinetics=kinetics)
        column = build_column_design(basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        operations_planning = OperationsPlanningArtifact(
            planning_id="ops",
            service_family="continuous_liquid_purification",
            recommended_operating_mode="continuous",
            availability_policy_label="continuous_liquid_train",
            raw_material_buffer_days=16.0,
            finished_goods_buffer_days=7.0,
            operating_stock_days=2.5,
            restart_buffer_days=1.5,
            startup_ramp_days=2.0,
            campaign_length_days=170.0,
            cleaning_cycle_days=150.0,
            cleaning_downtime_days=2.0,
            turnaround_buffer_factor=1.05,
            throughput_loss_fraction=0.02,
            restart_loss_fraction=0.005,
            annual_restart_loss_kg=1200.0,
            buffer_basis_note="test",
            markdown="test",
            citations=["s1"],
        )
        storage = build_storage_design(basis, 1113.0, ["s1"], [], operations_planning=operations_planning)
        equipment_list = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=61.0,
            price_range="INR 58-64/kg",
            competitor_notes=["seed"],
            demand_drivers=["seed"],
            capacity_rationale="seed",
            india_price_data=[
                IndianPriceDatum(datum_id="eo", category="raw_material", item_name="Ethylene oxide", region="India", units="INR/kg", value_inr=62.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="water", category="raw_material", item_name="Process water", region="India", units="INR/kg", value_inr=0.02, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region="India", units="INR/kg", value_inr=1.8, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="cw", category="utility", item_name="Cooling water", region="India", units="INR/m3", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
            ],
            markdown="seed",
            citations=["s1"],
        )
        site = SiteSelectionArtifact(
            candidates=[
                SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="seed", citations=["s1"])
            ],
            selected_site="Dahej",
            india_location_data=[
                IndianLocationDatum(location_id="loc1", site_name="Dahej", state="Gujarat", country="India", port_access="seed", utility_note="seed", logistics_note="seed", regulatory_note="seed", reference_year=2025, citations=["s1"])
            ],
            markdown="seed",
            citations=["s1"],
        )
        utilities = compute_utilities(basis, energy, equipment_list, build_utility_basis(basis, ["s1"], []), ["s1"], [])
        stressed_scenarios = ScenarioPolicy(
            cases=[
                ScenarioCase(name="base", description="base"),
                ScenarioCase(
                    name="conservative",
                    description="stressed downside",
                    steam_price_multiplier=1.30,
                    power_price_multiplier=1.20,
                    feedstock_price_multiplier=1.15,
                    selling_price_multiplier=0.78,
                    capex_multiplier=1.12,
                ),
            ]
        )
        cost_model = build_cost_model(
            basis,
            equipment=equipment_list,
            utilities=utilities,
            stream_table=stream_table,
            market=market,
            site=site,
            citations=["s1"],
            assumptions=[],
            scenario_policy=stressed_scenarios,
        )
        wc_model = build_working_capital_model(basis, cost_model, market.estimated_price_per_kg, ["s1"], [], operations_planning)
        financing_seed = build_financing_basis_decision(basis, site)

        financing_decision, financial_model = evaluate_financing_basis_decision(
            basis,
            market.estimated_price_per_kg,
            cost_model,
            wc_model,
            ["s1"],
            [],
            financing_seed,
        )

        self.assertTrue(financial_model.downside_scenario_name)
        self.assertTrue(financial_model.downside_financing_candidate_id)
        self.assertEqual(financial_model.selected_financing_candidate_id, financing_decision.selected_candidate_id)
        self.assertTrue(
            financial_model.financing_scenario_reversal
            or financial_model.downside_financing_candidate_id == financing_decision.selected_candidate_id
        )
        if financial_model.financing_scenario_reversal:
            self.assertTrue(financing_decision.approval_required)

    def test_cost_model_captures_utility_island_economics_when_recovery_is_selected(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy, kinetics=kinetics)
        column = build_column_design(basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        storage = build_storage_design(basis, 1113.0, ["s1"], [])
        equipment_list = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        utility_basis = build_utility_basis(basis, ["s1"], [])
        utilities = compute_utilities(basis, energy, equipment_list, utility_basis, ["s1"], [])
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=63.0,
            price_range="INR 58-70/kg",
            competitor_notes=["seed"],
            demand_drivers=["seed"],
            capacity_rationale="seed",
            india_price_data=[
                IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region="India", units="INR/kg", value_inr=1.8, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="cw", category="utility", item_name="Cooling water", region="India", units="INR/m3", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
                IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=["s1"]),
            ],
            markdown="seed",
            citations=["s1"],
        )
        site = SiteSelectionArtifact(
            candidates=[SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="seed", citations=["s1"])],
            selected_site="Dahej",
            india_location_data=[IndianLocationDatum(location_id="loc1", site_name="Dahej", state="Gujarat", country="India", port_access="seed", utility_note="seed", logistics_note="seed", regulatory_note="seed", reference_year=2025, citations=["s1"])],
            markdown="seed",
            citations=["s1"],
        )
        utility_decision = UtilityNetworkDecision(
            route_id="eo_hydration",
            utility_target=UtilityTarget(
                base_hot_utility_kw=180.0,
                base_cold_utility_kw=160.0,
                minimum_hot_utility_kw=40.0,
                minimum_cold_utility_kw=50.0,
                recoverable_duty_kw=120.0,
                pinch_temp_c=118.0,
            ),
            heat_streams=[
                HeatStream(stream_id="H1", name="Reactor effluent", kind="hot", source_unit_id="reactor", supply_temp_c=180.0, target_temp_c=120.0, duty_kw=100.0),
                HeatStream(stream_id="C1", name="Column reboiler", kind="cold", source_unit_id="purification", supply_temp_c=90.0, target_temp_c=150.0, duty_kw=90.0),
                HeatStream(stream_id="H2", name="Concentrator overhead", kind="hot", source_unit_id="concentration", supply_temp_c=140.0, target_temp_c=80.0, duty_kw=80.0),
                HeatStream(stream_id="C2", name="Dryer preheat", kind="cold", source_unit_id="drying", supply_temp_c=40.0, target_temp_c=95.0, duty_kw=70.0),
            ],
            cases=[
                HeatIntegrationCase(
                    case_id="eo_hydration_direct",
                    title="Direct recovery",
                    recovered_duty_kw=120.0,
                    residual_hot_utility_kw=60.0,
                    residual_cold_utility_kw=40.0,
                    added_capex_inr=10_000_000.0,
                    annual_savings_inr=5_000_000.0,
                    payback_years=2.0,
                    operability_penalty=0.05,
                    safety_penalty=0.02,
                    heat_matches=[
                        HeatMatch(match_id="match_1", hot_stream_id="H1", cold_stream_id="C1", recovered_duty_kw=85.0, direct=True, medium="direct", min_approach_temp_c=20.0),
                        HeatMatch(match_id="match_2", hot_stream_id="H2", cold_stream_id="C2", recovered_duty_kw=60.0, direct=True, medium="direct", min_approach_temp_c=20.0),
                    ],
                )
            ],
            decision=DecisionRecord(
                decision_id="utility_network_decision",
                context="test utility architecture",
                selected_candidate_id="eo_hydration_direct",
                selected_summary="Direct recovery selected for test basis.",
                confidence=0.8,
            ),
            selected_case_id="eo_hydration_direct",
            base_annual_utility_cost_inr=12_000_000.0,
            selected_annual_utility_cost_inr=7_000_000.0,
            markdown="test",
        )
        utility_architecture = build_utility_architecture_decision(utility_decision)
        cost_model = build_cost_model(
            basis,
            equipment=equipment_list,
            utilities=utilities,
            stream_table=stream_table,
            market=market,
            site=site,
            citations=["s1"],
            assumptions=[],
            utility_network_decision=utility_decision,
            utility_architecture=utility_architecture,
            column_design=column,
        )

        self.assertTrue(cost_model.utility_island_costs)
        self.assertGreater(cost_model.annual_utility_island_service_cost, 0.0)
        self.assertGreater(cost_model.annual_utility_island_replacement_cost, 0.0)
        self.assertEqual(len(cost_model.utility_island_costs), len(utility_architecture.architecture.selected_island_ids))
        self.assertTrue(all(item.project_capex_burden_inr > 0.0 for item in cost_model.utility_island_costs))
        self.assertTrue(all(item.annual_operating_burden_inr > item.annual_service_cost_inr for item in cost_model.utility_island_costs))
        self.assertTrue(all(item.maintenance_cycle_years > 0.0 for item in cost_model.utility_island_costs))
        self.assertTrue(all(item.replacement_event_cost_inr > 0.0 for item in cost_model.utility_island_costs))
        self.assertTrue(any(item.utility_island_impacts for item in cost_model.scenario_results))

    def test_design_selection_uses_selected_utility_architecture_family(self):
        basis = self._basis()
        route = self._route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        energy = build_energy_balance(route, stream_table, thermo)
        utility_decision = UtilityNetworkDecision(
            route_id="eo_hydration",
            utility_target=UtilityTarget(
                base_hot_utility_kw=240.0,
                base_cold_utility_kw=210.0,
                minimum_hot_utility_kw=70.0,
                minimum_cold_utility_kw=60.0,
                recoverable_duty_kw=150.0,
                pinch_temp_c=122.0,
            ),
            heat_streams=[
                HeatStream(stream_id="H1", name="Reactor effluent", kind="hot", source_unit_id="reactor", supply_temp_c=188.0, target_temp_c=120.0, duty_kw=92.0),
                HeatStream(stream_id="H2", name="Concentrator vapor", kind="hot", source_unit_id="concentration", supply_temp_c=152.0, target_temp_c=88.0, duty_kw=78.0),
                HeatStream(stream_id="C1", name="Purification reboiler", kind="cold", source_unit_id="purification", supply_temp_c=96.0, target_temp_c=168.0, duty_kw=88.0),
                HeatStream(stream_id="C2", name="Dryer preheat", kind="cold", source_unit_id="drying", supply_temp_c=58.0, target_temp_c=126.0, duty_kw=68.0),
            ],
            cases=[
                HeatIntegrationCase(
                    case_id="eo_hydration_htm",
                    title="HTM recovery basis",
                    recovered_duty_kw=150.0,
                    residual_hot_utility_kw=75.0,
                    residual_cold_utility_kw=60.0,
                    added_capex_inr=14_000_000.0,
                    annual_savings_inr=6_400_000.0,
                    payback_years=2.2,
                    operability_penalty=0.06,
                    safety_penalty=0.03,
                    heat_matches=[
                        HeatMatch(match_id="m1", hot_stream_id="H1", cold_stream_id="C1", recovered_duty_kw=82.0, direct=False, medium="Dowtherm A", min_approach_temp_c=20.0),
                        HeatMatch(match_id="m2", hot_stream_id="H2", cold_stream_id="C2", recovered_duty_kw=63.0, direct=False, medium="Dowtherm A", min_approach_temp_c=20.0),
                    ],
                )
            ],
            decision=DecisionRecord(
                decision_id="utility_network_decision",
                context="complex utility architecture",
                selected_candidate_id="eo_hydration_htm",
                selected_summary="HTM recovery selected for test basis.",
                confidence=0.82,
            ),
            selected_case_id="eo_hydration_htm",
            base_annual_utility_cost_inr=14_500_000.0,
            selected_annual_utility_cost_inr=8_100_000.0,
            markdown="test",
        )
        utility_architecture = build_utility_architecture_decision(utility_decision)

        reactor = build_reactor_design(
            basis,
            route,
            reaction_system,
            stream_table,
            energy,
            utility_architecture=utility_architecture,
            kinetics=kinetics,
        )
        self.assertEqual(reactor.utility_architecture_family, "shared_htm")
        self.assertTrue(reactor.selected_utility_island_ids)
        self.assertGreater(reactor.allocated_recovered_duty_target_kw, 0.0)
        self.assertTrue(
            any(
                trace.trace_id == "reactor_utility_integration_basis"
                and trace.substitutions.get("architecture_family") == "shared_htm"
                for trace in reactor.calc_traces
            )
        )

        cluster_case = next(
            case
            for case in utility_architecture.architecture.cases
            if case.architecture_family == "condenser_reboiler_cluster"
        )
        clustered_architecture = copy.deepcopy(utility_architecture)
        clustered_architecture.architecture.selected_case_id = cluster_case.case_id
        clustered_architecture.architecture.selected_island_ids = [island.island_id for island in cluster_case.utility_islands]
        clustered_architecture.architecture.selected_train_steps = cluster_case.selected_train_steps
        clustered_architecture.architecture.selected_package_items = [
            item for step in cluster_case.selected_train_steps for item in step.package_items
        ]
        clustered_architecture.architecture.topology_summary = (
            f"{cluster_case.topology} ({cluster_case.architecture_family}) with {len(cluster_case.utility_islands)} utility islands"
        )

        column = build_column_design(
            basis,
            route,
            stream_table,
            energy,
            utility_architecture=clustered_architecture,
        )
        exchanger = build_heat_exchanger_design(
            route,
            energy,
            utility_architecture=clustered_architecture,
        )

        self.assertEqual(column.utility_architecture_family, "condenser_reboiler_cluster")
        self.assertTrue(column.selected_utility_cluster_ids)
        self.assertGreater(column.allocated_reboiler_recovery_target_kw, 0.0)
        self.assertGreater(column.allocated_condenser_recovery_target_kw, 0.0)
        self.assertEqual(exchanger.utility_architecture_family, "condenser_reboiler_cluster")
        self.assertIsNotNone(exchanger.selected_cluster_id)
        self.assertGreater(exchanger.allocated_recovered_duty_target_kw, 0.0)
