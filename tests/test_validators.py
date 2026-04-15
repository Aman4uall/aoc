import unittest

from aoc.diagrams import build_diagram_domain_packs, build_diagram_symbol_library, build_diagram_target_profile
from aoc.models import (
    BACDrawingPackageArtifact,
    BACDrawingRegisterRow,
    BACDiagramBenchmarkArtifact,
    BACDiagramBenchmarkRow,
    BACRenderingAuditArtifact,
    BACRenderingAuditRow,
    ColumnDesign,
    CostModel,
    DecisionRecord,
    DiagramEdgeRole,
    DiagramEntityKind,
    DiagramInterModuleConnector,
    DiagramLabel,
    DiagramLevel,
    DiagramModuleArtifact,
    DiagramNode,
    DiagramModulePlacement,
    DiagramModulePort,
    DiagramModuleSpec,
    DiagramSheet,
    DiagramSymbolLibraryArtifact,
    DiagramPortSide,
    DiagramSheetComposition,
    DiagramSheetCompositionArtifact,
    DiagramSymbolPolicy,
    FinancialModel,
    GeographicScope,
    FlowsheetGraph,
    FlowsheetNode,
    HazopNode,
    HazopNodeRegister,
    HeatExchangerDesign,
    HeatIntegrationCase,
    MechanicalComponentDesign,
    MechanicalDesignArtifact,
    MethodSelectionArtifact,
    OperationsPlanningArtifact,
    ProcessTemplate,
    PlantDiagramConnection,
    PlantDiagramEntity,
    PlantDiagramSemanticsArtifact,
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
    validate_diagram_module_artifact,
    validate_diagram_module_symbols_against_library,
    validate_diagram_target_profile_against_domain_packs,
    validate_bac_pfd_process_purity,
    validate_bac_bfd_structure,
    validate_bac_diagram_benchmark_artifact,
    validate_bac_drawing_package_artifact,
    validate_bac_rendering_audit_artifact,
    validate_bac_pid_cluster_coverage,
    validate_diagram_drafting_sheets,
    validate_diagram_sheet_composition_artifact,
    validate_plant_diagram_semantics_against_target_profile,
    validate_diagram_semantics_against_symbol_library,
    validate_diagram_symbol_library,
    validate_equipment_applicability,
    validate_financial_model,
    validate_financing_decision_alignment,
    validate_financing_operability_critics,
    validate_hazop_node_register,
    validate_kinetics_method_critics,
    validate_mechanical_design_artifact,
    validate_reactor_hazard_basis_critics,
    validate_research_bundle,
    validate_route_economic_critics,
    validate_route_selection_critics,
    validate_separation_design_critics,
    validate_separation_thermo_artifact,
    validate_separation_thermo_critics,
    validate_plant_diagram_semantics,
    validate_technical_economic_critics,
    validate_unit_family_property_coverage,
    validate_working_capital,
)


