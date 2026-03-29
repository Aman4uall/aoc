import unittest

from aoc.models import (
    ColumnDesign,
    CostModel,
    DecisionRecord,
    FinancialModel,
    GeographicScope,
    HeatExchangerDesign,
    HeatIntegrationCase,
    MechanicalComponentDesign,
    MechanicalDesignArtifact,
    MethodSelectionArtifact,
    OperationsPlanningArtifact,
    ProcessTemplate,
    ProjectBasis,
    ProjectConfig,
    RouteFamilyArtifact,
    RouteFamilyProfile,
    ResearchBundle,
    RouteHazard,
    RouteOption,
    RouteSelectionArtifact,
    ReactionParticipant,
    ReactorDesign,
    SourceDomain,
    SourceKind,
    SourceRecord,
    UnitOperationFamilyArtifact,
    UnitOperationFamilyCandidate,
    UtilityNetworkDecision,
    UtilityTarget,
    WorkingCapitalModel,
)
from aoc.properties.models import (
    ChemicalIdentifier,
    HenryLawConstant,
    PropertyPackage,
    PropertyPackageArtifact,
    PureComponentProperty,
    RelativeVolatilityEstimate,
    SeparationThermoArtifact,
    SolubilityCurve,
)
from aoc.validators import (
    validate_architecture_package_critics,
    validate_equipment_applicability,
    validate_financial_model,
    validate_financing_decision_alignment,
    validate_financing_operability_critics,
    validate_kinetics_method_critics,
    validate_mechanical_design_artifact,
    validate_reactor_hazard_basis_critics,
    validate_research_bundle,
    validate_route_economic_critics,
    validate_route_selection_critics,
    validate_separation_design_critics,
    validate_separation_thermo_artifact,
    validate_separation_thermo_critics,
    validate_technical_economic_critics,
    validate_unit_family_property_coverage,
    validate_working_capital,
)


