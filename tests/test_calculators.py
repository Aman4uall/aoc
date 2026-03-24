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
from aoc.models import (
    GeographicScope,
    IndianLocationDatum,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    MarketAssessmentArtifact,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    RouteOption,
    SiteOption,
    SiteSelectionArtifact,
    ThermoAssessmentArtifact,
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
        reactor = build_reactor_design(basis, route, reaction_system, stream_table, energy)
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
        wc_model = build_working_capital_model(basis, cost_model, market.estimated_price_per_kg, ["s1"], [])
        financial = build_financial_model(basis, market.estimated_price_per_kg, cost_model, wc_model, ["s1"], [])

        self.assertAlmostEqual(sensible_duty_kw(3600, 4.0, 10.0), 40.0)
        self.assertGreater(_irr(100.0, 30.0, years=10), 0.0)
        self.assertLess(stream_table.closure_error_pct, 0.01)
        self.assertGreater(energy.total_heating_kw, 0.0)
        self.assertGreater(reactor.design_volume_m3, 0.0)
        self.assertGreater(column.design_stages, 0)
        self.assertGreater(storage.total_volume_m3, 0.0)
        self.assertGreater(wc_model.working_capital_inr, 0.0)
        self.assertGreater(financial.annual_revenue, 0.0)
        self.assertGreater(financial.irr, 0.0)