class ValidatorTests(unittest.TestCase):
    def _make_semantics(self, **overrides) -> PlantDiagramSemanticsArtifact:
        data = {
            "diagram_id": "demo_pfd",
            "route_id": "route_1",
            "entities": [
                PlantDiagramEntity(
                    entity_id="u_feed",
                    kind=DiagramEntityKind.UNIT,
                    label="Feed Tank",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="TK-101",
                    section_id="feed",
                ),
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="R-101",
                    section_id="reaction",
                ),
            ],
            "connections": [
                PlantDiagramConnection(
                    connection_id="c_main",
                    role=DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.PFD,
                    source_entity_id="u_feed",
                    target_entity_id="u_rxn",
                    stream_id="S-101",
                )
            ],
            "section_order": ["feed", "reaction"],
            "markdown": "seed",
            "citations": ["s1"],
            "assumptions": ["seed"],
        }
        data.update(overrides)
        return PlantDiagramSemanticsArtifact(**data)

    def test_hazop_validation_requires_safeguards_and_tracks_recommendations(self):
        register = HazopNodeRegister(
            nodes=[
                HazopNode(
                    node_id="R-101",
                    node_family="reactor",
                    design_intent="Maintain safe conversion.",
                    parameter="Temperature",
                    guide_word="More",
                    deviation="Higher than intended reactor temperature",
                    causes=["Cooling failure"],
                    consequences=["Runaway tendency"],
                    safeguards=[],
                    linked_control_loops=["TIC-R-101"],
                    consequence_severity="high",
                    recommendation_priority="high",
                    recommendation_status="open",
                    recommendation="Add HH trip.",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            coverage_summary="1 node",
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_hazop_node_register(register)

        self.assertTrue(any(issue.code == "hazop_missing_safeguards" for issue in issues))

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

    def test_validate_plant_diagram_semantics_blocks_pid_content_in_pfd(self):
        artifact = self._make_semantics(
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="R-101",
                ),
                PlantDiagramEntity(
                    entity_id="v_1",
                    kind=DiagramEntityKind.VALVE,
                    label="Control Valve",
                    diagram_level=DiagramLevel.PFD,
                ),
            ],
            connections=[],
        )

        issues = validate_plant_diagram_semantics(artifact)

        self.assertTrue(any(issue.code == "diagram_semantics_pid_content_in_pfd" for issue in issues))

    def test_validate_plant_diagram_semantics_blocks_missing_connection_entities(self):
        artifact = self._make_semantics(
            connections=[
                PlantDiagramConnection(
                    connection_id="c_bad",
                    role=DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.PFD,
                    source_entity_id="u_feed",
                    target_entity_id="missing_unit",
                )
            ]
        )

        issues = validate_plant_diagram_semantics(artifact)

        self.assertTrue(any(issue.code == "diagram_semantics_connection_missing_entity" for issue in issues))

    def test_validate_diagram_module_artifact_blocks_pfd_pid_mixing(self):
        semantics = self._make_semantics(
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="R-101",
                ),
                PlantDiagramEntity(
                    entity_id="i_tic",
                    kind=DiagramEntityKind.INSTRUMENT,
                    label="TIC",
                    diagram_level=DiagramLevel.PFD,
                    instrument_id="TIC-101",
                ),
            ],
            connections=[],
        )
        modules = DiagramModuleArtifact(
            diagram_id="demo_pfd",
            route_id="route_1",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(
                    module_id="pfd_reaction",
                    module_kind=DiagramLevel.PFD,
                    title="Reaction",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["u_rxn", "i_tic"],
                    allowed_edge_roles=[DiagramEdgeRole.PROCESS],
                    boundary_ports=[],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_diagram_module_artifact(modules, semantics)

        self.assertTrue(any(issue.code == "diagram_module_pfd_contains_pid_content" for issue in issues))

    def test_validate_diagram_sheet_composition_blocks_unknown_ports(self):
        semantics = self._make_semantics()
        modules = DiagramModuleArtifact(
            diagram_id="demo_pfd",
            route_id="route_1",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(
                    module_id="mod_a",
                    module_kind=DiagramLevel.PFD,
                    title="Feed",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["u_feed"],
                    connection_ids=[],
                    boundary_ports=[
                        DiagramModulePort(
                            port_id="port_a_out",
                            entity_id="u_feed",
                            connection_role=DiagramEdgeRole.PROCESS,
                            side=DiagramPortSide.RIGHT,
                        )
                    ],
                ),
                DiagramModuleSpec(
                    module_id="mod_b",
                    module_kind=DiagramLevel.PFD,
                    title="Reaction",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["u_rxn"],
                    connection_ids=[],
                    boundary_ports=[
                        DiagramModulePort(
                            port_id="port_b_in",
                            entity_id="u_rxn",
                            connection_role=DiagramEdgeRole.PROCESS,
                            side=DiagramPortSide.LEFT,
                        )
                    ],
                ),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        composition = DiagramSheetCompositionArtifact(
            diagram_id="demo_pfd",
            route_id="route_1",
            diagram_level=DiagramLevel.PFD,
            sheets=[
                DiagramSheetComposition(
                    sheet_id="sheet_1",
                    title="PFD Sheet 1",
                    diagram_level=DiagramLevel.PFD,
                    module_placements=[
                        DiagramModulePlacement(module_id="mod_a", sheet_id="sheet_1", x=0, y=0, width=200, height=120),
                        DiagramModulePlacement(module_id="mod_b", sheet_id="sheet_1", x=250, y=0, width=200, height=120),
                    ],
                    connectors=[
                        DiagramInterModuleConnector(
                            connector_id="conn_1",
                            role=DiagramEdgeRole.PROCESS,
                            source_module_id="mod_a",
                            source_port_id="missing_port",
                            target_module_id="mod_b",
                            target_port_id="port_b_in",
                        )
                    ],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_diagram_sheet_composition_artifact(composition, modules)

        self.assertTrue(any(issue.code == "diagram_sheet_connector_missing_port" for issue in issues))

    def test_validate_diagram_drafting_sheets_blocks_missing_title_block_duplicates_and_overlap(self):
        sheets = [
            DiagramSheet(
                sheet_id="sheet_1",
                title="Process Flow Diagram",
                width_px=900,
                height_px=500,
                drawing_number="PFD-001",
                sheet_number="1 of 2",
                revision_date="2026-04-12",
                node_ids=["R-101"],
                svg="<svg><text>No title block</text></svg>",
            ),
            DiagramSheet(
                sheet_id="sheet_2",
                title="Process Flow Diagram",
                width_px=900,
                height_px=500,
                drawing_number="PFD-001",
                sheet_number="1 of 2",
                revision_date="",
                svg="<svg><text>DRAFTING TITLE BLOCK</text></svg>",
            ),
        ]
        nodes = [DiagramNode(node_id="R-101", label="Reactor", node_family="reactor", x=470, y=395, width=160, height=80)]

        issues = validate_diagram_drafting_sheets(sheets, nodes=nodes)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("diagram_title_block_missing", issue_codes)
        self.assertIn("diagram_duplicate_drawing_number", issue_codes)
        self.assertIn("diagram_duplicate_sheet_number", issue_codes)
        self.assertIn("diagram_drafting_metadata_missing", issue_codes)
        self.assertIn("diagram_title_block_overlap", issue_codes)

    def test_validate_bac_pfd_process_purity_blocks_control_and_utility_annotations(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        nodes = [
            DiagramNode(
                node_id="R-101",
                label="Reactor",
                node_family="reactor",
                labels=[
                    DiagramLabel(text="R-101", kind="primary"),
                    DiagramLabel(text="Jacketed CSTR Reactor", kind="secondary"),
                    DiagramLabel(text="TIC-101", kind="utility"),
                    DiagramLabel(text="+250 kW heat", kind="utility"),
                ],
            ),
            DiagramNode(node_id="CV-101", label="Control Valve", node_family="valve"),
        ]

        issues = validate_bac_pfd_process_purity(nodes, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_pfd_contains_control_annotation", issue_codes)
        self.assertIn("bac_pfd_contains_utility_duty_annotation", issue_codes)
        self.assertIn("bac_pfd_contains_pid_symbol_family", issue_codes)

    def test_validate_bac_bfd_structure_blocks_wrong_order_and_labels(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        artifact = PlantDiagramSemanticsArtifact(
            diagram_id="bac_bfd_semantics",
            route_id="bac_route",
            entities=[
                PlantDiagramEntity(entity_id="s1", kind=DiagramEntityKind.SECTION, label="Reaction", diagram_level=DiagramLevel.BFD, section_id="reaction"),
                PlantDiagramEntity(entity_id="s2", kind=DiagramEntityKind.SECTION, label="Feed Prep", diagram_level=DiagramLevel.BFD, section_id="feed preparation"),
                PlantDiagramEntity(entity_id="s3", kind=DiagramEntityKind.SECTION, label="Cleanup", diagram_level=DiagramLevel.BFD, section_id="cleanup"),
            ],
            connections=[],
            section_order=["reaction", "feed preparation", "cleanup"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_bac_bfd_structure(artifact, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_bfd_section_order_mismatch", issue_codes)
        self.assertIn("bac_bfd_missing_required_sections", issue_codes)
        self.assertIn("bac_bfd_section_label_mismatch", issue_codes)

    def test_validate_bac_pid_cluster_coverage_blocks_missing_storage_cluster(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_cov",
            route_id="route_bac_pid_cov",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        artifact = PlantDiagramSemanticsArtifact(
            diagram_id="bac_pid_semantics",
            route_id="route_bac_pid_cov",
            entities=[
                PlantDiagramEntity(entity_id="pid_unit_r101", kind=DiagramEntityKind.UNIT, label="Reactor", diagram_level=DiagramLevel.PID_LITE, section_id="reaction", unit_id="R-101"),
                PlantDiagramEntity(entity_id="pid_unit_pu201", kind=DiagramEntityKind.UNIT, label="Purification Column", diagram_level=DiagramLevel.PID_LITE, section_id="purification", unit_id="PU-201"),
            ],
            connections=[],
            section_order=["reaction", "purification"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_bac_pid_cluster_coverage(artifact, flowsheet_graph, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_pid_missing_required_clusters", issue_codes)
        self.assertIn("bac_pid_missing_relief_coverage", issue_codes)

    def test_validate_bac_diagram_benchmark_artifact_flags_failed_rows(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        artifact = BACDiagramBenchmarkArtifact(
            artifact_id="bac_benchmark",
            route_id="route_bac",
            overall_status="blocked",
            rows=[
                BACDiagramBenchmarkRow(diagram_kind="bfd", status="pass", summary="ok"),
                BACDiagramBenchmarkRow(diagram_kind="pfd", status="fail", summary="PFD drift"),
                BACDiagramBenchmarkRow(diagram_kind="pid", status="pass", summary="ok"),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_bac_diagram_benchmark_artifact(artifact, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_diagram_benchmark_missing_rows", issue_codes)
        self.assertIn("bac_diagram_benchmark_blocked", issue_codes)
        self.assertIn("bac_diagram_benchmark_pfd_failed", issue_codes)

    def test_validate_bac_drawing_package_artifact_flags_missing_approver(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        artifact = BACDrawingPackageArtifact(
            artifact_id="bac_package",
            route_id="route_bac",
            overall_status="complete",
            benchmark_status="complete",
            review_workflow_status="approved",
            register_rows=[
                BACDrawingRegisterRow(diagram_kind="bfd", sheet_id="sheet_1", title="BFD", issue_status="For Review"),
                BACDrawingRegisterRow(diagram_kind="pfd", sheet_id="sheet_2", title="PFD", issue_status="Approved"),
                BACDrawingRegisterRow(diagram_kind="pid", sheet_id="sheet_3", title="PID", issue_status="Approved"),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_bac_drawing_package_artifact(artifact, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_drawing_package_missing_approver", issue_codes)
        self.assertIn("bac_drawing_package_sheet_missing_approver", issue_codes)

    def test_validate_bac_rendering_audit_artifact_flags_failed_rows(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        artifact = BACRenderingAuditArtifact(
            artifact_id="bac_rendering_audit",
            route_id="route_bac",
            overall_status="blocked",
            rows=[
                BACRenderingAuditRow(diagram_kind="bfd", status="pass", summary="ok"),
                BACRenderingAuditRow(diagram_kind="pfd", status="fail", summary="PFD routing failed"),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_bac_rendering_audit_artifact(artifact, target)
        issue_codes = {issue.code for issue in issues}

        self.assertIn("bac_rendering_audit_missing_rows", issue_codes)
        self.assertIn("bac_rendering_audit_blocked", issue_codes)
        self.assertIn("bac_rendering_audit_pfd_failed", issue_codes)

    def test_validate_diagram_symbol_library_accepts_canonical_library(self):
        library = build_diagram_symbol_library()

        issues = validate_diagram_symbol_library(library)

        self.assertFalse(issues)

    def test_phase11_symbol_library_includes_richer_pid_lite_symbols(self):
        library = build_diagram_symbol_library()

        pid_keys = {symbol.symbol_key for symbol in library.symbols if symbol.diagram_level == DiagramLevel.PID_LITE}

        self.assertTrue(
            {
                "pid_unit",
                "pid_indicator",
                "pid_transmitter",
                "pid_controller",
                "pid_manual_valve",
                "pid_control_valve",
                "pid_relief_valve",
            }.issubset(pid_keys)
        )

    def test_phase11_validate_pid_lite_semantics_requires_attachment_function_and_line_class(self):
        artifact = PlantDiagramSemanticsArtifact(
            diagram_id="demo_pid",
            route_id="route_1",
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PID_LITE,
                    unit_id="R-101",
                    symbol_key="pid_unit",
                ),
                PlantDiagramEntity(
                    entity_id="i_tit",
                    kind=DiagramEntityKind.INSTRUMENT,
                    label="TIT-101",
                    diagram_level=DiagramLevel.PID_LITE,
                    instrument_id="TIT-101",
                    symbol_key="pid_transmitter",
                ),
            ],
            connections=[
                PlantDiagramConnection(
                    connection_id="pid_line_1",
                    role=DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.PID_LITE,
                    source_entity_id="u_rxn",
                    target_entity_id="i_tit",
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_plant_diagram_semantics(artifact)
        codes = {issue.code for issue in issues}

        self.assertIn("diagram_semantics_pid_entity_missing_attachment", codes)
        self.assertIn("diagram_semantics_pid_instrument_missing_function", codes)
        self.assertIn("diagram_semantics_pid_material_edge_to_instrument", codes)
        self.assertIn("diagram_semantics_pid_line_missing_class", codes)

    def test_phase11_validate_pid_lite_controller_requires_loop_id(self):
        artifact = PlantDiagramSemanticsArtifact(
            diagram_id="demo_pid",
            route_id="route_1",
            entities=[
                PlantDiagramEntity(
                    entity_id="u_sep",
                    kind=DiagramEntityKind.UNIT,
                    label="Separator",
                    diagram_level=DiagramLevel.PID_LITE,
                    unit_id="V-101",
                    symbol_key="pid_unit",
                ),
                PlantDiagramEntity(
                    entity_id="i_tic",
                    kind=DiagramEntityKind.INSTRUMENT,
                    label="TIC-101",
                    diagram_level=DiagramLevel.PID_LITE,
                    instrument_id="TIC-101",
                    symbol_key="pid_controller",
                    attached_to_entity_id="u_sep",
                    pid_function="temperature_controller",
                ),
            ],
            connections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_plant_diagram_semantics(artifact)

        self.assertTrue(any(issue.code == "diagram_semantics_pid_controller_missing_loop_id" for issue in issues))

    def test_phase11_validate_pid_lite_module_requires_isolated_unit_cluster(self):
        semantics = PlantDiagramSemanticsArtifact(
            diagram_id="demo_pid",
            route_id="route_1",
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PID_LITE,
                    unit_id="R-101",
                    symbol_key="pid_unit",
                ),
                PlantDiagramEntity(
                    entity_id="v_fcv",
                    kind=DiagramEntityKind.VALVE,
                    label="FCV-101",
                    diagram_level=DiagramLevel.PID_LITE,
                    symbol_key="pid_control_valve",
                    attached_to_entity_id="u_rxn",
                    pid_function="flow_control_valve",
                ),
            ],
            connections=[
                PlantDiagramConnection(
                    connection_id="c_pid",
                    role=DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.PID_LITE,
                    source_entity_id="u_rxn",
                    target_entity_id="v_fcv",
                    line_class="process_liquid",
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        modules = DiagramModuleArtifact(
            diagram_id="demo_pid",
            route_id="route_1",
            module_kind=DiagramLevel.PID_LITE,
            modules=[
                DiagramModuleSpec(
                    module_id="pid_cluster_1",
                    module_kind=DiagramLevel.PID_LITE,
                    title="Reactor Cluster",
                    symbol_policy=DiagramSymbolPolicy.PID_LITE_ONLY,
                    entity_ids=["u_rxn", "v_fcv"],
                    connection_ids=["c_pid"],
                    must_be_isolated=False,
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_diagram_module_artifact(modules, semantics)

        self.assertTrue(any(issue.code == "diagram_module_pid_not_isolated" for issue in issues))

    def test_validate_diagram_semantics_against_symbol_library_blocks_wrong_level_symbol(self):
        library = build_diagram_symbol_library()
        artifact = self._make_semantics(
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="R-101",
                    symbol_key="control_unit_ref",
                )
            ],
            connections=[],
        )

        issues = validate_diagram_semantics_against_symbol_library(artifact, library)

        self.assertTrue(any(issue.code == "diagram_semantics_symbol_level_mismatch" for issue in issues))

    def test_validate_diagram_semantics_against_symbol_library_blocks_edge_role_without_policy(self):
        library = build_diagram_symbol_library()
        artifact = self._make_semantics(
            connections=[
                PlantDiagramConnection(
                    connection_id="c_bad_signal",
                    role=DiagramEdgeRole.CONTROL_SIGNAL,
                    diagram_level=DiagramLevel.PFD,
                    source_entity_id="u_feed",
                    target_entity_id="u_rxn",
                )
            ]
        )

        issues = validate_diagram_semantics_against_symbol_library(artifact, library)

        self.assertTrue(any(issue.code == "diagram_semantics_edge_role_not_allowed_by_policy" for issue in issues))

    def test_validate_diagram_module_symbols_against_library_blocks_disallowed_symbol(self):
        library = build_diagram_symbol_library()
        semantics = self._make_semantics(
            entities=[
                PlantDiagramEntity(
                    entity_id="u_rxn",
                    kind=DiagramEntityKind.UNIT,
                    label="Reactor",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="R-101",
                    symbol_key="control_unit_ref",
                )
            ],
            connections=[],
        )
        modules = DiagramModuleArtifact(
            diagram_id="demo_pfd",
            route_id="route_1",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(
                    module_id="pfd_reaction",
                    module_kind=DiagramLevel.PFD,
                    title="Reaction",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["u_rxn"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_diagram_module_symbols_against_library(modules, semantics, library)

        self.assertTrue(any(issue.code == "diagram_module_symbol_not_allowed_by_library" for issue in issues))

    def test_validate_diagram_symbol_library_blocks_missing_level_policy(self):
        library = build_diagram_symbol_library()
        broken = DiagramSymbolLibraryArtifact(
            library_id=library.library_id,
            library_name=library.library_name,
            symbols=library.symbols,
            edge_styles=library.edge_styles,
            level_policies=[policy for policy in library.level_policies if policy.diagram_level != DiagramLevel.CONTROL],
            markdown=library.markdown,
            citations=library.citations,
            assumptions=library.assumptions,
        )

        issues = validate_diagram_symbol_library(broken)

        self.assertTrue(any(issue.code == "diagram_symbol_library_missing_level_policy" for issue in issues))

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

    def test_validate_diagram_target_profile_against_domain_packs_accepts_selected_pack(self):
        domain_packs = build_diagram_domain_packs()
        target = build_diagram_target_profile(ProjectBasis(target_product="Ethylene Oxide", capacity_tpa=1000, target_purity_wt_pct=99.0))

        issues = validate_diagram_target_profile_against_domain_packs(target, domain_packs)

        self.assertFalse(issues)

    def test_validate_diagram_target_profile_against_domain_packs_warns_for_symbol_policy_drift(self):
        domain_packs = build_diagram_domain_packs()
        target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))
        target.allowed_pfd_symbol_keys = target.allowed_pfd_symbol_keys + ["pfd_column"]

        issues = validate_diagram_target_profile_against_domain_packs(target, domain_packs)

        self.assertTrue(any(issue.code == "diagram_target_domain_pack_symbol_policy_mismatch" for issue in issues))

    def test_validate_plant_diagram_semantics_against_target_profile_warns_for_domain_pack_mismatch(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))
        artifact = PlantDiagramSemanticsArtifact(
            diagram_id="utility_pack_semantics",
            route_id="route_utility_pack",
            entities=[
                PlantDiagramEntity(
                    entity_id="c1",
                    kind=DiagramEntityKind.UNIT,
                    label="Main Column",
                    diagram_level=DiagramLevel.PFD,
                    unit_id="C-101",
                    metadata={"template_family": "column"},
                )
            ],
            connections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        issues = validate_plant_diagram_semantics_against_target_profile(artifact, target)

        self.assertTrue(any(issue.code == "diagram_target_missing_required_pfd_family" for issue in issues))
        self.assertTrue(any(issue.code == "diagram_target_unexpected_pfd_family_for_domain_pack" for issue in issues))