class ValidatorTests(unittest.TestCase):
    def _make_route(self, route_id: str = "oxidation_route") -> RouteOption:
        return RouteOption(
            route_id=route_id,
            name="Catalytic oxidation route",
            rationale="Validator fixture route.",
            reaction_equation="A + O2 -> B",
            participants=[ReactionParticipant(name="Product", formula="B", coefficient=1.0, role="product", molecular_weight_g_mol=50.0, phase="liquid")],
            catalysts=["Pd catalyst"],
            operating_temperature_c=220.0,
            operating_pressure_bar=12.0,
            residence_time_hr=0.5,
            yield_fraction=0.85,
            selectivity_fraction=0.80,
            route_score=80.0,
            scale_up_notes="Catalytic oxidation",
            citations=["s1"],
            assumptions=["seed"],
        )

    def _make_column(self, **overrides) -> ColumnDesign:
        data = {
            "column_id": "C-101",
            "service": "Distillation column",
            "light_key": "water",
            "heavy_key": "product",
            "relative_volatility": 1.4,
            "min_stages": 12.0,
            "design_stages": 18,
            "reflux_ratio": 1.8,
            "column_diameter_m": 1.6,
            "column_height_m": 16.0,
            "condenser_duty_kw": 600.0,
            "reboiler_duty_kw": 750.0,
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return ColumnDesign(**data)

    def _make_reactor(self, **overrides) -> ReactorDesign:
        data = {
            "reactor_id": "R-101",
            "reactor_type": "Plug flow reactor",
            "design_basis": "seed",
            "residence_time_hr": 0.5,
            "liquid_holdup_m3": 5.0,
            "design_volume_m3": 6.0,
            "design_temperature_c": 220.0,
            "design_pressure_bar": 12.0,
            "heat_duty_kw": 500.0,
            "heat_transfer_area_m2": 40.0,
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return ReactorDesign(**data)

    def _make_exchanger(self, **overrides) -> HeatExchangerDesign:
        data = {
            "exchanger_id": "E-101",
            "service": "Reboiler",
            "heat_load_kw": 750.0,
            "lmtd_k": 25.0,
            "overall_u_w_m2_k": 450.0,
            "area_m2": 30.0,
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return HeatExchangerDesign(**data)

    def _make_utility_network(self, case: HeatIntegrationCase | None = None, **overrides) -> UtilityNetworkDecision:
        data = {
            "route_id": "route",
            "utility_target": UtilityTarget(
                base_hot_utility_kw=1000.0,
                base_cold_utility_kw=800.0,
                minimum_hot_utility_kw=700.0,
                minimum_cold_utility_kw=500.0,
                recoverable_duty_kw=300.0,
                pinch_temp_c=15.0,
                citations=["s1"],
                assumptions=["seed"],
            ),
            "cases": [case] if case is not None else [],
            "decision": DecisionRecord(
                decision_id="utility_network",
                context="seed",
                selected_candidate_id=case.case_id if case is not None else None,
                selected_summary="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            "selected_case_id": case.case_id if case is not None else None,
            "base_annual_utility_cost_inr": 1_000_000.0,
            "selected_annual_utility_cost_inr": 800_000.0,
            "markdown": "seed",
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return UtilityNetworkDecision(**data)

    def _make_cost_model(self, **overrides) -> CostModel:
        data = {
            "currency": "INR",
            "equipment_purchase_cost": 10_000_000.0,
            "installed_cost": 15_000_000.0,
            "direct_cost": 20_000_000.0,
            "indirect_cost": 5_000_000.0,
            "contingency": 2_000_000.0,
            "total_capex": 27_000_000.0,
            "annual_opex": 8_000_000.0,
            "annual_raw_material_cost": 4_000_000.0,
            "annual_utility_cost": 1_000_000.0,
            "annual_labor_cost": 500_000.0,
            "annual_maintenance_cost": 400_000.0,
            "annual_overheads": 300_000.0,
            "selected_route_id": "oxidation_route",
            "selected_heat_integration_case_id": "recovery_case",
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return CostModel(**data)

    def _make_operations_planning(self, **overrides) -> OperationsPlanningArtifact:
        data = {
            "planning_id": "ops",
            "service_family": "gas_liquid_absorption",
            "recommended_operating_mode": "continuous",
            "availability_policy_label": "gas_liquid_loop_availability",
            "raw_material_buffer_days": 18.0,
            "finished_goods_buffer_days": 5.0,
            "operating_stock_days": 2.0,
            "restart_buffer_days": 0.8,
            "startup_ramp_days": 1.5,
            "campaign_length_days": 180.0,
            "cleaning_cycle_days": 180.0,
            "cleaning_downtime_days": 1.4,
            "turnaround_buffer_factor": 1.04,
            "throughput_loss_fraction": 0.018,
            "restart_loss_fraction": 0.004,
            "annual_restart_loss_kg": 1200.0,
            "buffer_basis_note": "seed",
            "markdown": "seed",
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return OperationsPlanningArtifact(**data)

    def _make_property_packages(self, **overrides) -> PropertyPackageArtifact:
        data = {
            "identifiers": [
                ChemicalIdentifier(
                    identifier_id="product",
                    canonical_name="Product",
                    aliases=["product"],
                    source_ids=["s1"],
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            "packages": [
                PropertyPackage(
                    package_id="pkg_product",
                    identifier=ChemicalIdentifier(
                        identifier_id="product",
                        canonical_name="Product",
                        aliases=["product"],
                        source_ids=["s1"],
                        citations=["s1"],
                        assumptions=["seed"],
                    ),
                    liquid_density=PureComponentProperty(
                        property_id="rho_product",
                        identifier_id="product",
                        property_name="liquid_density",
                        value="950.0",
                        units="kg/m3",
                        source_ids=["s1"],
                        citations=["s1"],
                        assumptions=["seed"],
                    ),
                    liquid_heat_capacity=PureComponentProperty(
                        property_id="cp_product",
                        identifier_id="product",
                        property_name="liquid_heat_capacity",
                        value="2.5",
                        units="kJ/kg/K",
                        source_ids=["s1"],
                        citations=["s1"],
                        assumptions=["seed"],
                    ),
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            "primary_identifier_ids": ["product"],
            "markdown": "seed",
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return PropertyPackageArtifact(**data)

    def test_india_only_research_bundle_validation(self):
        config = ProjectConfig(
            project_id="eg",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            require_india_only_data=True,
        )
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="s1",
                    source_kind=SourceKind.HANDBOOK,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Tech",
                    citation_text="Tech",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2025,
                )
            ],
            corpus_excerpt="seed",
        )
        issues, missing, stale = validate_research_bundle(bundle, config)
        self.assertTrue(issues)
        self.assertIn("india_sources", missing)
        self.assertFalse(stale)

    def test_india_research_bundle_passes_when_coverage_exists(self):
        config = ProjectConfig(
            project_id="eg",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            require_india_only_data=True,
        )
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="s1",
                    source_kind=SourceKind.HANDBOOK,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Tech",
                    citation_text="Tech",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2025,
                ),
                SourceRecord(
                    source_id="s2",
                    source_kind=SourceKind.MARKET,
                    source_domain=SourceDomain.ECONOMICS,
                    title="India market",
                    citation_text="India market",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
                SourceRecord(
                    source_id="s3",
                    source_kind=SourceKind.COMPANY_REPORT,
                    source_domain=SourceDomain.SITE,
                    title="India site",
                    citation_text="India site",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                ),
                SourceRecord(
                    source_id="s4",
                    source_kind=SourceKind.UTILITY,
                    source_domain=SourceDomain.UTILITIES,
                    title="India utility",
                    citation_text="India utility",
                    geographic_scope=GeographicScope.STATE,
                    geographic_label="Gujarat",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
            ],
            technical_source_ids=["s1"],
            india_source_ids=["s2", "s3", "s4"],
            corpus_excerpt="seed",
        )
        issues, missing, stale = validate_research_bundle(bundle, config)
        self.assertFalse(issues)
        self.assertFalse(missing)
        self.assertFalse(stale)

    def test_mechanical_design_validation_requires_foundation_and_load_basis(self):
        artifact = MechanicalDesignArtifact(
            markdown="mechanical basis",
            items=[
                MechanicalComponentDesign(
                    equipment_id="V-101",
                    equipment_type="Vertical vessel",
                    service="Absorber service",
                    design_pressure_bar=8.0,
                    design_temperature_c=90.0,
                    corrosion_allowance_mm=3.0,
                    shell_thickness_mm=12.0,
                    pressure_class="Class 300",
                    hydrotest_pressure_bar=9.6,
                    support_type="skirt support",
                    support_variant="skirted vessel",
                    support_load_case="pressure + wind",
                    foundation_footprint_m2=0.0,
                    anchor_group_count=0,
                    local_shell_load_interaction_factor=0.8,
                    maintenance_platform_required=True,
                    platform_area_m2=0.0,
                )
            ]
        )

        issues = validate_mechanical_design_artifact(artifact)
        codes = {item.code for item in issues}

        self.assertIn("missing_foundation_footprint", codes)
        self.assertIn("missing_anchor_group_basis", codes)
        self.assertIn("missing_platform_area", codes)
        self.assertIn("invalid_local_shell_interaction", codes)

    def test_working_capital_validation_requires_procurement_timing_basis(self):
        model = WorkingCapitalModel(
            raw_material_days=18.0,
            product_inventory_days=10.0,
            receivable_days=32.0,
            payable_days=24.0,
            cash_buffer_days=8.0,
            working_capital_inr=10_000_000.0,
            precommissioning_inventory_inr=0.0,
            peak_working_capital_inr=9_000_000.0,
            peak_working_capital_month=0.0,
            procurement_timing_factor=0.0,
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_working_capital(model)
        codes = {item.code for item in issues}

        self.assertIn("missing_precommissioning_inventory_basis", codes)
        self.assertIn("missing_working_capital_timing_basis", codes)
        self.assertIn("invalid_peak_working_capital", codes)

    def test_financial_validation_requires_lender_coverage_basis(self):
        config = ProjectConfig(
            project_id="eg",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            require_india_only_data=True,
        )
        model = FinancialModel(
            currency="INR",
            annual_revenue=100_000_000.0,
            annual_operating_cost=70_000_000.0,
            gross_profit=30_000_000.0,
            working_capital=12_000_000.0,
            payback_years=5.0,
            npv=25_000_000.0,
            irr=18.0,
            profitability_index=1.2,
            break_even_fraction=0.68,
            total_project_funding_inr=180_000_000.0,
            construction_interest_during_construction_inr=8_000_000.0,
            minimum_dscr=1.05,
            average_dscr=1.18,
            llcr=0.0,
            plcr=0.0,
            annual_schedule=[
                {
                    "year": 1,
                    "debt_service_inr": 10_000_000.0,
                    "dscr": 1.05,
                }
            ],
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_financial_model(model, config)
        codes = {item.code for item in issues}

        self.assertIn("missing_lender_coverage_basis", codes)
        self.assertIn("weak_llcr_screening", codes)
        self.assertIn("weak_plcr_screening", codes)

    def test_financing_decision_alignment_requires_approval_for_breaches(self):
        decision = DecisionRecord(
            decision_id="financing_basis",
            context="seed",
            selected_candidate_id="debt_equity_70_30",
            selected_summary="seed",
            approval_required=False,
            citations=["s1"],
            assumptions=["seed"],
        )
        model = FinancialModel(
            currency="INR",
            annual_revenue=100_000_000.0,
            annual_operating_cost=70_000_000.0,
            gross_profit=30_000_000.0,
            working_capital=12_000_000.0,
            payback_years=5.0,
            npv=25_000_000.0,
            irr=18.0,
            profitability_index=1.2,
            break_even_fraction=0.68,
            total_project_funding_inr=180_000_000.0,
            construction_interest_during_construction_inr=8_000_000.0,
            minimum_dscr=1.05,
            average_dscr=1.18,
            llcr=1.12,
            plcr=1.24,
            selected_financing_candidate_id="debt_equity_70_30",
            covenant_breach_codes=["minimum_dscr_breach", "llcr_breach", "plcr_breach"],
            annual_schedule=[],
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_financing_decision_alignment(decision, model)
        codes = {item.code for item in issues}

        self.assertIn("financing_decision_missing_approval_flag", codes)

    def test_financing_decision_alignment_requires_approval_for_scenario_reversal(self):
        decision = DecisionRecord(
            decision_id="financing_basis",
            context="seed",
            selected_candidate_id="debt_equity_60_40",
            selected_summary="seed",
            approval_required=False,
            citations=["s1"],
            assumptions=["seed"],
        )
        model = FinancialModel(
            currency="INR",
            annual_revenue=100_000_000.0,
            annual_operating_cost=70_000_000.0,
            gross_profit=30_000_000.0,
            working_capital=12_000_000.0,
            payback_years=5.0,
            npv=25_000_000.0,
            irr=18.0,
            profitability_index=1.2,
            break_even_fraction=0.68,
            total_project_funding_inr=180_000_000.0,
            construction_interest_during_construction_inr=8_000_000.0,
            minimum_dscr=1.18,
            average_dscr=1.24,
            llcr=1.36,
            plcr=1.51,
            selected_financing_candidate_id="debt_equity_60_40",
            downside_scenario_name="conservative",
            downside_financing_candidate_id="conservative_50_50",
            financing_scenario_reversal=True,
            covenant_breach_codes=[],
            annual_schedule=[],
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_financing_decision_alignment(decision, model)
        codes = {item.code for item in issues}

        self.assertIn("financing_decision_missing_scenario_reversal_flag", codes)

    def test_separation_thermo_critics_warn_on_ideal_nonideal_service(self):
        route = RouteOption(
            route_id="acetic_acid_route",
            name="Carbonylation with polishing",
            rationale="Benchmark carbonylation route.",
            reaction_equation="A + B -> C",
            participants=[ReactionParticipant(name="Acetic Acid", formula="C2H4O2", coefficient=1.0, role="product", molecular_weight_g_mol=60.0, phase="liquid")],
            operating_temperature_c=180.0,
            operating_pressure_bar=25.0,
            residence_time_hr=1.0,
            yield_fraction=0.95,
            selectivity_fraction=0.93,
            route_score=90.0,
            scale_up_notes="Polishing train",
            citations=["s1"],
            assumptions=["seed"],
        )
        artifact = SeparationThermoArtifact(
            artifact_id="sep",
            route_id="acetic_acid_route",
            separation_family="distillation",
            system_pressure_bar=1.2,
            nominal_top_temp_c=90.0,
            nominal_bottom_temp_c=120.0,
            light_key="water",
            heavy_key="acetic acid",
            activity_model="ideal_raoult",
            missing_binary_pairs=["water|acetic acid"],
            fallback_notes=["Ideal fallback used."],
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )
        issues = validate_separation_thermo_critics(route, artifact)
        codes = {item.code for item in issues}
        self.assertIn("weak_nonideal_thermo_basis", codes)
        self.assertIn("missing_binary_interaction_coverage", codes)
        self.assertIn("separation_thermo_fallback_active", codes)

    def test_extraction_family_low_alpha_warns_instead_of_blocking(self):
        artifact = SeparationThermoArtifact(
            artifact_id="sep_extract",
            route_id="extract_route",
            separation_family="extraction",
            system_pressure_bar=1.2,
            nominal_top_temp_c=70.0,
            nominal_bottom_temp_c=95.0,
            light_key="ethanol",
            heavy_key="ethyl acetate",
            activity_model="ideal_raoult_missing_bip_fallback",
            relative_volatility=RelativeVolatilityEstimate(
                estimate_id="rv1",
                light_key_identifier_id="ethanol",
                heavy_key_identifier_id="ethyl_acetate",
                light_key="ethanol",
                heavy_key="ethyl acetate",
                average_alpha=0.85,
                top_alpha=0.82,
                bottom_alpha=0.88,
                method="screening",
            ),
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )
        issues = validate_separation_thermo_artifact(artifact)
        codes = {item.code for item in issues}
        self.assertIn("weak_extraction_partition_basis", codes)
        self.assertNotIn("invalid_relative_volatility", codes)

    def test_kinetics_method_critics_warn_on_complex_route_analogy(self):
        route = RouteOption(
            route_id="oxidation_route",
            name="Catalytic oxidation route",
            rationale="Catalytic oxidation benchmark route.",
            reaction_equation="A + O2 -> B",
            participants=[ReactionParticipant(name="Product", formula="B", coefficient=1.0, role="product", molecular_weight_g_mol=50.0, phase="liquid")],
            catalysts=["Pd catalyst"],
            operating_temperature_c=220.0,
            operating_pressure_bar=12.0,
            residence_time_hr=0.5,
            yield_fraction=0.85,
            selectivity_fraction=0.80,
            route_score=80.0,
            scale_up_notes="Catalytic oxidation",
            hazards=[RouteHazard(severity="high", description="runaway", safeguard="cooling")],
            citations=["s1"],
            assumptions=["seed"],
        )
        artifact = MethodSelectionArtifact(
            method_family="kinetics",
            decision=DecisionRecord(
                decision_id="kinetics_method",
                context="seed",
                selected_candidate_id="conservative_analogy",
                selected_summary="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )
        issues = validate_kinetics_method_critics(route, artifact)
        codes = {item.code for item in issues}
        self.assertIn("weak_kinetics_basis_for_complex_route", codes)
        self.assertIn("hazard_route_using_analogy_kinetics", codes)

    def test_route_selection_critics_warn_on_family_flags(self):
        selection = RouteSelectionArtifact(
            selected_route_id="oxidation_route",
            justification="Best available route under the current basis.",
            comparison_markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        families = RouteFamilyArtifact(
            profiles=[
                RouteFamilyProfile(
                    route_id="oxidation_route",
                    route_family_id="gas_oxidation",
                    family_label="Gas oxidation",
                    dominant_phase_pattern="gas-liquid",
                    primary_reactor_class="multi-bed catalytic reactor",
                    primary_separation_train="absorber -> stripper",
                    heat_recovery_style="waste heat boiler",
                    critic_flags=["limited public kinetics coverage"],
                    route_descriptors=["oxidation", "absorber-led"],
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_route_selection_critics(selection, families)
        codes = {item.code for item in issues}

        self.assertIn("route_family_critic_flags_present", codes)

    def test_separation_design_critics_block_impossible_distillation(self):
        choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="distillation_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        column = self._make_column(relative_volatility=1.02)

        issues = validate_separation_design_critics(choice, column)
        codes = {item.code for item in issues}

        self.assertIn("distillation_relative_volatility_too_low", codes)

    def test_equipment_applicability_escalates_family_fallback_and_service_mismatch(self):
        route = self._make_route()
        reactor_choice = DecisionRecord(
            decision_id="reactor_choice",
            context="seed",
            selected_candidate_id="fixed_bed_oxidizer",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        separation_choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="absorption_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        reactor = self._make_reactor(reactor_type="Stirred tank reactor")
        column = self._make_column(service="Distillation polishing")
        exchanger = self._make_exchanger()
        utility_network = self._make_utility_network()
        unit_family = UnitOperationFamilyArtifact(
            route_id="oxidation_route",
            route_family_id="gas_absorption_converter_train",
            reactor_candidates=[
                UnitOperationFamilyCandidate(
                    candidate_id="fixed_bed_oxidizer",
                    service_group="reactor",
                    family_label="Fixed-bed oxidizer",
                    description="seed",
                    applicability_status="fallback",
                    critic_flags=["high hotspot sensitivity"],
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            separation_candidates=[
                UnitOperationFamilyCandidate(
                    candidate_id="absorption_train",
                    service_group="separation",
                    family_label="Absorption train",
                    description="seed",
                    applicability_status="fallback",
                    critic_flags=["solvent makeup uncertainty"],
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            supporting_unit_operations=["absorber"],
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_equipment_applicability(
            route,
            reactor_choice,
            separation_choice,
            reactor,
            column,
            exchanger,
            utility_network,
            unit_family,
        )
        codes = {item.code for item in issues}

        self.assertIn("reactor_choice_nonpreferred_family_candidate", codes)
        self.assertIn("separation_choice_nonpreferred_family_candidate", codes)
        self.assertIn("reactor_design_service_mismatch", codes)
        self.assertIn("separation_design_service_mismatch", codes)

    def test_technical_economic_critics_block_absorber_cost_gaps(self):
        case = HeatIntegrationCase(
            case_id="recovery_case",
            title="Recovery",
            recovered_duty_kw=250.0,
            residual_hot_utility_kw=500.0,
            residual_cold_utility_kw=350.0,
            added_capex_inr=1_500_000.0,
            annual_savings_inr=300_000.0,
            payback_years=5.0,
            operability_penalty=0.1,
            safety_penalty=0.1,
            citations=["s1"],
            assumptions=["seed"],
        )
        column = self._make_column(service="Absorption / Stripper", absorber_packing_family="structured")
        utility_network = self._make_utility_network(case=case, selected_case_id="recovery_case", base_annual_utility_cost_inr=1_000_000.0)
        cost_model = self._make_cost_model(
            annual_utility_cost=1_000_000.0,
            annual_packing_replacement_cost=0.0,
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="oxidation_route",
            route_family_id="gas_absorption_converter_train",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_technical_economic_critics(column, utility_network, cost_model, unit_family)
        codes = {item.code for item in issues}

        self.assertIn("heat_recovery_without_economic_benefit", codes)
        self.assertIn("absorber_packing_cost_missing", codes)

    def test_technical_economic_critics_block_solids_cost_gaps(self):
        column = self._make_column(
            service="Crystallizer / Dryer",
            filter_area_m2=12.0,
            dryer_evaporation_load_kg_hr=400.0,
        )
        utility_network = self._make_utility_network()
        cost_model = self._make_cost_model(
            annual_filter_media_replacement_cost=0.0,
            annual_dryer_exhaust_treatment_cost=0.0,
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="sodium_bicarbonate_route",
            route_family_id="solids_carboxylation_train",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_technical_economic_critics(column, utility_network, cost_model, unit_family)
        codes = {item.code for item in issues}

        self.assertIn("filter_media_cost_missing", codes)
        self.assertIn("dryer_exhaust_cost_missing", codes)

    def test_unit_family_property_coverage_warns_for_hazard_sensitive_reactor(self):
        route = self._make_route()
        route.hazards = [RouteHazard(severity="high", description="runaway", safeguard="cooling")]
        reactor_choice = DecisionRecord(
            decision_id="reactor_choice",
            context="seed",
            selected_candidate_id="fixed_bed_oxidizer",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        separation_choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="distillation_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="oxidation_route",
            route_family_id="gas_absorption_converter_train",
            citations=["s1"],
            assumptions=["seed"],
        )
        property_packages = self._make_property_packages()

        issues = validate_unit_family_property_coverage(
            route,
            reactor_choice,
            separation_choice,
            unit_family,
            property_packages,
        )
        codes = {item.code for item in issues}

        self.assertIn("reactor_hazard_property_coverage_weak", codes)

    def test_unit_family_property_coverage_blocks_without_henry_basis(self):
        route = self._make_route("sulfuric_route")
        reactor_choice = DecisionRecord(
            decision_id="reactor_choice",
            context="seed",
            selected_candidate_id="converter",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        separation_choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="packed_absorption_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="sulfuric_route",
            route_family_id="gas_absorption_converter_train",
            citations=["s1"],
            assumptions=["seed"],
        )
        property_packages = self._make_property_packages(unresolved_henry_pairs=["so3|water"])

        issues = validate_unit_family_property_coverage(
            route,
            reactor_choice,
            separation_choice,
            unit_family,
            property_packages,
        )
        issue = next(item for item in issues if item.code == "absorption_family_property_coverage_weak")

        self.assertEqual(issue.severity.value, "blocked")

    def test_unit_family_property_coverage_warns_with_partial_solids_basis(self):
        route = self._make_route("solids_route")
        reactor_choice = DecisionRecord(
            decision_id="reactor_choice",
            context="seed",
            selected_candidate_id="slurry_reactor",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        separation_choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="crystallizer_filter_dryer_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="solids_route",
            route_family_id="solids_carboxylation_train",
            citations=["s1"],
            assumptions=["seed"],
        )
        property_packages = self._make_property_packages(
            solubility_curves=[
                SolubilityCurve(
                    curve_id="sol_curve",
                    solute_component_id="product",
                    solvent_component_id="water",
                    solute_component_name="Product",
                    solvent_component_name="Water",
                    parameters={"a": 0.10, "b": 0.001},
                    source_ids=["s1"],
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            unresolved_solubility_pairs=["product|mother_liquor"],
        )

        issues = validate_unit_family_property_coverage(
            route,
            reactor_choice,
            separation_choice,
            unit_family,
            property_packages,
        )
        issue = next(item for item in issues if item.code == "solids_family_property_coverage_weak")

        self.assertEqual(issue.severity.value, "warning")

    def test_route_economic_critics_warn_on_counterfactual_rejection_of_recovery(self):
        route_selection = RouteSelectionArtifact(
            selected_route_id="oxidation_route",
            justification="seed",
            comparison_markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        case = HeatIntegrationCase(
            case_id="recovery_case",
            title="Recovery",
            recovered_duty_kw=250.0,
            residual_hot_utility_kw=500.0,
            residual_cold_utility_kw=350.0,
            added_capex_inr=1_500_000.0,
            annual_savings_inr=300_000.0,
            payback_years=5.0,
            operability_penalty=0.1,
            safety_penalty=0.1,
            citations=["s1"],
            assumptions=["seed"],
        )
        utility_network = self._make_utility_network(
            case=case,
            selected_case_id="recovery_case",
            base_annual_utility_cost_inr=1_000_000.0,
            selected_annual_utility_cost_inr=800_000.0,
        )
        cost_model = self._make_cost_model(integration_capex_inr=1_500_000.0)
        economic_basis = DecisionRecord(
            decision_id="economic_basis",
            context="seed",
            selected_candidate_id="no_recovery_counterfactual",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_route_economic_critics(
            route_selection,
            utility_network,
            cost_model,
            economic_basis,
        )
        codes = {item.code for item in issues}

        self.assertIn("economic_basis_counterfactual_selected", codes)
        self.assertIn("economic_basis_rejects_selected_recovery", codes)

    def test_reactor_hazard_basis_critics_warn_on_high_runaway_and_batch_mode(self):
        route = self._make_route()
        route.hazards = [RouteHazard(severity="high", description="runaway", safeguard="cooling")]
        reactor_choice = DecisionRecord(
            decision_id="reactor_choice",
            context="seed",
            selected_candidate_id="fixed_bed_oxidizer",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        reactor = self._make_reactor(
            heat_removal_margin_fraction=0.06,
            thermal_stability_score=48.0,
            runaway_risk_label="high",
        )
        operations = self._make_operations_planning(
            recommended_operating_mode="batch",
            restart_loss_fraction=0.010,
        )

        issues = validate_reactor_hazard_basis_critics(route, reactor_choice, reactor, operations)
        codes = {item.code for item in issues}

        self.assertIn("reactor_hazard_basis_high_runaway_risk", codes)
        self.assertIn("reactor_hazard_basis_unsupported", codes)
        self.assertIn("hazard_route_batch_mode_selected", codes)
        self.assertIn("hazard_route_restart_loss_high", codes)

    def test_financing_operability_critics_warn_on_leverage_and_operating_tension(self):
        financing_basis = DecisionRecord(
            decision_id="financing_basis",
            context="seed",
            selected_candidate_id="debt_equity_70_30",
            selected_summary="70:30 debt-equity basis",
            citations=["s1"],
            assumptions=["seed"],
        )
        economic_basis = DecisionRecord(
            decision_id="economic_basis",
            context="seed",
            selected_candidate_id="no_recovery_counterfactual",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        financial_model = FinancialModel(
            currency="INR",
            annual_revenue=100_000_000.0,
            annual_operating_cost=72_000_000.0,
            gross_profit=28_000_000.0,
            working_capital=12_000_000.0,
            payback_years=5.0,
            npv=20_000_000.0,
            irr=16.0,
            profitability_index=1.1,
            break_even_fraction=0.70,
            total_project_funding_inr=180_000_000.0,
            construction_interest_during_construction_inr=8_000_000.0,
            minimum_dscr=1.04,
            average_dscr=1.16,
            llcr=1.20,
            plcr=1.32,
            selected_financing_candidate_id="debt_equity_70_30",
            covenant_breach_codes=["minimum_dscr_breach"],
            annual_schedule=[],
            citations=["s1"],
            assumptions=["seed"],
        )
        operations = self._make_operations_planning(
            recommended_operating_mode="continuous",
            throughput_loss_fraction=0.028,
            restart_loss_fraction=0.006,
        )
        reactor = self._make_reactor(runaway_risk_label="high")
        case = HeatIntegrationCase(
            case_id="recovery_case",
            title="Recovery",
            recovered_duty_kw=250.0,
            residual_hot_utility_kw=500.0,
            residual_cold_utility_kw=350.0,
            added_capex_inr=1_500_000.0,
            annual_savings_inr=300_000.0,
            payback_years=5.0,
            operability_penalty=0.1,
            safety_penalty=0.1,
            citations=["s1"],
            assumptions=["seed"],
        )
        utility_network = self._make_utility_network(
            case=case,
            selected_case_id="recovery_case",
        )

        issues = validate_financing_operability_critics(
            financing_basis,
            economic_basis,
            financial_model,
            operations,
            reactor,
            utility_network,
        )
        codes = {item.code for item in issues}

        self.assertIn("financing_operability_tension", codes)
        self.assertIn("hazard_route_high_leverage_financing", codes)
        self.assertIn("operating_mode_integrated_economics_tension", codes)

    def test_architecture_package_critics_compound_fallback_thermo_and_analogy_kinetics(self):
        route = self._make_route()
        route.hazards = [RouteHazard(severity="high", description="runaway", safeguard="cooling")]
        separation_choice = DecisionRecord(
            decision_id="separation_choice",
            context="seed",
            selected_candidate_id="distillation_train",
            selected_summary="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        unit_family = UnitOperationFamilyArtifact(
            route_id="oxidation_route",
            route_family_id="continuous_liquid_organic_train",
            citations=["s1"],
            assumptions=["seed"],
        )
        separation_thermo = SeparationThermoArtifact(
            artifact_id="sep",
            route_id="oxidation_route",
            separation_family="distillation",
            system_pressure_bar=1.2,
            nominal_top_temp_c=90.0,
            nominal_bottom_temp_c=120.0,
            light_key="water",
            heavy_key="product",
            activity_model="ideal_raoult",
            missing_binary_pairs=["water|product"],
            fallback_notes=["Ideal fallback used."],
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )
        kinetics_method = MethodSelectionArtifact(
            method_family="kinetics",
            decision=DecisionRecord(
                decision_id="kinetics_method",
                context="seed",
                selected_candidate_id="conservative_analogy",
                selected_summary="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )
        property_packages = self._make_property_packages(unresolved_binary_pairs=["water|product"])

        issues = validate_architecture_package_critics(
            route,
            separation_choice,
            unit_family,
            separation_thermo,
            kinetics_method,
            None,
            property_packages,
        )
        codes = {item.code for item in issues}

        self.assertIn("architecture_package_fallback_thermo", codes)
        self.assertIn("architecture_package_weak_kinetics_basis", codes)
