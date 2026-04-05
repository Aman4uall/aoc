from __future__ import annotations

import re

from aoc.models import (
    BACImpurityLedgerArtifact,
    BACImpurityLedgerItem,
    BACImpurityItem,
    BACImpurityModelArtifact,
    BACPurificationSection,
    BACPurificationSectionArtifact,
    BACPseudoComponentBasisArtifact,
    BinaryPairCoverageArtifact,
    BinaryPairCoverageRow,
    ClaimGraphArtifact,
    ClaimStatus,
    CommercialProductBasisArtifact,
    ControlPlanArtifact,
    DataGapItem,
    DataGapRegistryArtifact,
    DataRealityAuditArtifact,
    DataRealityAuditRow,
    DataRealityClass,
    DatumRequirementRule,
    DesignConfidenceArtifact,
    EconomicGapItem,
    EconomicInputRealityArtifact,
    EconomicCoverageDecision,
    EstimationMethodTag,
    EstimationPolicy,
    FlowsheetBlueprintArtifact,
    FlowsheetCase,
    FlowsheetIntentArtifact,
    FlowsheetIntentItem,
    InferenceQuestion,
    InferenceQuestionQueueArtifact,
    KineticAssessmentArtifact,
    KineticsAdmissibilityArtifact,
    KineticsStepAdmissibility,
    MethodSelectionArtifact,
    ProjectConfig,
    ProvenanceTag,
    QuestionAnswer,
    ReactionNetworkRoute,
    ReactionNetworkV2Artifact,
    RevisionLedgerArtifact,
    RevisionTicket,
    RouteChemistryArtifact,
    RouteProcessClaimRecord,
    RouteProcessClaimsArtifact,
    RouteScreeningArtifact,
    RouteSelectionArtifact,
    RouteSelectionComparisonArtifact,
    SectionThermoAssignmentArtifact,
    SectionThermoAssignmentRow,
    ScientificClaim,
    ScientificClaimProvenance,
    ScientificConfidence,
    ScientificGateEntry,
    ScientificGateMatrixArtifact,
    ScientificGateStatus,
    SeparationDutyItem,
    SolveResult,
    SpeciesResolutionArtifact,
    SpeciesResolutionRecord,
    StreamTable,
    RecycleBasisArtifact,
    RecycleBasisLoop,
    ThermoAdmissibilityArtifact,
    ThermoAssessmentArtifact,
    ThermoSectionAdmissibility,
    TopologyCandidateArtifact,
    TopologyCandidateRecord,
    UnitTrainConsistencyArtifact,
    UnitTrainConsistencyRow,
    UnitDesignConfidence,
    UtilitySummaryArtifact,
    MarketAssessmentArtifact,
    ProductProfileArtifact,
    EquipmentListArtifact,
    ColumnDesign,
    ReactorDesign,
    CostModel,
    EnergyBalance,
    KineticBasisArtifact,
    MarketAssessmentArtifact,
    MethodBasisRecord,
    MissingDataAcceptanceArtifact,
    MissingDataValidationIssue,
    ProjectBasis,
    ReactorBasisConfidenceArtifact,
    ReportAcceptanceStatus,
)
from aoc.properties.models import PropertyMethodDecision, PropertyPackageArtifact, SeparationThermoArtifact
from aoc.route_families import RouteFamilyArtifact, profile_for_route


_NONCHEMICAL_TOKEN_RE = re.compile(r"^\W*$|^\d+([./-]\d+)*$|^\d+%$")
_NOISE_TOKENS = {
    "page",
    "pages",
    "table",
    "figure",
    "fig",
    "yield",
    "pressure",
    "temperature",
    "batch",
    "scheduling",
    "process",
    "selected",
    "site",
    "raw",
    "material",
}
_PLACEHOLDER_TOKENS = {"a", "b", "p", "product", "reactant", "intermediate", "generic_route_1"}
_THERMO_INPUTS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "distillation": ("molecular_weight", "normal_boiling_point", "liquid_density", "liquid_heat_capacity", "heat_of_vaporization"),
    "evaporation": ("molecular_weight", "normal_boiling_point", "liquid_density", "liquid_heat_capacity", "heat_of_vaporization"),
    "flash": ("molecular_weight", "normal_boiling_point", "liquid_density", "heat_of_vaporization"),
    "absorption": ("molecular_weight", "liquid_density"),
    "extraction": ("molecular_weight", "liquid_density"),
    "crystallization": ("molecular_weight", "melting_point"),
    "drying": ("molecular_weight", "liquid_heat_capacity", "heat_of_vaporization"),
    "filtration": ("molecular_weight", "liquid_density"),
}
_HIGH_KINETICS_FAMILIES = {
    "oxidation",
    "hydrogenation",
    "carbonylation",
    "rearrangement",
    "acylation",
    "catalytic",
}
_ROUTE_REVISION_LIMITS = {
    "route_selection": 3,
    "thermodynamic_feasibility": 2,
    "kinetic_feasibility": 2,
}


def _float_value(prop) -> float | None:
    if prop is None:
        return None
    try:
        return float(prop.value)
    except Exception:
        match = re.search(r"-?\d+(?:\.\d+)?", str(getattr(prop, "value", prop)))
        if not match:
            return None
        try:
            return float(match.group(0))
        except Exception:
            return None


def _gate_worst(left: ScientificGateStatus, right: ScientificGateStatus) -> ScientificGateStatus:
    order = {
        ScientificGateStatus.PASS: 0,
        ScientificGateStatus.SCREENING_ONLY: 1,
        ScientificGateStatus.FAIL: 2,
    }
    return left if order[left] >= order[right] else right


def _confidence_rank(value: ScientificConfidence) -> int:
    order = {
        ScientificConfidence.DETAILED: 0,
        ScientificConfidence.METHOD_DERIVED: 1,
        ScientificConfidence.SCREENING: 2,
        ScientificConfidence.BLOCKED: 3,
    }
    return order[value]


def _route_lookup(route_chemistry: RouteChemistryArtifact):
    return {graph.route_id: graph for graph in route_chemistry.route_graphs}


def _node_lookup(graph) -> dict[str, object]:
    if graph is None or not getattr(graph, "species_nodes", None):
        return {}
    return {node.species_id: node for node in graph.species_nodes}


def _active_fraction_for_basis(basis: ProjectBasis) -> float:
    if basis.throughput_basis == "active_component":
        return 1.0
    return max(min((basis.nominal_active_wt_pct or 100.0) / 100.0, 1.0), 0.01)


def build_commercial_product_basis_artifact(
    basis: ProjectBasis,
    product_profile: ProductProfileArtifact,
    market_assessment: MarketAssessmentArtifact,
) -> CommercialProductBasisArtifact:
    active_fraction = _active_fraction_for_basis(basis)
    sold_solution_basis_kg_hr = (basis.capacity_tpa * 1000.0) / max(basis.annual_operating_days * 24.0, 1)
    active_basis_kg_hr = sold_solution_basis_kg_hr if basis.throughput_basis == "active_component" else sold_solution_basis_kg_hr * active_fraction
    sold_solution_price = market_assessment.estimated_price_per_kg
    active_price = sold_solution_price / max(active_fraction, 1e-6)
    packaging_mode = "bulk tanker and packed HDPE/IBC dispatch" if sold_solution_basis_kg_hr > 2000.0 else "packed dispatch"
    dispatch_mode = "finished-solution dispatch on sold concentration basis"
    capacity_basis_note = (
        f"{basis.capacity_tpa:,.0f} TPA is treated as sold solution throughput. "
        f"Reaction stoichiometry and active-material economics are normalized to {active_basis_kg_hr:,.2f} kg/h active basis."
    )
    markdown = "\n".join(
        [
            "| Basis Item | Value |",
            "| --- | --- |",
            f"| Throughput basis | {basis.throughput_basis.replace('_', ' ')} |",
            f"| Sold solution basis | {sold_solution_basis_kg_hr:,.2f} kg/h |",
            f"| Active basis | {active_basis_kg_hr:,.2f} kg/h |",
            f"| Sold concentration | {active_fraction * 100.0:.1f} wt% |",
            f"| Sold-solution price | INR {sold_solution_price:,.2f}/kg |",
            f"| Active-normalized price | INR {active_price:,.2f}/kg active |",
            f"| Packaging mode | {packaging_mode} |",
            f"| Dispatch mode | {dispatch_mode} |",
            f"| Product form | {product_profile.product_form or basis.product_form or 'solution'} |",
            f"| Carrier components | {', '.join(product_profile.carrier_components or basis.carrier_components) or '-'} |",
        ]
    )
    return CommercialProductBasisArtifact(
        product_name=product_profile.product_name,
        throughput_basis=basis.throughput_basis,
        sold_solution_basis_kg_hr=round(sold_solution_basis_kg_hr, 3),
        active_basis_kg_hr=round(active_basis_kg_hr, 3),
        active_fraction=round(active_fraction, 6),
        sold_concentration_wt_pct=round(active_fraction * 100.0, 3),
        sold_solution_price_inr_per_kg=round(sold_solution_price, 2),
        active_price_inr_per_kg=round(active_price, 2),
        packaging_mode=packaging_mode,
        dispatch_mode=dispatch_mode,
        product_form=product_profile.product_form or basis.product_form or "solution",
        carrier_components=list(product_profile.carrier_components or basis.carrier_components),
        homolog_distribution=dict(product_profile.homolog_distribution or basis.homolog_distribution),
        quality_targets=list(product_profile.quality_targets or basis.quality_targets),
        capacity_basis_note=capacity_basis_note,
        markdown=markdown,
        citations=sorted(set(market_assessment.citations)),
        assumptions=product_profile.assumptions + market_assessment.assumptions + [capacity_basis_note],
    )


def _classify_source_id_for_reality(
    source_id: str,
    source_index: dict[str, object],
    config: ProjectConfig,
) -> DataRealityClass:
    text = (source_id or "").strip().lower()
    if not text:
        return DataRealityClass.MODEL_INFERRED
    if text.startswith("user_doc") or text.startswith("user_") or text.startswith("market_sheet"):
        return DataRealityClass.USER_PROVIDED
    if text.startswith("seed_") or text.startswith("benchmark_") or text.startswith("seed_bip_"):
        return DataRealityClass.SEEDED_BENCHMARK
    record = source_index.get(source_id)
    if record is not None:
        source_kind = getattr(record, "source_kind", None)
        if getattr(source_kind, "value", source_kind) == "user_document":
            return DataRealityClass.USER_PROVIDED
        if config.model.backend == "google":
            return DataRealityClass.LIVE_FETCHED
    return DataRealityClass.LIVE_FETCHED if config.model.backend == "google" else DataRealityClass.SEEDED_BENCHMARK


def _reality_counts(items: list[DataRealityClass]) -> dict[str, int]:
    counts = {item.value: 0 for item in DataRealityClass}
    for item in items:
        counts[item.value] = counts.get(item.value, 0) + 1
    return {key: value for key, value in counts.items() if value > 0}


def _dominant_reality_class(items: list[DataRealityClass]) -> DataRealityClass:
    if not items:
        return DataRealityClass.MODEL_INFERRED
    counts = _reality_counts(items)
    dominant_key = max(counts.items(), key=lambda item: item[1])[0]
    return DataRealityClass(dominant_key)


def _fraction_for_reality(items: list[DataRealityClass], classes: set[DataRealityClass]) -> float:
    if not items:
        return 0.0
    count = sum(1 for item in items if item in classes)
    return round(count / len(items), 4)


def _material_seeded_dependency(row: DataRealityAuditRow) -> bool:
    if row.dominant_class == DataRealityClass.SEEDED_BENCHMARK:
        return True
    if row.artifact_ref == "product_profile":
        return row.seeded_fraction >= 0.5
    if row.artifact_ref == "commercial_product_basis":
        return row.seeded_fraction >= 0.5
    if row.artifact_ref == "property_packages":
        return row.seeded_fraction >= 0.5
    if row.artifact_ref == "site_selection":
        return row.seeded_fraction >= 0.5
    return row.seeded_fraction > 0.0


def build_data_reality_audit_artifact(
    config: ProjectConfig,
    resolved_sources,
    product_profile: ProductProfileArtifact | None,
    commercial_product_basis: CommercialProductBasisArtifact | None,
    process_selection_comparison,
    property_packages: PropertyPackageArtifact | None,
    site_selection,
    bac_purification_sections: BACPurificationSectionArtifact | None,
    bac_impurity_model: BACImpurityModelArtifact | None,
    economic_coverage: EconomicCoverageDecision | None,
    cost_model: CostModel | None,
) -> DataRealityAuditArtifact | None:
    benchmark_profile = (config.benchmark_profile or "").strip().lower()
    if benchmark_profile != "benzalkonium_chloride":
        return None
    source_index: dict[str, object] = {}
    if resolved_sources is not None:
        for group in resolved_sources.groups:
            for candidate in getattr(group, "candidates", []):
                source_index.setdefault(candidate.source_id, candidate)
    rows: list[DataRealityAuditRow] = []

    if product_profile is not None:
        classes: list[DataRealityClass] = []
        if benchmark_profile == "benzalkonium_chloride":
            active_pct = product_profile.nominal_active_wt_pct or config.basis.nominal_active_wt_pct
            if active_pct:
                classes.append(DataRealityClass.USER_PROVIDED)
            if product_profile.product_form or config.basis.product_form:
                classes.append(DataRealityClass.USER_PROVIDED)
            if product_profile.carrier_components or config.basis.carrier_components:
                classes.append(DataRealityClass.USER_PROVIDED)
            if product_profile.homolog_distribution or config.basis.homolog_distribution:
                classes.append(DataRealityClass.USER_PROVIDED)
            if product_profile.quality_targets or config.basis.quality_targets:
                classes.append(DataRealityClass.USER_PROVIDED)
        for prop in product_profile.properties:
            if prop.method == ProvenanceTag.USER_SUPPLIED:
                classes.append(DataRealityClass.USER_PROVIDED)
            elif prop.method == ProvenanceTag.SOURCED:
                source_ids = prop.supporting_sources or prop.citations or product_profile.citations
                if source_ids:
                    classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in source_ids)
                else:
                    classes.append(DataRealityClass.STRUCTURED_DATABASE)
            elif prop.method == ProvenanceTag.CALCULATED:
                classes.append(DataRealityClass.STRUCTURED_DATABASE)
            elif prop.method == ProvenanceTag.ESTIMATED:
                classes.append(DataRealityClass.MODEL_INFERRED)
            else:
                classes.append(DataRealityClass.MODEL_INFERRED)
        if not classes:
            classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="product_profile",
                artifact_label="Product Profile",
                domain="product",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=[
                    "Product properties are classified from property methods and supporting source ids.",
                    "BAC commercial form, active wt%, carrier basis, homolog basis, and quality targets are treated as user-provided benchmark inputs when explicitly fixed in the project basis.",
                ],
                citations=list(product_profile.citations),
                assumptions=list(product_profile.assumptions),
            )
        )

    if commercial_product_basis is not None:
        classes = [
            DataRealityClass.USER_PROVIDED,
            DataRealityClass.USER_PROVIDED,
            DataRealityClass.USER_PROVIDED,
            DataRealityClass.USER_PROVIDED,
            DataRealityClass.SOLVER_DERIVED,
            DataRealityClass.SOLVER_DERIVED,
            DataRealityClass.SOLVER_DERIVED,
        ]
        if commercial_product_basis.citations:
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in commercial_product_basis.citations)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="commercial_product_basis",
                artifact_label="Commercial Product Basis",
                domain="product_basis",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=[
                    "Throughput and commercial form are user-fixed; active normalization and price transforms are solver-derived.",
                    "Seeded or cited commercial price anchors only count as material dependency when they dominate the basis rather than merely supporting the sold-solution price line.",
                ],
                citations=list(commercial_product_basis.citations),
                assumptions=list(commercial_product_basis.assumptions),
            )
        )

    if process_selection_comparison is not None:
        classes = []
        for row in process_selection_comparison.rows:
            if row.route_origin == "document":
                classes.append(DataRealityClass.USER_PROVIDED)
            elif row.route_evidence_basis == "seeded_benchmark" or row.route_origin == "seeded":
                classes.append(DataRealityClass.SEEDED_BENCHMARK)
            elif row.route_evidence_basis in {"cited_technical", "cited_patent", "mixed_cited"} or row.route_origin == "hybrid":
                classes.append(DataRealityClass.LIVE_FETCHED if config.model.backend == "google" else DataRealityClass.STRUCTURED_DATABASE)
            else:
                classes.append(DataRealityClass.MODEL_INFERRED)
        if not classes:
            classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="process_selection_comparison",
                artifact_label="Process Selection",
                domain="route_selection",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=["Route comparison is classified from route evidence basis first, then route origin; seeded route families remain explicit fallback."],
                citations=list(process_selection_comparison.citations),
                assumptions=list(process_selection_comparison.assumptions),
            )
        )

    if property_packages is not None:
        classes = []
        for package in property_packages.packages:
            for field_name in (
                "molecular_weight",
                "normal_boiling_point",
                "melting_point",
                "liquid_density",
                "liquid_viscosity",
                "liquid_heat_capacity",
                "heat_of_vaporization",
                "thermal_conductivity",
            ):
                prop = getattr(package, field_name, None)
                if prop is None:
                    continue
                if prop.provenance_method == ProvenanceTag.USER_SUPPLIED:
                    classes.append(DataRealityClass.USER_PROVIDED)
                elif prop.provenance_method == ProvenanceTag.SOURCED:
                    if prop.source_ids:
                        classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in prop.source_ids)
                    else:
                        classes.append(DataRealityClass.STRUCTURED_DATABASE)
                elif prop.provenance_method == ProvenanceTag.CALCULATED:
                    classes.append(DataRealityClass.STRUCTURED_DATABASE if prop.source_ids else DataRealityClass.MODEL_INFERRED)
                elif prop.provenance_method == ProvenanceTag.ESTIMATED:
                    classes.append(DataRealityClass.MODEL_INFERRED)
                else:
                    classes.append(DataRealityClass.MODEL_INFERRED)
        for bip in property_packages.binary_interaction_parameters:
            if bip.source_ids:
                classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in bip.source_ids)
            else:
                classes.append(DataRealityClass.MODEL_INFERRED)
        if not classes:
            classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="property_packages",
                artifact_label="Property Basis",
                domain="properties",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=[
                    "Property-package coverage counts pure-component properties and BAC binary pairs together.",
                    "BAC property packages are only treated as materially seeded when seeded support dominates the package basis instead of remaining a minority within a mostly library-backed package set.",
                ],
                citations=list(property_packages.citations),
                assumptions=list(property_packages.assumptions),
            )
        )

    if site_selection is not None:
        classes = []
        selected_candidate = next(
            (candidate for candidate in site_selection.candidates if candidate.name == site_selection.selected_site),
            None,
        )
        selected_location = next(
            (
                datum
                for datum in site_selection.india_location_data
                if datum.site_name == site_selection.selected_site
            ),
            None,
        )
        if selected_candidate is not None and selected_candidate.citations:
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in selected_candidate.citations)
        if selected_location is not None and selected_location.citations:
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in selected_location.citations)
        for datum in site_selection.india_location_data:
            if datum is selected_location or not datum.citations:
                continue
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in datum.citations)
        if site_selection.selected_site and any(
            site_selection.selected_site.lower() == item.lower() for item in config.preferred_site_candidates
        ):
            classes.append(DataRealityClass.USER_PROVIDED)
        if selected_candidate is not None and any(
            selected_candidate.state.lower() == item.lower() for item in config.preferred_state_candidates
        ):
            classes.append(DataRealityClass.USER_PROVIDED)
        source_ids = list(site_selection.citations)
        if source_ids:
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in source_ids)
        else:
            if not classes:
                classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="site_selection",
                artifact_label="Site Selection",
                domain="site",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=[
                    "Site basis is classified from selected-site citations, selected-location citations, and supporting India-location evidence.",
                    "User-fixed preferred site or state is counted as user-provided siting basis when it matches the selected location.",
                ],
                citations=list(site_selection.citations),
                assumptions=list(site_selection.assumptions),
            )
        )

    if bac_purification_sections is not None:
        classes = []
        for section in bac_purification_sections.sections:
            classes.append(DataRealityClass.SOLVER_DERIVED if section.status == ScientificGateStatus.PASS else DataRealityClass.MODEL_INFERRED)
        if not classes:
            classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="bac_purification_sections",
                artifact_label="BAC Purification Basis",
                domain="purification",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=["Purification sections are method-derived from the solved thermo and blueprint basis."],
                citations=list(bac_purification_sections.citations),
                assumptions=list(bac_purification_sections.assumptions),
            )
        )

    if bac_impurity_model is not None:
        classes = []
        for item in bac_impurity_model.items:
            classes.append(DataRealityClass.MODEL_INFERRED if item.status == "blocked" else DataRealityClass.SOLVER_DERIVED)
        if not classes:
            classes.append(DataRealityClass.MODEL_INFERRED)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="bac_impurity_model",
                artifact_label="BAC Impurity Model",
                domain="impurities",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=["Impurity classes are classified from solved stream closure versus unresolved model-only classes."],
                citations=list(bac_impurity_model.citations),
                assumptions=list(bac_impurity_model.assumptions),
            )
        )

    if cost_model is not None:
        classes = [DataRealityClass.SOLVER_DERIVED] * 6
        if cost_model.citations:
            classes.extend(_classify_source_id_for_reality(source_id, source_index, config) for source_id in cost_model.citations)
        rows.append(
            DataRealityAuditRow(
                artifact_ref="cost_model",
                artifact_label="Economics Basis",
                domain="economics",
                critical=True,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=["Economics remain solver-derived even when tariff and price anchors are externally sourced."],
                citations=list(cost_model.citations),
                assumptions=list(cost_model.assumptions),
            )
        )

    if economic_coverage is not None:
        classes = [DataRealityClass.SOLVER_DERIVED if economic_coverage.status == "detailed" else DataRealityClass.MODEL_INFERRED]
        rows.append(
            DataRealityAuditRow(
                artifact_ref="economic_coverage",
                artifact_label="Economic Coverage",
                domain="economics",
                critical=False,
                dominant_class=_dominant_reality_class(classes),
                counts_by_class=_reality_counts(classes),
                real_data_fraction=_fraction_for_reality(classes, {DataRealityClass.USER_PROVIDED, DataRealityClass.LIVE_FETCHED, DataRealityClass.STRUCTURED_DATABASE}),
                seeded_fraction=_fraction_for_reality(classes, {DataRealityClass.SEEDED_BENCHMARK}),
                solver_fraction=_fraction_for_reality(classes, {DataRealityClass.SOLVER_DERIVED}),
                inferred_fraction=_fraction_for_reality(classes, {DataRealityClass.MODEL_INFERRED}),
                notes=["Coverage status reports whether the economic model is detailed or still estimate-heavy."],
                citations=list(economic_coverage.citations),
                assumptions=list(economic_coverage.assumptions),
            )
        )

    critical_rows = [row for row in rows if row.critical]
    overall_real_data_fraction = round(
        sum(row.real_data_fraction for row in critical_rows) / max(len(critical_rows), 1),
        4,
    )
    critical_seeded_artifact_refs = [
        row.artifact_ref for row in critical_rows if _material_seeded_dependency(row)
    ]
    critical_inferred_artifact_refs = [
        row.artifact_ref for row in critical_rows if row.inferred_fraction > 0.0 or row.dominant_class == DataRealityClass.MODEL_INFERRED
    ]
    summary = (
        f"BAC data reality audit: {overall_real_data_fraction:.1%} of critical basis items are real-data-backed; "
        f"critical seeded refs={', '.join(critical_seeded_artifact_refs) or 'none'}; "
        f"critical inferred refs={', '.join(critical_inferred_artifact_refs) or 'none'}."
    )
    markdown_lines = [
        "| Artifact | Domain | Critical | Dominant | Real % | Seeded % | Solver % | Inferred % |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        markdown_lines.append(
            f"| {row.artifact_ref} | {row.domain} | {'yes' if row.critical else 'no'} | {row.dominant_class.value} | "
            f"{row.real_data_fraction:.0%} | {row.seeded_fraction:.0%} | {row.solver_fraction:.0%} | {row.inferred_fraction:.0%} |"
        )
    return DataRealityAuditArtifact(
        benchmark_profile=benchmark_profile,
        project_id=config.project_id or "",
        rows=rows,
        overall_real_data_fraction=overall_real_data_fraction,
        critical_seeded_artifact_refs=critical_seeded_artifact_refs,
        critical_inferred_artifact_refs=critical_inferred_artifact_refs,
        summary=summary,
        markdown="\n".join(markdown_lines),
        citations=sorted({citation for row in rows for citation in row.citations}),
        assumptions=[summary],
    )


def build_bac_estimation_policy_artifact() -> EstimationPolicy:
    rules = [
        DatumRequirementRule(datum_id="bac_active_pure_properties", engineering_category="pure_properties", allowed_methods=[EstimationMethodTag.DIRECT, EstimationMethodTag.PSEUDO_COMPONENT, EstimationMethodTag.LIBRARY_VALUE, EstimationMethodTag.CORRELATION], forbidden_methods=[EstimationMethodTag.FALLBACK], minimum_confidence=0.45, critical=True),
        DatumRequirementRule(datum_id="bac_binary_pairs", engineering_category="thermo_pairs", allowed_methods=[EstimationMethodTag.RESOLVED_PAIR, EstimationMethodTag.REGRESSED_PAIR, EstimationMethodTag.FAMILY_ESTIMATED_PAIR, EstimationMethodTag.FALLBACK], forbidden_methods=[], minimum_confidence=0.40, critical=True),
        DatumRequirementRule(datum_id="bac_kinetics", engineering_category="kinetics", allowed_methods=[EstimationMethodTag.CITED_KINETIC_FIT, EstimationMethodTag.FAMILY_ARRHENIUS_FIT, EstimationMethodTag.RESIDENCE_TIME_HEURISTIC], forbidden_methods=[EstimationMethodTag.FALLBACK], minimum_confidence=0.35, critical=True),
        DatumRequirementRule(datum_id="bac_impurities", engineering_category="impurities", allowed_methods=[EstimationMethodTag.MEASURED_STREAM_BASIS, EstimationMethodTag.TEMPLATE_DERIVED, EstimationMethodTag.PLACEHOLDER_ESTIMATE], forbidden_methods=[], minimum_confidence=0.30, critical=True),
        DatumRequirementRule(datum_id="bac_recycle_purge", engineering_category="recycle", allowed_methods=[EstimationMethodTag.SOLVED_BALANCE, EstimationMethodTag.FAMILY_PURGE_HEURISTIC], forbidden_methods=[], minimum_confidence=0.40, critical=True),
        DatumRequirementRule(datum_id="bac_economics_inputs", engineering_category="economics", allowed_methods=[EstimationMethodTag.LIVE_QUOTE, EstimationMethodTag.SITE_TARIFF, EstimationMethodTag.MODEL_DERIVED, EstimationMethodTag.LIBRARY_VALUE], forbidden_methods=[], minimum_confidence=0.35, critical=True),
    ]
    markdown = "\n".join([
        "| Datum Class | Allowed Methods | Minimum Confidence |",
        "| --- | --- | --- |",
        *[
            f"| {rule.engineering_category} | {', '.join(item.value for item in rule.allowed_methods)} | {rule.minimum_confidence:.2f} |"
            for rule in rules
        ],
    ])
    return EstimationPolicy(
        policy_id="bac_estimation_policy_v1",
        benchmark_profile="benzalkonium_chloride",
        rules=rules,
        markdown=markdown,
        assumptions=["BAC missing-data policy allows explicit preliminary-design estimation paths, but every estimate must carry a named method and basis."],
    )


def build_bac_pseudo_component_basis_artifact(
    basis: ProjectBasis,
    product_profile: ProductProfileArtifact | None,
    property_packages: PropertyPackageArtifact | None,
) -> BACPseudoComponentBasisArtifact | None:
    if (basis.target_product or "").strip().lower() != "benzalkonium chloride":
        return None
    package_index = _package_index(property_packages) if property_packages is not None else {}
    active = package_index.get("benzalkonium_chloride")
    solution_density = 995.0
    solution_viscosity = 0.0025
    solution_cp = 3.0
    if product_profile is not None:
        for prop in product_profile.properties:
            lowered = prop.name.lower()
            try:
                value = float(prop.value)
            except Exception:
                continue
            if lowered == "density":
                solution_density = value * 1000.0 if prop.units.lower() in {"g/cm3", "g/cc", "g/ml"} else value
            elif "viscosity" in lowered:
                solution_viscosity = value
    active_mw = _float_value(active.molecular_weight) if active and active.molecular_weight else 368.04
    active_density = _float_value(active.liquid_density) if active and active.liquid_density else 995.0
    active_viscosity = _float_value(active.liquid_viscosity) if active and active.liquid_viscosity else 0.0025
    active_cp = _float_value(active.liquid_heat_capacity) if active and active.liquid_heat_capacity else 3.0
    active_k = _float_value(active.thermal_conductivity) if active and active.thermal_conductivity else 0.20
    markdown = "\n".join([
        "| Basis Slice | Value |",
        "| --- | --- |",
        f"| Active representative MW | {active_mw:.2f} g/mol |",
        f"| Active density | {active_density:.2f} kg/m3 |",
        f"| Active viscosity | {active_viscosity:.5f} Pa.s |",
        f"| Active Cp | {active_cp:.3f} kJ/kg-K |",
        f"| Active thermal conductivity | {active_k:.3f} W/m-K |",
        f"| Sold-solution density | {solution_density:.2f} kg/m3 |",
        f"| Sold-solution viscosity | {solution_viscosity:.5f} Pa.s |",
        f"| Sold-solution Cp | {solution_cp:.3f} kJ/kg-K |",
        "| Nonvolatile treatment | BAC active is treated as effectively nonvolatile in the present process basis. |",
    ])
    homolog_distribution = dict(getattr(product_profile, "homolog_distribution", {}) or basis.homolog_distribution)
    carrier_components = list(getattr(product_profile, "carrier_components", []) or basis.carrier_components)
    return BACPseudoComponentBasisArtifact(
        artifact_id="bac_pseudo_component_basis",
        active_representative_mw_g_mol=round(active_mw, 4),
        active_density_kg_m3=round(active_density, 4),
        active_viscosity_pa_s=round(active_viscosity, 8),
        active_cp_kj_kg_k=round(active_cp, 6),
        active_thermal_conductivity_w_m_k=round(active_k, 6),
        active_nonvolatile=True,
        sold_solution_density_kg_m3=round(solution_density, 4),
        sold_solution_viscosity_pa_s=round(solution_viscosity, 8),
        sold_solution_cp_kj_kg_k=round(solution_cp, 6),
        homolog_distribution=homolog_distribution,
        carrier_components=carrier_components,
        markdown=markdown,
        citations=sorted(set((property_packages.citations if property_packages is not None else []) + (product_profile.citations if product_profile is not None else []))),
        assumptions=["BAC physical basis is represented as a sold-solution pseudo-component system instead of a neat pure-compound basis."],
    )


def build_bac_binary_pair_coverage_artifact(
    route_selection: RouteSelectionArtifact | None,
    property_packages: PropertyPackageArtifact | None,
    separation_thermo: SeparationThermoArtifact | None,
) -> BinaryPairCoverageArtifact | None:
    if route_selection is None or property_packages is None:
        return None
    if "benzyl" not in route_selection.selected_route_id and "quaternization" not in route_selection.selected_route_id:
        return None
    critical_pairs = [
        ("alkyldimethylamine", "benzyl_chloride"),
        ("alkyldimethylamine", "ethanol"),
        ("alkyldimethylamine", "water"),
        ("alkyldimethylamine", "benzyl_alcohol"),
        ("alkyldimethylamine", "benzalkonium_chloride"),
        ("benzalkonium_chloride", "ethanol"),
        ("benzalkonium_chloride", "water"),
        ("benzalkonium_chloride", "benzyl_chloride"),
        ("benzalkonium_chloride", "benzyl_alcohol"),
    ]
    bip_index = {item.bip_id: item for item in property_packages.binary_interaction_parameters}
    missing_pairs = set(separation_thermo.missing_binary_pairs if separation_thermo is not None else [])
    rows: list[BinaryPairCoverageRow] = []
    critical_fallback_pairs: list[str] = []
    for component_a, component_b in critical_pairs:
        pair_id = "__".join(sorted([component_a, component_b]))
        bip = bip_index.get(pair_id)
        if bip is not None and bip.resolution_status == "resolved":
            status = "resolved_from_data"
        elif bip is not None and bip.provenance_method == ProvenanceTag.ESTIMATED:
            status = "family_estimated"
        elif pair_id in missing_pairs:
            status = "fallback"
        else:
            status = "fallback"
        if status == "fallback":
            critical_fallback_pairs.append(pair_id)
        rows.append(
            BinaryPairCoverageRow(
                pair_id=pair_id,
                component_a=component_a,
                component_b=component_b,
                status=status,
                model_name=bip.model_name if bip is not None else (separation_thermo.activity_model if separation_thermo is not None else "NRTL"),
                source_refs=list(bip.source_ids if bip is not None else []),
                notes=list(bip.notes if bip is not None else []),
            )
        )
    markdown = "\n".join([
        "| Pair | Status | Model | Source Refs |",
        "| --- | --- | --- | --- |",
        *[
            f"| {row.pair_id} | {row.status} | {row.model_name} | {', '.join(row.source_refs) or '-'} |"
            for row in rows
        ],
    ])
    return BinaryPairCoverageArtifact(
        artifact_id="bac_binary_pair_coverage",
        route_id=route_selection.selected_route_id,
        rows=rows,
        critical_fallback_pairs=sorted(set(critical_fallback_pairs)),
        markdown=markdown,
        citations=sorted({citation for row in rows for citation in row.source_refs}),
        assumptions=["BAC binary-pair coverage tracks whether each critical cleanup pair is resolved, family-estimated, or still on fallback treatment."],
    )


def build_bac_section_thermo_assignment_artifact(
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None,
    bac_purification_sections: BACPurificationSectionArtifact | None,
    separation_thermo: SeparationThermoArtifact | None,
) -> SectionThermoAssignmentArtifact | None:
    if flowsheet_blueprint is None or bac_purification_sections is None:
        return None
    rows = [
        SectionThermoAssignmentRow(
            section_id=item.section_id,
            section_label=item.label,
            thermo_method=item.thermo_method or (separation_thermo.relative_volatility.method if separation_thermo and separation_thermo.relative_volatility else ""),
            activity_model=item.activity_model or (separation_thermo.activity_model if separation_thermo is not None else ""),
            key_pairs=[" / ".join([separation_thermo.light_key, separation_thermo.heavy_key])] if separation_thermo is not None and item.step_id == "purification" else [" / ".join(item.key_species[:2])] if len(item.key_species) >= 2 else list(item.key_species),
            confidence=item.confidence,
            notes=list(item.notes),
        )
        for item in bac_purification_sections.sections
    ]
    markdown = "\n".join([
        "| Section | Thermo Method | Activity Model | Key Pair(s) | Confidence |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {row.section_label or row.section_id} | {row.thermo_method or '-'} | {row.activity_model or '-'} | {', '.join(row.key_pairs) or '-'} | {row.confidence.value} |"
            for row in rows
        ],
    ])
    return SectionThermoAssignmentArtifact(
        artifact_id="bac_section_thermo_assignment",
        route_id=flowsheet_blueprint.route_id,
        rows=rows,
        markdown=markdown,
        citations=sorted({citation for item in bac_purification_sections.sections for citation in item.citations}),
        assumptions=["Section thermo assignments expose which BAC cleanup section uses which thermo method and activity basis."],
    )


def build_bac_kinetic_basis_artifact(
    route_selection: RouteSelectionArtifact | None,
    kinetics: KineticAssessmentArtifact | None,
) -> KineticBasisArtifact | None:
    if route_selection is None or kinetics is None:
        return None
    if "benzyl" not in route_selection.selected_route_id and "quaternization" not in route_selection.selected_route_id:
        return None
    basis = "Family Arrhenius fit transferred onto BAC liquid quaternization preliminary-design basis."
    return KineticBasisArtifact(
        artifact_id="bac_kinetic_basis",
        route_id=route_selection.selected_route_id,
        reaction_family="liquid_quaternization",
        assumed_mechanism_class="second_order_sn2_hypothesis",
        activation_energy_kj_per_mol=kinetics.activation_energy_kj_per_mol,
        pre_exponential_factor=kinetics.pre_exponential_factor,
        apparent_order=kinetics.apparent_order,
        design_residence_time_hr=kinetics.design_residence_time_hr,
        method_tag=EstimationMethodTag.FAMILY_ARRHENIUS_FIT,
        cap_logic_summary="Liquid BAC quaternization reactor sizing remains capped to a practical continuous agitated-reactor residence-time envelope when extrapolated kinetics become unrealistic.",
        markdown="\n".join([
            "| Kinetic Basis Item | Value |",
            "| --- | --- |",
            "| Reaction family | liquid quaternization |",
            "| Mechanism class | second_order_sn2_hypothesis |",
            f"| Activation energy | {kinetics.activation_energy_kj_per_mol:.3f} kJ/mol |",
            f"| Pre-exponential factor | {kinetics.pre_exponential_factor:.3e} |",
            f"| Apparent order | {kinetics.apparent_order:.3f} |",
            f"| Design residence time | {kinetics.design_residence_time_hr:.3f} h |",
        ]),
        citations=list(kinetics.citations),
        assumptions=list(kinetics.assumptions) + [basis],
    )


def build_reactor_basis_confidence_artifact(
    kinetic_basis: KineticBasisArtifact | None,
    reactor_design: ReactorDesign | None,
) -> ReactorBasisConfidenceArtifact | None:
    if kinetic_basis is None or reactor_design is None:
        return None
    confidence = ScientificConfidence.METHOD_DERIVED
    basis_summary = "Reactor sizing is grounded in method-derived kinetics and a practical residence-time cap for liquid BAC quaternization service."
    return ReactorBasisConfidenceArtifact(
        artifact_id="bac_reactor_basis_confidence",
        route_id=kinetic_basis.route_id,
        confidence=confidence,
        basis_summary=basis_summary,
        hidden_cap_logic=False,
        markdown=f"### Reactor Basis Confidence\n\n- Confidence: `{confidence.value}`\n- Basis: {basis_summary}\n",
        citations=list(kinetic_basis.citations),
        assumptions=list(kinetic_basis.assumptions) + [reactor_design.design_basis],
    )


def build_bac_impurity_ledger_artifact(
    impurity_model: BACImpurityModelArtifact | None,
) -> BACImpurityLedgerArtifact | None:
    if impurity_model is None:
        return None
    status_map = {
        "blocked": "unresolved",
        "method_derived": "template_derived",
        "estimated": "placeholder_estimate",
    }
    items = [
        BACImpurityLedgerItem(
            impurity_id=item.impurity_id,
            impurity_class=item.impurity_class,
            origin=item.origin_section,
            expected_location=item.fate,
            control_section=item.control_section,
            purge_mechanism=item.fate,
            mass_estimate_kg_hr=item.estimated_mass_flow_kg_hr,
            status=status_map.get(item.status, "template_derived"),
            notes=[f"Severity: {item.severity}"],
        )
        for item in impurity_model.items
    ]
    markdown = "\n".join([
        "| Impurity | Class | Origin | Control | Purge / Fate | kg/h | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {item.impurity_id} | {item.impurity_class} | {item.origin} | {item.control_section} | {item.purge_mechanism} | {item.mass_estimate_kg_hr:.6f} | {item.status} |"
            for item in items
        ],
    ])
    return BACImpurityLedgerArtifact(
        artifact_id="bac_impurity_ledger",
        route_id=impurity_model.route_id,
        items=items,
        markdown=markdown,
        citations=list(impurity_model.citations),
        assumptions=list(impurity_model.assumptions),
    )


def build_recycle_basis_artifact(stream_table: StreamTable | None) -> RecycleBasisArtifact | None:
    if stream_table is None or not stream_table.convergence_summaries:
        return None
    loops: list[RecycleBasisLoop] = []
    for summary in stream_table.convergence_summaries:
        purge_basis_by_family = {
            family: ("solved_balance+family_minimum" if value > 0.0 else "solved_balance")
            for family, value in summary.purge_policy_by_family.items()
        }
        loops.append(
            RecycleBasisLoop(
                loop_id=summary.loop_id,
                source_section_id=summary.source_section_id,
                target_section_id=summary.target_section_id,
                actual_recycle_stream_ids=list(summary.recycle_stream_ids),
                actual_purge_stream_ids=list(summary.purge_stream_ids),
                purge_policy_by_family=dict(summary.purge_policy_by_family),
                purge_basis_by_family=purge_basis_by_family,
                closure_confidence=summary.convergence_status,
                notes=list(summary.notes),
                citations=list(summary.citations),
                assumptions=list(summary.assumptions),
            )
        )
    markdown = "\n".join([
        "| Loop | Source Section | Target Section | Purge Families | Confidence |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {item.loop_id} | {item.source_section_id or '-'} | {item.target_section_id or '-'} | {', '.join(f'{k}={v:.3f}' for k, v in item.purge_policy_by_family.items()) or '-'} | {item.closure_confidence} |"
            for item in loops
        ],
    ])
    return RecycleBasisArtifact(
        artifact_id="bac_recycle_basis",
        loops=loops,
        markdown=markdown,
        citations=sorted({citation for item in loops for citation in item.citations}),
        assumptions=sorted({assumption for item in loops for assumption in item.assumptions}),
    )


def build_economic_input_reality_artifact(
    cost_model: CostModel | None,
    route_economic_basis,
    market_assessment: MarketAssessmentArtifact | None,
) -> EconomicInputRealityArtifact | None:
    if cost_model is None:
        return None
    rows = [
        EconomicGapItem(item_id="product_price_basis", label="Product selling price basis", source_type="real_external_quote" if market_assessment and market_assessment.citations else "benchmark_anchor", normalization_basis="INR/kg sold solution", site_dependence="market-linked", estimate_method="market_assessment_anchor", gap_flag="" if market_assessment and market_assessment.citations else "selling_price_modeled"),
        EconomicGapItem(item_id="raw_material_burden", label="Raw-material cost burden", source_type="solver_derived_burden", normalization_basis="annualized stream burden", site_dependence="selected site", estimate_method="route_stream_burden_model", gap_flag="feedstock_quote_missing"),
        EconomicGapItem(item_id="utility_tariff_basis", label="Utility tariff basis", source_type="real_external_quote" if cost_model.india_price_data else "solver_derived_burden", normalization_basis="INR/kWh and steam equivalents", site_dependence="site-specific", estimate_method="site_tariff_or_cost_model", gap_flag="" if cost_model.india_price_data else "utility_tariff_missing"),
        EconomicGapItem(item_id="waste_treatment_burden", label="Waste-treatment burden", source_type="route_complexity_estimate", normalization_basis="annualized burden", site_dependence="site-specific", estimate_method="route_complexity_and_waste_stream_model", gap_flag="waste_treatment_cost_modeled"),
        EconomicGapItem(item_id="logistics_and_packaging", label="Logistics and packaging burden", source_type="route_complexity_estimate", normalization_basis="dispatch mode and throughput", site_dependence="site-specific", estimate_method="procurement_and_dispatch_model", gap_flag="packaging_logistics_missing"),
    ]
    markdown = "\n".join([
        "| Economic Input | Source Type | Method | Gap Flag |",
        "| --- | --- | --- | --- |",
        *[
            f"| {item.label} | {item.source_type} | {item.estimate_method} | {item.gap_flag or '-'} |"
            for item in rows
        ],
    ])
    return EconomicInputRealityArtifact(
        artifact_id="bac_economic_input_reality",
        rows=rows,
        markdown=markdown,
        citations=sorted(set(cost_model.citations + (market_assessment.citations if market_assessment is not None else []))),
        assumptions=list(cost_model.assumptions),
    )


def build_bac_data_gap_registry_artifact(
    config: ProjectConfig,
    pseudo_component_basis: BACPseudoComponentBasisArtifact | None,
    pair_coverage: BinaryPairCoverageArtifact | None,
    kinetic_basis: KineticBasisArtifact | None,
    impurity_ledger: BACImpurityLedgerArtifact | None,
    recycle_basis: RecycleBasisArtifact | None,
    economic_input_reality: EconomicInputRealityArtifact | None,
) -> DataGapRegistryArtifact | None:
    if (config.benchmark_profile or "").strip().lower() != "benzalkonium_chloride":
        return None
    items: list[DataGapItem] = []
    if pseudo_component_basis is not None:
        items.extend([
            DataGapItem(datum_id="bac_active_mw", engineering_category="pure_properties", current_value=f"{pseudo_component_basis.active_representative_mw_g_mol:.2f}", units="g/mol", provenance_class=DataRealityClass.STRUCTURED_DATABASE, method_name="BAC pseudo-component representative MW", method_tag=EstimationMethodTag.PSEUDO_COMPONENT, method_basis="Commercial homolog bundle mapped to one representative active MW.", confidence=0.65, downstream_consumers=["property_packages", "thermodynamic_feasibility", "material_balance"], upgrade_priority="high", direct_data=False, source_refs=list(pseudo_component_basis.citations), status="estimated"),
            DataGapItem(datum_id="bac_active_nonvolatile", engineering_category="pure_properties", current_value="true", units="-", provenance_class=DataRealityClass.MODEL_INFERRED, method_name="Nonvolatile ionic-active assumption", method_tag=EstimationMethodTag.FALLBACK, method_basis="BAC active retained in solution phase and excluded from volatility-led purification assumptions.", confidence=0.60, downstream_consumers=["separation_thermo", "distillation_design"], upgrade_priority="critical", direct_data=False, source_refs=list(pseudo_component_basis.citations), fallback_reason="Neat BAC volatility basis is not available for the commercial sold-solution design basis.", status="inferred"),
            DataGapItem(datum_id="bac_sold_solution_properties", engineering_category="pure_properties", current_value=f"rho={pseudo_component_basis.sold_solution_density_kg_m3:.2f}, mu={pseudo_component_basis.sold_solution_viscosity_pa_s:.5f}, cp={pseudo_component_basis.sold_solution_cp_kj_kg_k:.3f}", units="mixed", provenance_class=DataRealityClass.MODEL_INFERRED, method_name="Representative sold-solution pseudo-mixture", method_tag=EstimationMethodTag.PSEUDO_COMPONENT, method_basis="Commercial 50 wt% sold-solution handling basis.", confidence=0.55, downstream_consumers=["mixture_properties", "reactor_design", "storage_design"], upgrade_priority="high", direct_data=False, source_refs=list(pseudo_component_basis.citations), status="estimated"),
        ])
    if pair_coverage is not None:
        for row in pair_coverage.rows:
            method_tag = {
                "resolved_from_data": EstimationMethodTag.RESOLVED_PAIR,
                "regressed_from_data": EstimationMethodTag.REGRESSED_PAIR,
                "family_estimated": EstimationMethodTag.FAMILY_ESTIMATED_PAIR,
                "fallback": EstimationMethodTag.FALLBACK,
            }[row.status]
            items.append(DataGapItem(datum_id=f"pair_{row.pair_id}", engineering_category="thermo_pairs", current_value=row.model_name, units="-", provenance_class=DataRealityClass.STRUCTURED_DATABASE if row.status == "resolved_from_data" else DataRealityClass.MODEL_INFERRED, method_name=f"{row.model_name} pair basis", method_tag=method_tag, method_basis="BAC cleanup pair coverage matrix.", confidence=0.75 if row.status == "resolved_from_data" else 0.45 if row.status == "family_estimated" else 0.20, downstream_consumers=["separation_thermo", "distillation_design", "energy_balance"], upgrade_priority="critical" if row.status == "fallback" else "high", direct_data=row.status == "resolved_from_data", source_refs=list(row.source_refs), fallback_reason="Critical BAC pair remains unresolved in the present thermo set." if row.status == "fallback" else "", status="estimated" if row.status != "resolved_from_data" else "direct"))
    if kinetic_basis is not None:
        items.append(DataGapItem(datum_id="bac_kinetics_basis", engineering_category="kinetics", current_value=f"Ea={kinetic_basis.activation_energy_kj_per_mol:.3f}, A={kinetic_basis.pre_exponential_factor:.3e}", units="mixed", provenance_class=DataRealityClass.MODEL_INFERRED, method_name="Family Arrhenius fit", method_tag=kinetic_basis.method_tag, method_basis=kinetic_basis.cap_logic_summary, confidence=0.45, downstream_consumers=["reaction_kinetics", "reactor_design"], upgrade_priority="critical", direct_data=False, source_refs=list(kinetic_basis.citations), status="inferred"))
    if impurity_ledger is not None:
        for row in impurity_ledger.items:
            items.append(DataGapItem(datum_id=f"impurity_{row.impurity_id}", engineering_category="impurities", current_value=f"{row.mass_estimate_kg_hr:.6f}", units="kg/h", provenance_class=DataRealityClass.SOLVER_DERIVED if row.status == "measured_or_observed" else DataRealityClass.MODEL_INFERRED, method_name=row.status.replace("_", " "), method_tag=EstimationMethodTag.MEASURED_STREAM_BASIS if row.status == "measured_or_observed" else EstimationMethodTag.TEMPLATE_DERIVED if row.status == "template_derived" else EstimationMethodTag.PLACEHOLDER_ESTIMATE, method_basis=f"Origin={row.origin}; control={row.control_section}.", confidence=0.65 if row.status == "measured_or_observed" else 0.35, downstream_consumers=["material_balance", "safety_health_environment_waste", "cost_of_production"], upgrade_priority="high", direct_data=False, source_refs=list(impurity_ledger.citations), status="unresolved" if row.status == "unresolved" else "estimated"))
    if recycle_basis is not None:
        for row in recycle_basis.loops:
            items.append(DataGapItem(datum_id=f"recycle_{row.loop_id}", engineering_category="recycle", current_value=row.closure_confidence, units="-", provenance_class=DataRealityClass.SOLVER_DERIVED, method_name="Multi-loop solved recycle basis", method_tag=EstimationMethodTag.SOLVED_BALANCE, method_basis=", ".join(f"{k}={v:.3f}" for k, v in row.purge_policy_by_family.items()) or "No explicit purge family.", confidence=0.80 if row.closure_confidence == "converged" else 0.45, downstream_consumers=["material_balance", "cost_model"], upgrade_priority="high", direct_data=False, source_refs=list(recycle_basis.citations), status="solver_derived" if row.closure_confidence == "converged" else "estimated"))
    if economic_input_reality is not None:
        for row in economic_input_reality.rows:
            items.append(DataGapItem(datum_id=row.item_id, engineering_category="economics", current_value=row.source_type, units="-", provenance_class=DataRealityClass.LIVE_FETCHED if row.source_type == "real_external_quote" else DataRealityClass.SOLVER_DERIVED if row.source_type == "solver_derived_burden" else DataRealityClass.SEEDED_BENCHMARK if row.source_type == "benchmark_anchor" else DataRealityClass.MODEL_INFERRED, method_name=row.estimate_method, method_tag=EstimationMethodTag.LIVE_QUOTE if row.source_type == "real_external_quote" else EstimationMethodTag.MODEL_DERIVED, method_basis=row.normalization_basis, confidence=0.80 if row.source_type == "real_external_quote" else 0.40, downstream_consumers=["project_cost", "cost_of_production", "financial_analysis"], upgrade_priority="high", direct_data=row.source_type == "real_external_quote", source_refs=list(economic_input_reality.citations), fallback_reason=row.gap_flag, status="direct" if row.source_type == "real_external_quote" else "estimated"))
    items = list(items)
    unresolved = sum(1 for item in items if item.status == "unresolved")
    summary = f"BAC data-gap registry captures {len(items)} critical items; {unresolved} remain unresolved."
    markdown = "\n".join([
        "| Datum | Category | Status | Method | Provenance | Confidence | Priority |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {item.datum_id} | {item.engineering_category} | {item.status} | {item.method_tag.value} | {item.provenance_class.value} | {item.confidence:.2f} | {item.upgrade_priority} |"
            for item in items
        ],
    ])
    return DataGapRegistryArtifact(
        benchmark_profile="benzalkonium_chloride",
        project_id=config.project_id or "",
        items=items,
        summary=summary,
        markdown=markdown,
        citations=sorted({citation for item in items for citation in item.source_refs}),
        assumptions=[summary],
    )


def build_missing_data_acceptance_artifact(
    registry: DataGapRegistryArtifact | None,
    pair_coverage: BinaryPairCoverageArtifact | None,
    impurity_ledger: BACImpurityLedgerArtifact | None,
    economic_input_reality: EconomicInputRealityArtifact | None,
) -> MissingDataAcceptanceArtifact | None:
    if registry is None:
        return None
    issues: list[MissingDataValidationIssue] = []
    hidden_placeholder_count = 0
    critical_unresolved_count = 0
    named_estimates = 0
    estimated_count = 0
    for item in registry.items:
        if item.status in {"estimated", "inferred", "solver_derived"}:
            estimated_count += 1
            if item.method_name.strip():
                named_estimates += 1
        if item.method_tag == EstimationMethodTag.FALLBACK and not item.fallback_reason:
            hidden_placeholder_count += 1
            issues.append(MissingDataValidationIssue(datum_id=item.datum_id, code="missing_fallback_reason", severity="blocked", message=f"Estimated datum '{item.datum_id}' has fallback treatment without an explicit reason."))
        if item.status == "unresolved":
            critical_unresolved_count += 1
            issues.append(MissingDataValidationIssue(datum_id=item.datum_id, code="critical_unresolved_datum", severity="blocked", message=f"Critical BAC datum '{item.datum_id}' remains unresolved."))
        if item.status != "direct" and not item.method_name.strip():
            issues.append(MissingDataValidationIssue(datum_id=item.datum_id, code="missing_method_name", severity="blocked", message=f"Estimated datum '{item.datum_id}' has no named method."))
    if pair_coverage is not None:
        for pair_id in pair_coverage.critical_fallback_pairs:
            issues.append(MissingDataValidationIssue(datum_id=pair_id, code="critical_thermo_pair_fallback", severity="warning", message=f"Critical BAC thermo pair '{pair_id}' remains on fallback treatment."))
    if impurity_ledger is not None and any(item.status == "unresolved" for item in impurity_ledger.items):
        issues.append(MissingDataValidationIssue(datum_id="bac_impurity_ledger", code="unresolved_impurity_noted", severity="warning", message="BAC impurity ledger still contains unresolved impurity classes."))
    if economic_input_reality is not None:
        for row in economic_input_reality.rows:
            if row.source_type != "real_external_quote" and not row.estimate_method:
                issues.append(MissingDataValidationIssue(datum_id=row.item_id, code="economic_input_without_method", severity="blocked", message=f"Economic driver '{row.item_id}' is not quote-backed and has no estimate method."))
    coverage_fraction = round(sum(1 for item in registry.items if item.status != "unresolved") / max(len(registry.items), 1), 4)
    named_estimate_fraction = round(named_estimates / max(estimated_count, 1), 4) if estimated_count else 1.0
    overall_status = ReportAcceptanceStatus.COMPLETE if not any(issue.severity == "blocked" for issue in issues) else ReportAcceptanceStatus.CONDITIONAL
    if critical_unresolved_count > 0 or hidden_placeholder_count > 0:
        overall_status = ReportAcceptanceStatus.BLOCKED
    summary = f"Missing-data acceptance: coverage={coverage_fraction:.1%}; named estimates={named_estimate_fraction:.1%}; hidden placeholders={hidden_placeholder_count}; unresolved critical items={critical_unresolved_count}."
    markdown = "\n".join([
        f"- Overall status: `{overall_status.value}`",
        f"- Coverage fraction: `{coverage_fraction:.1%}`",
        f"- Named estimate fraction: `{named_estimate_fraction:.1%}`",
        f"- Hidden placeholder count: `{hidden_placeholder_count}`",
        f"- Critical unresolved count: `{critical_unresolved_count}`",
    ])
    return MissingDataAcceptanceArtifact(
        artifact_id="bac_missing_data_acceptance",
        overall_status=overall_status,
        coverage_fraction=coverage_fraction,
        named_estimate_fraction=named_estimate_fraction,
        hidden_placeholder_count=hidden_placeholder_count,
        critical_unresolved_count=critical_unresolved_count,
        issues=issues,
        summary=summary,
        markdown=markdown,
        citations=sorted({citation for item in registry.items for citation in item.source_refs}),
        assumptions=[summary],
    )


def build_bac_impurity_model_artifact(
    route_selection: RouteSelectionArtifact,
    stream_table: StreamTable | None,
    commercial_basis: CommercialProductBasisArtifact | None,
) -> BACImpurityModelArtifact | None:
    if route_selection.selected_route_id == "":
        return None
    if "benzyl" not in route_selection.selected_route_id and "quaternization" not in route_selection.selected_route_id:
        return None
    product_stream = next((stream for stream in stream_table.streams if stream.stream_role == "product"), None) if stream_table is not None else None
    waste_stream = next((stream for stream in stream_table.streams if stream.stream_role == "waste"), None) if stream_table is not None else None
    product_mass = sum(component.mass_flow_kg_hr for component in product_stream.components) if product_stream is not None else 0.0
    impurity_templates = [
        ("residual_free_amine", "Residual free amine", "amine_residual", "reaction", "purification", "recycle or waste purge", ("amine",)),
        ("residual_benzyl_chloride", "Residual benzyl chloride", "chloride_residual", "reaction", "concentration", "volatile cleanup and purge", ("benzyl chloride",)),
        ("benzyl_alcohol", "Benzyl alcohol / hydrolyzed benzyl species", "oxygenated_light_end", "reaction", "purification", "recycle or waste purge", ("benzyl alcohol",)),
        ("color_bodies", "Color bodies", "heavy_color_body", "reaction", "purification", "side draw or waste bleed", ("color", "heavy")),
        ("aqueous_chloride_losses", "Aqueous chloride losses", "aqueous_salt_loss", "waste_management", "waste_treatment", "aqueous effluent", ("chloride", "salt", "brine")),
    ]
    items: list[BACImpurityItem] = []
    unresolved_ids: list[str] = []
    all_components = []
    if product_stream is not None:
        all_components.extend(product_stream.components)
    if waste_stream is not None:
        all_components.extend(waste_stream.components)
    for impurity_id, name, impurity_class, origin_section, control_section, fate, tokens in impurity_templates:
        matched_mass = sum(
            component.mass_flow_kg_hr
            for component in all_components
            if any(token in component.name.lower() for token in tokens)
        )
        if matched_mass <= 1e-9 and impurity_id in {"color_bodies", "aqueous_chloride_losses"}:
            matched_mass = 0.001 * max(product_mass, 1.0)
        elif matched_mass <= 1e-9:
            unresolved_ids.append(impurity_id)
        items.append(
            BACImpurityItem(
                impurity_id=impurity_id,
                name=name,
                impurity_class=impurity_class,
                origin_section=origin_section,
                control_section=control_section,
                fate=fate,
                estimated_mass_flow_kg_hr=round(matched_mass, 6),
                estimated_mass_fraction=round(matched_mass / max(product_mass, 1.0), 8),
                severity="high" if "benzyl" in impurity_id else "moderate",
                status="blocked" if impurity_id in unresolved_ids else "method_derived",
            )
        )
    markdown = "\n".join(
        [
            "| Impurity | Class | Origin | Control Section | kg/h | Mass Fraction | Status |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {item.name} | {item.impurity_class} | {item.origin_section} | {item.control_section} | "
                f"{item.estimated_mass_flow_kg_hr:.6f} | {item.estimated_mass_fraction:.8f} | {item.status} |"
                for item in items
            ],
        ]
    )
    return BACImpurityModelArtifact(
        route_id=route_selection.selected_route_id,
        selected_route_name=route_selection.selected_route_id,
        product_basis_active_fraction=commercial_basis.active_fraction if commercial_basis is not None else 1.0,
        items=items,
        product_quality_targets=list(commercial_basis.quality_targets if commercial_basis is not None else []),
        unresolved_impurity_ids=unresolved_ids,
        markdown=markdown,
        citations=stream_table.citations if stream_table is not None else route_selection.citations,
        assumptions=(stream_table.assumptions if stream_table is not None else route_selection.assumptions)
        + ["BAC impurity model is derived from solved product and waste components plus route-specific residual classes."],
    )


def build_bac_purification_section_artifact(
    route_selection: RouteSelectionArtifact,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None,
    separation_thermo: SeparationThermoArtifact | None,
    stream_table: StreamTable | None = None,
) -> BACPurificationSectionArtifact | None:
    if route_selection.selected_route_id == "":
        return None
    route_tokens = " ".join(
        item
        for item in [
            route_selection.selected_route_id,
            flowsheet_blueprint.route_id if flowsheet_blueprint is not None else "",
            flowsheet_blueprint.blueprint_id if flowsheet_blueprint is not None else "",
        ]
        if item
    ).lower()
    if not any(token in route_tokens for token in ("benzyl", "quaternization", "benzalkonium", "bac")):
        return None
    if flowsheet_blueprint is None:
        return None
    sections: list[BACPurificationSection] = []
    unresolved_section_ids: list[str] = []
    thermo_method = (
        separation_thermo.relative_volatility.method
        if separation_thermo is not None and separation_thermo.relative_volatility is not None
        else separation_thermo.separation_family if separation_thermo is not None else ""
    )
    activity_model = separation_thermo.activity_model if separation_thermo is not None else ""
    thermo_status = ScientificGateStatus.PASS if separation_thermo is not None else ScientificGateStatus.SCREENING_ONLY
    thermo_confidence = ScientificConfidence.METHOD_DERIVED if separation_thermo is not None else ScientificConfidence.SCREENING
    for step in flowsheet_blueprint.steps:
        if step.step_role not in {"primary_separation", "concentration", "purification", "recycle_recovery"}:
            continue
        key_species: list[str] = []
        if step.step_role == "concentration":
            key_species = ["Benzyl chloride", "Ethanol", "Water"]
        elif step.step_role == "purification":
            key_species = [separation_thermo.light_key, separation_thermo.heavy_key] if separation_thermo is not None else ["Benzyl chloride", "Alkyldimethylamine"]
        elif step.step_role == "recycle_recovery":
            key_species = ["Alkyldimethylamine", "Ethanol"]
        else:
            key_species = ["Benzyl chloride", "Ethanol"]
        recovery_targets = [item for item in key_species if item]
        purge_targets = ["Residual free amine", "Residual benzyl chloride", "Color bodies"] if step.step_role in {"purification", "recycle_recovery"} else ["Light ends"]
        status = thermo_status if step.step_role in {"primary_separation", "concentration", "purification"} else ScientificGateStatus.SCREENING_ONLY
        confidence = thermo_confidence if step.step_role in {"primary_separation", "concentration", "purification"} else ScientificConfidence.SCREENING
        if status != ScientificGateStatus.PASS:
            unresolved_section_ids.append(step.step_id)
        sections.append(
            BACPurificationSection(
                section_id=step.section_id,
                step_id=step.step_id,
                label=step.section_label,
                service=step.service,
                separation_family="evaporation" if step.step_role == "concentration" else "distillation" if step.step_role == "purification" else "recovery",
                key_species=[item for item in key_species if item],
                recovery_targets=recovery_targets,
                purge_targets=purge_targets,
                thermo_method=thermo_method,
                activity_model=activity_model,
                status=status,
                confidence=confidence,
                notes=list(step.notes),
                citations=sorted(set(step.citations + (separation_thermo.citations if separation_thermo is not None else []))),
                assumptions=step.assumptions + (separation_thermo.assumptions if separation_thermo is not None else []),
            )
        )
    markdown = "\n".join(
        [
            "| Step | Label | Service | Family | Key Species | Thermo | Activity | Status |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {section.step_id} | {section.label} | {section.service} | {section.separation_family} | "
                f"{', '.join(section.key_species) or '-'} | {section.thermo_method or '-'} | {section.activity_model or '-'} | {section.status.value} |"
                for section in sections
            ],
        ]
    )
    return BACPurificationSectionArtifact(
        route_id=route_selection.selected_route_id,
        blueprint_id=flowsheet_blueprint.blueprint_id,
        sections=sections,
        unresolved_section_ids=sorted(set(unresolved_section_ids)),
        markdown=markdown,
        citations=sorted({citation for section in sections for citation in section.citations}),
        assumptions=sorted({assumption for section in sections for assumption in section.assumptions}),
    )


def _unit_alias_map(flowsheet_blueprint: FlowsheetBlueprintArtifact) -> dict[str, list[str]]:
    alias_map: dict[str, list[str]] = {}
    defaults = {
        "feed_prep": ["feed_prep", "E-101"],
        "reactor": ["reactor", "R-101", "CONV-101"],
        "primary_flash": ["primary_flash", "V-101", "ABS-201"],
        "primary_separation": ["primary_separation", "primary_flash", "V-101", "ABS-201"],
        "concentration": ["concentration", "EV-101", "STR-201"],
        "purification": ["purification", "D-101", "PU-201", "SR-301", "E-201"],
        "recycle_recovery": ["recycle_recovery", "STR-201"],
        "filtration": ["filtration", "FILT-201"],
        "drying": ["drying", "DRY-301"],
        "storage": ["storage", "T-101", "TK-101", "TK-301"],
        "waste_treatment": ["waste_treatment", "WW-101"],
    }
    for step in flowsheet_blueprint.steps:
        alias_map[step.unit_id] = list(dict.fromkeys([step.unit_id, step.solver_anchor_unit_id, *(defaults.get(step.unit_id, []))] + ([step.unit_tag] if step.unit_tag else [])))
    return alias_map


def build_unit_train_consistency_artifact(
    flowsheet_blueprint: FlowsheetBlueprintArtifact,
    stream_table: StreamTable | None = None,
    energy_balance: EnergyBalance | None = None,
    equipment_list: EquipmentListArtifact | None = None,
    control_plan: ControlPlanArtifact | None = None,
    reactor_design: ReactorDesign | None = None,
    column_design: ColumnDesign | None = None,
    cost_model: CostModel | None = None,
) -> UnitTrainConsistencyArtifact:
    alias_map = _unit_alias_map(flowsheet_blueprint)
    canonical_unit_ids = [step.unit_id for step in flowsheet_blueprint.steps]
    canonical_sections = list(dict.fromkeys(step.section_id for step in flowsheet_blueprint.steps))
    rows: list[UnitTrainConsistencyRow] = []
    blocked_refs: list[str] = []

    def _row(artifact_ref: str, observed_unit_ids: list[str], expected_unit_ids: list[str], strict_missing: bool = True) -> UnitTrainConsistencyRow:
        observed = list(dict.fromkeys([item for item in observed_unit_ids if item]))
        expected_aliases = list(dict.fromkeys([alias for unit_id in expected_unit_ids for alias in alias_map.get(unit_id, [unit_id])]))
        unexpected = [item for item in observed if item not in expected_aliases and item not in {"battery_limits"}]
        missing = []
        if strict_missing:
            for unit_id in expected_unit_ids:
                aliases = set(alias_map.get(unit_id, [unit_id]))
                if not aliases.intersection(observed):
                    missing.append(unit_id)
        status = "pass"
        notes: list[str] = []
        if unexpected:
            status = "blocked"
            notes.append("Observed unit ids fall outside the selected BAC unit train.")
        elif missing:
            status = "warning"
            notes.append("Some expected BAC unit-train anchors are not represented in this artifact.")
        if any(item in {"CRYS-201", "FILT-201", "DRY-301"} for item in observed):
            status = "blocked"
            notes.append("Legacy solids-unit ids appeared in a liquid BAC train artifact.")
        if status == "blocked":
            blocked_refs.append(artifact_ref)
        return UnitTrainConsistencyRow(
            artifact_ref=artifact_ref,
            expected_unit_aliases=expected_aliases,
            observed_unit_ids=observed,
            missing_expected_units=missing,
            unexpected_units=unexpected,
            status=status,
            notes=notes,
            citations=flowsheet_blueprint.citations,
            assumptions=flowsheet_blueprint.assumptions,
        )

    if stream_table is not None:
        observed = sorted({packet.unit_id for packet in stream_table.unit_operation_packets})
        stream_expectation = [
            unit_id
            for unit_id in canonical_unit_ids
            if unit_id in {"feed_prep", "reactor", "primary_separation", "concentration", "purification"}
        ]
        rows.append(_row("stream_table", observed, stream_expectation, strict_missing=False))
    if energy_balance is not None:
        thermal_expectation = [
            unit_id
            for unit_id in canonical_unit_ids
            if unit_id in {
                "feed_prep",
                "reactor",
                "primary_flash",
                "primary_separation",
                "concentration",
                "purification",
                "storage",
            }
        ]
        observed = [duty.unit_id for duty in energy_balance.duties]
        rows.append(_row("energy_balance", observed, thermal_expectation))
    equipment_expectation = [
        unit_id
        for unit_id in canonical_unit_ids
        if unit_id in {"feed_prep", "reactor", "primary_separation", "concentration", "purification", "storage"}
    ]
    if equipment_list is not None:
        observed = [item.equipment_id for item in equipment_list.items]
        rows.append(_row("equipment_list", observed, equipment_expectation, strict_missing=False))
    if control_plan is not None:
        observed = [loop.unit_id for loop in control_plan.control_loops if loop.unit_id]
        rows.append(_row("control_plan", observed, ["reactor", "purification", "storage"], strict_missing=False))
    if reactor_design is not None:
        rows.append(_row("reactor_design", [reactor_design.reactor_id], ["reactor"]))
    if column_design is not None:
        rows.append(_row("column_design", [column_design.column_id], ["purification"], strict_missing=False))
    if cost_model is not None:
        observed = [item.equipment_id for item in cost_model.equipment_cost_items]
        rows.append(_row("cost_model", observed, equipment_expectation, strict_missing=False))
    overall_status = "pass"
    if any(row.status == "blocked" for row in rows):
        overall_status = "blocked"
    elif any(row.status == "warning" for row in rows):
        overall_status = "warning"
    markdown = "\n".join(
        [
            "| Artifact | Status | Missing | Unexpected |",
            "| --- | --- | --- | --- |",
            *[
                f"| {row.artifact_ref} | {row.status} | {', '.join(row.missing_expected_units) or '-'} | {', '.join(row.unexpected_units) or '-'} |"
                for row in rows
            ],
        ]
    )
    return UnitTrainConsistencyArtifact(
        route_id=flowsheet_blueprint.route_id,
        blueprint_id=flowsheet_blueprint.blueprint_id,
        canonical_unit_ids=canonical_unit_ids,
        canonical_sections=canonical_sections,
        alias_map=alias_map,
        rows=rows,
        overall_status=overall_status,
        blocking_artifact_refs=sorted(set(blocked_refs)),
        markdown=markdown,
        citations=flowsheet_blueprint.citations,
        assumptions=flowsheet_blueprint.assumptions + ["Unit-train consistency is benchmarked against the selected BAC blueprint and a controlled alias map for downstream design ids."],
    )


def _is_invalid_species_name(name: str) -> bool:
    stripped = name.strip()
    lowered = stripped.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if not stripped:
        return True
    if _NONCHEMICAL_TOKEN_RE.match(stripped):
        return True
    if normalized in _PLACEHOLDER_TOKENS:
        return True
    if any(token in lowered for token in ("page", "table", "figure", "fig.", "wt%", "mol%", "bar", "celsius")):
        return True
    words = [item for item in re.split(r"[^a-z0-9]+", lowered) if item]
    if words and all(item in _NOISE_TOKENS for item in words):
        return True
    alpha_count = sum(char.isalpha() for char in stripped)
    return alpha_count < 2


def build_species_resolution_artifact(
    route_chemistry: RouteChemistryArtifact,
    selected_route_id: str = "",
) -> SpeciesResolutionArtifact:
    records: list[SpeciesResolutionRecord] = []
    blocking_route_ids: list[str] = []
    invalid_species_names: list[str] = []
    for graph in route_chemistry.route_graphs:
        core_nodes = [
            node
            for node in graph.species_nodes
            if any(tag in {"reactant", "product", "byproduct"} for tag in node.role_tags)
        ]
        intermediate_nodes = [
            node
            for node in graph.species_nodes
            if not any(tag in {"reactant", "product", "byproduct"} for tag in node.role_tags)
            and "document_mention" not in node.role_tags
        ]
        valid_core_species_ids: list[str] = []
        invalid_core_species_names: list[str] = []
        unresolved_core_species_names: list[str] = []
        unresolved_intermediate_names: list[str] = []
        for node in core_nodes:
            if node.resolution_status == "anonymous" or _is_invalid_species_name(node.canonical_name):
                invalid_core_species_names.append(node.canonical_name)
                invalid_species_names.append(node.canonical_name)
            elif node.resolution_status != "resolved":
                unresolved_core_species_names.append(node.canonical_name)
            else:
                valid_core_species_ids.append(node.species_id)
        for node in intermediate_nodes:
            if getattr(node, "species_kind", "") == "impurity_class" or "impurity_class" in node.role_tags:
                continue
            if node.resolution_status != "resolved":
                unresolved_intermediate_names.append(node.canonical_name)
        if invalid_core_species_names:
            status = ScientificGateStatus.FAIL
            blocking_route_ids.append(graph.route_id)
        elif unresolved_core_species_names or unresolved_intermediate_names:
            status = ScientificGateStatus.SCREENING_ONLY
        else:
            status = ScientificGateStatus.PASS
        markdown = "\n".join(
            [
                f"Route `{graph.route_name}` species basis.",
                f"- valid core species: {', '.join(valid_core_species_ids) or 'none'}",
                f"- invalid core species: {', '.join(invalid_core_species_names) or 'none'}",
                f"- unresolved intermediates: {', '.join(unresolved_intermediate_names) or 'none'}",
            ]
        )
        records.append(
            SpeciesResolutionRecord(
                route_id=graph.route_id,
                route_name=graph.route_name,
                core_species_ids=[node.species_id for node in core_nodes],
                valid_core_species_ids=valid_core_species_ids,
                invalid_core_species_names=invalid_core_species_names,
                unresolved_core_species_names=unresolved_core_species_names,
                unresolved_intermediate_names=unresolved_intermediate_names,
                status=status,
                markdown=markdown,
                citations=graph.citations,
                assumptions=graph.assumptions,
            )
        )
    markdown = "\n".join(
        [
            "| Route | Status | Valid Core Species | Invalid Core Species | Unresolved Intermediates |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {record.route_name} | {record.status.value} | {', '.join(record.valid_core_species_ids) or '-'} | "
                f"{', '.join(record.invalid_core_species_names) or '-'} | {', '.join(record.unresolved_intermediate_names) or '-'} |"
                for record in records
            ],
        ]
    )
    return SpeciesResolutionArtifact(
        selected_route_id=selected_route_id,
        routes=records,
        blocking_route_ids=sorted(set(blocking_route_ids)),
        invalid_species_names=sorted(set(invalid_species_names)),
        markdown=markdown,
        citations=sorted({citation for record in records for citation in record.citations}),
        assumptions=["Core species must be valid named chemical entities before route selection is treated as design-feasible."],
    )


def build_reaction_network_v2_artifact(
    route_chemistry: RouteChemistryArtifact,
    species_resolution: SpeciesResolutionArtifact,
    selected_route_id: str = "",
) -> ReactionNetworkV2Artifact:
    species_lookup = {record.route_id: record for record in species_resolution.routes}
    routes: list[ReactionNetworkRoute] = []
    blocking_route_ids: list[str] = []
    for graph in route_chemistry.route_graphs:
        record = species_lookup.get(graph.route_id)
        blocking_issue_codes = [issue.issue_code for issue in graph.unresolved_issues if issue.blocking]
        if record is None:
            status = ScientificGateStatus.FAIL
            blocking_issue_codes.append("missing_species_resolution")
        elif record.status == ScientificGateStatus.FAIL or not graph.reaction_steps:
            status = ScientificGateStatus.FAIL
            if not graph.reaction_steps:
                blocking_issue_codes.append("missing_reaction_steps")
        elif record.status == ScientificGateStatus.SCREENING_ONLY:
            status = ScientificGateStatus.SCREENING_ONLY
        else:
            status = ScientificGateStatus.PASS
        if status == ScientificGateStatus.FAIL:
            blocking_route_ids.append(graph.route_id)
        routes.append(
            ReactionNetworkRoute(
                route_id=graph.route_id,
                route_name=graph.route_name,
                core_species_complete=record is not None and record.status != ScientificGateStatus.FAIL,
                step_count=len(graph.reaction_steps),
                reaction_steps=graph.reaction_steps,
                blocking_issue_codes=sorted(set(blocking_issue_codes)),
                status=status,
                markdown=f"{graph.route_name}: {len(graph.reaction_steps)} step(s), status={status.value}.",
                citations=graph.citations,
                assumptions=graph.assumptions,
            )
        )
    markdown = "\n".join(
        [
            "| Route | Status | Step Count | Blocking Issues |",
            "| --- | --- | --- | --- |",
            *[
                f"| {route.route_name} | {route.status.value} | {route.step_count} | {', '.join(route.blocking_issue_codes) or '-'} |"
                for route in routes
            ],
        ]
    )
    return ReactionNetworkV2Artifact(
        selected_route_id=selected_route_id,
        routes=routes,
        blocking_route_ids=sorted(set(blocking_route_ids)),
        markdown=markdown,
        citations=sorted({citation for route in routes for citation in route.citations}),
        assumptions=["Reaction network v2 preserves stepwise route chemistry and blocks detailed design when core step truth is missing."],
    )


def _primary_separation_families(route, graph, route_families: RouteFamilyArtifact | None) -> list[str]:
    hints = list(graph.major_separation_hints if graph is not None else [])
    hints.extend(route.separations)
    profile = profile_for_route(route_families, route.route_id) if route_families is not None else None
    if profile is not None:
        hints.append(profile.primary_separation_train)
    text = " ".join(hints).lower()
    families: list[str] = []
    if profile is not None and profile.route_family_id == "quaternization_liquid_train":
        if any(token in text for token in ("strip", "light-end", "light end", "flash", "vacuum", "recovery")):
            families.append("flash")
        if any(token in text for token in ("recovery", "polish", "polishing", "distill")):
            families.append("distillation")
        return list(dict.fromkeys(families or ["flash", "distillation"]))
    if "absor" in text or "strip" in text:
        families.append("absorption")
    if "extract" in text or "liquid-liquid" in text:
        families.append("extraction")
    if "crystal" in text or "filter" in text:
        families.append("crystallization")
    if "dry" in text:
        families.append("drying")
    if "evapor" in text or "concentr" in text:
        families.append("evaporation")
    if "flash" in text or "phase" in text:
        families.append("flash")
    if "distill" in text or "column" in text:
        families.append("distillation")
    if not families:
        families.append("distillation")
    return list(dict.fromkeys(families))


def _package_index(property_packages: PropertyPackageArtifact):
    return {package.identifier.identifier_id: package for package in property_packages.packages}


def _route_process_text(route, graph, blueprint: FlowsheetBlueprintArtifact | None) -> str:
    text_parts = [
        route.name,
        route.reaction_equation,
        route.scale_up_notes,
        route.rationale,
        " ".join(route.catalysts),
        " ".join(route.byproducts),
        " ".join(route.separations),
    ]
    if graph is not None:
        for step in graph.reaction_steps:
            text_parts.extend(
                [
                    step.step_label,
                    step.reaction_family,
                    " ".join(step.catalyst_names),
                    " ".join(step.solvent_names),
                    step.source_excerpt,
                ]
            )
    if blueprint is not None:
        for step in blueprint.steps:
            text_parts.extend([step.section_label, step.service, step.step_role, *step.notes])
    return " ".join(part for part in text_parts if part).lower()


def _classify_impurity_families(names: list[str]) -> set[str]:
    families: set[str] = set()
    for name in names:
        lowered = name.lower()
        if any(token in lowered for token in ("tar", "heavy", "heavies", "acetophenone", "hydroquinone", "catechol", "glycol", "alpha-methylstyrene", "propionic")):
            families.add("heavy_organics")
        if any(token in lowered for token in ("saline", "brine", "salt", "chloride", "mother liquor", "ammonium chloride")):
            families.add("salts_or_aqueous")
        if any(token in lowered for token in ("co2", "offgas", "mist", "vent", "sox", "so3", "ammonia")):
            families.add("offgas")
        if any(token in lowered for token in ("solid", "solids", "insoluble", "cake", "coke", "residue")):
            families.add("solids")
        if any(token in lowered for token in ("acid", "aldehyde", "ketone", "phenol", "alcohol")):
            families.add("oxygenated_liquids")
        if any(token in lowered for token in ("chlorinated", "chlorohydrin")):
            families.add("chlorinated")
    return families


def _cleanup_family(label: str) -> str:
    lowered = label.lower()
    if "distill" in lowered:
        return "distillation"
    if "extract" in lowered:
        return "extraction"
    if "wash" in lowered or "caustic" in lowered:
        return "washing"
    if "flash" in lowered or "phase split" in lowered or "quench" in lowered:
        return "phase_split"
    if "crystal" in lowered:
        return "crystallization"
    if "filter" in lowered or "clar" in lowered or "salt removal" in lowered:
        return "solids_cleanup"
    if "dry" in lowered:
        return "drying"
    if "absorp" in lowered or "gas cleanup" in lowered:
        return "scrubbing"
    if "recovery" in lowered or "recycle" in lowered or "regeneration" in lowered or "cleanup" in lowered:
        return "recovery"
    return "generic_cleanup"


def _waste_treatment_modes(route, graph, blueprint: FlowsheetBlueprintArtifact | None) -> set[str]:
    modes: set[str] = set()
    text = _route_process_text(route, graph, blueprint)
    if any(token in text for token in ("saline", "brine", "mother liquor", "caustic wash", "salt removal", "ammonium chloride")):
        modes.add("aqueous_treatment")
    if any(token in text for token in ("offgas", "gas vent", "gas cleanup", "mist", "sox", "so3", "ammonia")):
        modes.add("gas_scrubbing")
    if any(token in text for token in ("chlorinated", "chloride")):
        modes.add("halogenated_waste")
    if any(token in text for token in ("tar", "heavy", "solvent recovery", "organic", "acetophenone", "alpha-methylstyrene", "phenol")):
        modes.add("organic_recovery_or_incineration")
    if any(token in text for token in ("solid", "solids", "insoluble", "filter", "cake", "drying")):
        modes.add("solids_handling")
    if route.catalysts:
        modes.add("catalyst_or_media_service")
    return modes


def build_route_process_claims_artifact(
    route_survey,
    route_chemistry: RouteChemistryArtifact,
    candidate_set,
) -> RouteProcessClaimsArtifact:
    graph_lookup = _route_lookup(route_chemistry)
    blueprint_lookup = {blueprint.route_id: blueprint for blueprint in candidate_set.blueprints} if candidate_set is not None else {}
    claims: list[RouteProcessClaimRecord] = []
    for route in route_survey.routes:
        graph = graph_lookup.get(route.route_id)
        blueprint = blueprint_lookup.get(route.route_id)
        recoverable_species: set[str] = set()
        catalyst_step_count = 0
        if graph is not None:
            for step in graph.reaction_steps:
                recoverable_species.update(name for name in step.solvent_names if name)
                if step.catalyst_names:
                    catalyst_step_count += 1
        recycle_intent_count = len(blueprint.recycle_intents) if blueprint is not None else 0
        if blueprint is not None:
            for intent in blueprint.recycle_intents:
                recoverable_species.update(name for name in intent.closing_species if name)
        recovery_sections = [
            item
            for item in route.separations
            if any(token in item.lower() for token in ("recovery", "recycle", "cleanup", "regeneration", "wash"))
        ]
        recycle_status = ScientificGateStatus.PASS if blueprint is not None else ScientificGateStatus.SCREENING_ONLY
        claims.append(
            RouteProcessClaimRecord(
                route_id=route.route_id,
                route_name=route.name,
                claim_type="reagent_recycle",
                status=recycle_status,
                items=sorted(recoverable_species),
                item_count=len(recoverable_species),
                metrics={
                    "recoverable_species_count": float(len(recoverable_species)),
                    "recycle_intent_count": float(recycle_intent_count),
                    "catalyst_step_count": float(catalyst_step_count),
                    "recovery_section_count": float(len(recovery_sections)),
                },
                rationale="Recoverable reagent / solvent closure is inferred from route chemistry steps and blueprint recycle intents.",
                citations=route.citations + ((graph.citations if graph is not None else []) if graph is not None else []),
                assumptions=route.assumptions,
            )
        )

        impurity_families = sorted(_classify_impurity_families(route.byproducts))
        cleanup_families: set[str] = set()
        for separation in route.separations:
            cleanup_families.add(_cleanup_family(separation))
        if blueprint is not None:
            for duty in blueprint.separation_duties:
                cleanup_families.add(duty.separation_family or "generic_cleanup")
            for step in blueprint.steps:
                if step.step_role in {"phase_split", "purification", "recycle_recovery", "filtration", "drying", "waste_treatment"}:
                    cleanup_families.add(step.step_role)
        impurity_status = ScientificGateStatus.PASS if graph is not None else ScientificGateStatus.SCREENING_ONLY
        claims.append(
            RouteProcessClaimRecord(
                route_id=route.route_id,
                route_name=route.name,
                claim_type="impurity_classes",
                status=impurity_status,
                items=impurity_families,
                item_count=len(impurity_families),
                metrics={
                    "byproduct_count": float(len(route.byproducts)),
                    "impurity_family_count": float(len(impurity_families)),
                },
                rationale="Impurity classes are inferred from named byproducts and route-level impurity cues.",
                citations=route.citations,
                assumptions=route.assumptions,
            )
        )
        claims.append(
            RouteProcessClaimRecord(
                route_id=route.route_id,
                route_name=route.name,
                claim_type="cleanup_sequence",
                status=ScientificGateStatus.PASS if blueprint is not None else ScientificGateStatus.SCREENING_ONLY,
                items=sorted(cleanup_families),
                item_count=len(cleanup_families),
                metrics={
                    "cleanup_family_count": float(len(cleanup_families)),
                    "cleanup_section_count": float(len(route.separations)),
                },
                rationale="Cleanup sequence is inferred from named separation sections and conceptual blueprint duties.",
                citations=route.citations + (blueprint.citations if blueprint is not None else []),
                assumptions=route.assumptions + (blueprint.assumptions if blueprint is not None else []),
            )
        )

        waste_modes = sorted(_waste_treatment_modes(route, graph, blueprint))
        claims.append(
            RouteProcessClaimRecord(
                route_id=route.route_id,
                route_name=route.name,
                claim_type="waste_modes",
                status=ScientificGateStatus.PASS if blueprint is not None else ScientificGateStatus.SCREENING_ONLY,
                items=waste_modes,
                item_count=len(waste_modes),
                metrics={
                    "waste_mode_count": float(len(waste_modes)),
                    "has_halogenated_waste": 1.0 if "halogenated_waste" in waste_modes else 0.0,
                    "has_aqueous_treatment": 1.0 if "aqueous_treatment" in waste_modes else 0.0,
                    "has_gas_scrubbing": 1.0 if "gas_scrubbing" in waste_modes else 0.0,
                },
                rationale="Waste-treatment modes are inferred from route byproducts, cleanup sections, and blueprint waste/recovery structure.",
                citations=route.citations + (blueprint.citations if blueprint is not None else []),
                assumptions=route.assumptions + (blueprint.assumptions if blueprint is not None else []),
            )
        )
    markdown = "\n".join(
        [
            "| Route | Claim | Status | Items | Metrics |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {claim.route_name} | {claim.claim_type} | {claim.status.value} | {', '.join(claim.items) or '-'} | "
                f"{', '.join(f'{key}={value:.1f}' for key, value in sorted(claim.metrics.items())) or '-'} |"
                for claim in claims
            ],
        ]
    )
    return RouteProcessClaimsArtifact(
        claims=claims,
        markdown=markdown,
        citations=sorted({citation for claim in claims for citation in claim.citations}),
        assumptions=sorted({assumption for claim in claims for assumption in claim.assumptions}),
    )


def _prop_status(package, property_name: str) -> tuple[bool, bool]:
    prop = getattr(package, property_name, None) if package is not None else None
    if prop is None:
        return False, False
    if getattr(prop, "blocking", False) or getattr(prop, "resolution_status", "") == "blocked":
        return False, False
    if getattr(prop, "provenance_method", None) is not None and getattr(prop.provenance_method, "value", "") in {"estimated", "analogy"}:
        return True, False
    if getattr(prop, "resolution_status", "") == "estimated":
        return True, False
    return True, True


def _has_principal_henry_basis(
    property_packages: PropertyPackageArtifact,
    key_species: Sequence[str],
) -> bool:
    key_set = {species_id for species_id in key_species if species_id}
    if not key_set:
        return bool(property_packages.henry_law_constants)
    for constant in property_packages.henry_law_constants:
        if (
            constant.gas_component_id in key_set
            or constant.solvent_component_id in key_set
        ):
            return True
    return False


def _has_principal_solubility_basis(
    property_packages: PropertyPackageArtifact,
    key_species: Sequence[str],
) -> bool:
    key_set = {species_id for species_id in key_species if species_id}
    if not key_set:
        return bool(property_packages.solubility_curves)
    for curve in property_packages.solubility_curves:
        if (
            curve.solute_component_id in key_set
            or curve.solvent_component_id in key_set
        ):
            return True
    return False


def _relevant_species_for_family(
    graph,
    family: str,
    fallback_species: Sequence[str],
) -> list[str]:
    if graph is None or not getattr(graph, "species_nodes", None):
        return list(fallback_species)
    nodes = list(graph.species_nodes)
    if family in {"distillation", "evaporation", "flash"}:
        species_ids = [
            node.species_id
            for node in nodes
            if node.species_kind != "impurity_class"
            and node.volatility_class in {"volatile", "semivolatile", "carrier"}
            and node.commercial_role != "active_bundle"
        ]
        if species_ids:
            return list(dict.fromkeys(species_ids))
    if family in {"crystallization", "drying"}:
        preferred_tags = {"product", "byproduct", "solvent", "carrier"}
    elif family == "absorption":
        preferred_tags = {"reactant", "product", "byproduct", "solvent", "carrier"}
    else:
        preferred_tags = {"reactant", "product", "byproduct", "solvent", "carrier"}
    species_ids = [
        node.species_id
        for node in nodes
        if node.species_kind != "impurity_class"
        and any(tag in preferred_tags for tag in node.role_tags)
    ]
    if species_ids:
        return list(dict.fromkeys(species_ids))
    fallback_lookup = _node_lookup(graph)
    filtered_fallback = [
        species_id
        for species_id in fallback_species
        if species_id not in fallback_lookup or fallback_lookup[species_id].commercial_role != "active_bundle"
    ]
    return filtered_fallback or list(fallback_species)


def _required_inputs_for_species(
    graph,
    family: str,
    species_id: str,
    default_inputs: Sequence[str],
) -> list[str]:
    if graph is None or not getattr(graph, "species_nodes", None):
        return list(default_inputs)
    node = next((item for item in graph.species_nodes if item.species_id == species_id), None)
    role_tags = set(node.role_tags) if node is not None else set()
    if node is not None and node.commercial_role == "active_bundle":
        if family in {"distillation", "evaporation", "flash"}:
            return []
        if family == "drying":
            return ["molecular_weight", "liquid_density"]
    if family != "drying":
        return list(default_inputs)
    if "product" in role_tags and not role_tags.intersection({"solvent", "byproduct"}):
        return ["molecular_weight"]
    if "reactant" in role_tags and not role_tags.intersection({"solvent", "byproduct"}):
        return ["molecular_weight"]
    return list(default_inputs)


def build_thermo_admissibility_artifact(
    route_survey,
    route_chemistry: RouteChemistryArtifact,
    property_packages: PropertyPackageArtifact,
    route_families: RouteFamilyArtifact | None = None,
    *,
    selected_route_id: str = "",
    separation_thermo: SeparationThermoArtifact | None = None,
    property_method: PropertyMethodDecision | None = None,
) -> ThermoAdmissibilityArtifact:
    graph_lookup = _route_lookup(route_chemistry)
    packages = _package_index(property_packages)
    sections: list[ThermoSectionAdmissibility] = []
    route_status: dict[str, ScientificGateStatus] = {}
    route_confidence: dict[str, ScientificConfidence] = {}
    blocking_route_ids: list[str] = []
    property_method_id = property_method.decision.selected_candidate_id if property_method is not None else ""
    for route in route_survey.routes:
        graph = graph_lookup.get(route.route_id)
        families = _primary_separation_families(route, graph, route_families)
        overall_status = ScientificGateStatus.PASS
        overall_confidence = ScientificConfidence.METHOD_DERIVED
        key_species = [
            node.species_id
            for node in (graph.species_nodes if graph is not None else [])
            if any(tag in {"reactant", "product", "byproduct"} for tag in node.role_tags)
        ]
        if not key_species:
            key_species = [re.sub(r"[^a-z0-9]+", "_", part.name.lower()).strip("_") for part in route.participants[:3]]
        for family in families:
            required_inputs = list(_THERMO_INPUTS_BY_FAMILY.get(family, ("molecular_weight",)))
            missing_inputs: list[str] = []
            has_screening_basis = True
            has_detailed_basis = True
            family_species = _relevant_species_for_family(graph, family, key_species)
            for species_id in family_species[:3]:
                package = packages.get(species_id)
                species_required_inputs = _required_inputs_for_species(graph, family, species_id, required_inputs)
                for prop_name in species_required_inputs:
                    covered, detailed = _prop_status(package, prop_name)
                    if not covered:
                        has_screening_basis = False
                        has_detailed_basis = False
                        missing_inputs.append(f"{species_id}:{prop_name}")
                    elif not detailed:
                        has_detailed_basis = False
                        missing_inputs.append(f"{species_id}:{prop_name}:detailed")
            if family == "absorption":
                has_principal_basis = _has_principal_henry_basis(property_packages, family_species)
                if property_packages.unresolved_henry_pairs:
                    has_detailed_basis = False
                    if not property_packages.henry_law_constants:
                        has_screening_basis = False
                    missing_inputs.extend(property_packages.unresolved_henry_pairs[:4])
                if (
                    route.route_id == selected_route_id
                    and route.route_origin == "seeded"
                    and has_principal_basis
                    and property_method_id in {"direct_public_data", "correlation_interpolation", "hybrid_cited_plus_library"}
                ):
                    has_screening_basis = True
                    has_detailed_basis = True
            if family == "extraction":
                if property_packages.unresolved_binary_pairs:
                    has_detailed_basis = False
                    if not property_packages.binary_interaction_parameters:
                        has_screening_basis = False
                    missing_inputs.extend(property_packages.unresolved_binary_pairs[:4])
            if family == "crystallization":
                has_principal_basis = _has_principal_solubility_basis(property_packages, family_species)
                if property_packages.unresolved_solubility_pairs:
                    has_detailed_basis = False
                    if not property_packages.solubility_curves:
                        has_screening_basis = False
                    missing_inputs.extend(property_packages.unresolved_solubility_pairs[:4])
                if (
                    route.route_id == selected_route_id
                    and route.route_origin == "seeded"
                    and has_principal_basis
                    and property_method_id in {"direct_public_data", "correlation_interpolation", "hybrid_cited_plus_library"}
                ):
                    has_screening_basis = True
                    has_detailed_basis = True
            if separation_thermo is not None and route.route_id == selected_route_id and family in {"distillation", "evaporation", "flash"}:
                if separation_thermo.relative_volatility is None or not separation_thermo.relative_volatility.feasible:
                    has_detailed_basis = False
                    if not has_screening_basis:
                        has_screening_basis = False
                    missing_inputs.append("relative_volatility")
                if separation_thermo.missing_binary_pairs:
                    has_detailed_basis = False
                if (
                    separation_thermo.relative_volatility is not None
                    and separation_thermo.relative_volatility.feasible
                    and (
                        route.route_origin == "seeded"
                        or property_method_id in {"direct_public_data", "correlation_interpolation", "hybrid_cited_plus_library"}
                    )
                ):
                    has_screening_basis = True
                    has_detailed_basis = True
                    missing_inputs = [
                        item
                        for item in missing_inputs
                        if item not in {"relative_volatility", *separation_thermo.missing_binary_pairs}
                        and not item.endswith(":detailed")
                    ]
            if not has_screening_basis:
                status = ScientificGateStatus.FAIL
                confidence = ScientificConfidence.BLOCKED
                rationale = "Required thermodynamic anchors are missing for the principal separation section."
            elif has_detailed_basis:
                status = ScientificGateStatus.PASS
                if property_method_id == "direct_public_data":
                    confidence = ScientificConfidence.DETAILED
                elif property_method_id == "correlation_interpolation" or property_method is None:
                    confidence = ScientificConfidence.METHOD_DERIVED
                else:
                    confidence = ScientificConfidence.METHOD_DERIVED
                rationale = "Section has an admissible thermodynamic method basis for detailed design."
            else:
                status = ScientificGateStatus.SCREENING_ONLY
                confidence = ScientificConfidence.SCREENING
                rationale = "Section can be screened thermodynamically, but not defended as detailed design."
            if profile_for_route(route_families, route.route_id) is not None and profile_for_route(route_families, route.route_id).route_family_id == "quaternization_liquid_train" and family in {"distillation", "evaporation", "flash"}:
                rationale += " Nonvolatile BAC active is treated as a retained solution-phase product, so admissibility is judged on solvent and light-end cleanup rather than active distillation."
            sections.append(
                ThermoSectionAdmissibility(
                    route_id=route.route_id,
                    section_id=f"{route.route_id}_{family}",
                    separation_family=family,
                    method_family=family,
                    status=status,
                    confidence=confidence,
                    required_inputs=required_inputs,
                    missing_inputs=sorted(set(missing_inputs)),
                    rationale=rationale,
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
            overall_status = _gate_worst(overall_status, status)
            if _confidence_rank(confidence) > _confidence_rank(overall_confidence):
                overall_confidence = confidence
        route_status[route.route_id] = overall_status
        route_confidence[route.route_id] = overall_confidence
        if overall_status == ScientificGateStatus.FAIL:
            blocking_route_ids.append(route.route_id)
    selected_status = route_status.get(selected_route_id, ScientificGateStatus.SCREENING_ONLY if selected_route_id else ScientificGateStatus.PASS)
    selected_confidence = route_confidence.get(selected_route_id, ScientificConfidence.SCREENING if selected_route_id else ScientificConfidence.METHOD_DERIVED)
    markdown = "\n".join(
        [
            "| Route | Section | Status | Confidence | Missing Inputs |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {section.route_id} | {section.separation_family} | {section.status.value} | {section.confidence.value} | "
                f"{', '.join(section.missing_inputs) or '-'} |"
                for section in sections
            ],
        ]
    )
    return ThermoAdmissibilityArtifact(
        selected_route_id=selected_route_id,
        selected_route_status=selected_status,
        selected_route_confidence=selected_confidence,
        route_status=route_status,
        route_confidence=route_confidence,
        sections=sections,
        blocking_route_ids=sorted(set(blocking_route_ids)),
        markdown=markdown,
        citations=sorted({citation for section in sections for citation in section.citations}),
        assumptions=["Thermo admissibility distinguishes detailed-design method support from screening-only separation support."],
    )


def _route_is_kinetics_critical(route, graph) -> bool:
    families = {step.reaction_family.lower() for step in (graph.reaction_steps if graph is not None else []) if step.reaction_family}
    families.update(item.lower() for item in route.reaction_family_hints)
    if families & _HIGH_KINETICS_FAMILIES:
        return True
    return any(hazard.severity == "high" for hazard in route.hazards)


def _is_bac_quaternization_route(route, graph) -> bool:
    text_parts = [
        route.route_id,
        route.name,
        route.reaction_equation,
        *route.reaction_family_hints,
        *route.solvents,
        *route.separations,
    ]
    if graph is not None:
        for step in graph.reaction_steps:
            text_parts.extend(
                [
                    step.reaction_family,
                    *step.reactant_species_ids,
                    *step.product_species_ids,
                    *step.byproduct_species_ids,
                    *step.solvent_names,
                ]
            )
    text = " ".join(part for part in text_parts if part).lower()
    return (
        "quaternization" in text
        and any(token in text for token in ("benzalkonium", "bac", "benzyl chloride", "alkyl dimethyl amine", "alkyldimethylamine"))
    )


def build_kinetics_admissibility_artifact(
    route_survey,
    route_chemistry: RouteChemistryArtifact,
    *,
    selected_route_id: str = "",
    kinetics_method: MethodSelectionArtifact | None = None,
    kinetic_assessment: KineticAssessmentArtifact | None = None,
) -> KineticsAdmissibilityArtifact:
    graph_lookup = _route_lookup(route_chemistry)
    steps: list[KineticsStepAdmissibility] = []
    route_status: dict[str, ScientificGateStatus] = {}
    route_confidence: dict[str, ScientificConfidence] = {}
    blocking_route_ids: list[str] = []
    selected_method = kinetics_method.decision.selected_candidate_id if kinetics_method is not None else ""
    for route in route_survey.routes:
        graph = graph_lookup.get(route.route_id)
        critical = _route_is_kinetics_critical(route, graph)
        bac_quaternization = _is_bac_quaternization_route(route, graph)
        route_steps = graph.reaction_steps if graph is not None and graph.reaction_steps else []
        if not route_steps:
            route_steps = []
        overall_status = ScientificGateStatus.PASS
        overall_confidence = ScientificConfidence.METHOD_DERIVED
        for index, step in enumerate(route_steps or [], start=1):
            if route.route_id == selected_route_id and kinetics_method is not None and kinetic_assessment is not None:
                if selected_method == "cited_rate_law":
                    status = ScientificGateStatus.PASS
                    confidence = ScientificConfidence.DETAILED
                    rationale = "Cited kinetic basis supports detailed reactor design."
                elif selected_method == "arrhenius_fit":
                    status = ScientificGateStatus.PASS
                    confidence = ScientificConfidence.METHOD_DERIVED
                    rationale = "Arrhenius-style fit supports method-derived reactor design."
                elif selected_method == "apparent_order_fit":
                    status = ScientificGateStatus.SCREENING_ONLY
                    confidence = ScientificConfidence.SCREENING
                    rationale = "Only apparent-order screening kinetics are available."
                else:
                    status = ScientificGateStatus.FAIL if critical else ScientificGateStatus.SCREENING_ONLY
                    confidence = ScientificConfidence.BLOCKED if critical else ScientificConfidence.SCREENING
                    rationale = "Only analogy kinetics are available for this route."
            else:
                if bac_quaternization:
                    status = ScientificGateStatus.PASS
                    confidence = ScientificConfidence.METHOD_DERIVED
                    rationale = "BAC quaternization family retains a method-derived kinetics basis for preliminary reactor design."
                elif route.route_origin == "seeded" and not critical:
                    status = ScientificGateStatus.PASS
                    confidence = ScientificConfidence.METHOD_DERIVED
                    rationale = "Curated seeded route retains a method-derived kinetics basis."
                elif route.route_origin == "seeded":
                    status = ScientificGateStatus.SCREENING_ONLY
                    confidence = ScientificConfidence.SCREENING
                    rationale = "Seeded route can be screened, but kinetics remain critical."
                else:
                    status = ScientificGateStatus.FAIL if critical else ScientificGateStatus.SCREENING_ONLY
                    confidence = ScientificConfidence.BLOCKED if critical else ScientificConfidence.SCREENING
                    rationale = "Unseen route does not yet have admissible detailed kinetics."
            steps.append(
                KineticsStepAdmissibility(
                    route_id=route.route_id,
                    step_id=step.step_id or f"{route.route_id}_step_{index}",
                    reaction_family=step.reaction_family,
                    status=status,
                    confidence=confidence,
                    kinetics_required=True,
                    rationale=rationale,
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
            overall_status = _gate_worst(overall_status, status)
            if _confidence_rank(confidence) > _confidence_rank(overall_confidence):
                overall_confidence = confidence
        if not route_steps:
            overall_status = ScientificGateStatus.FAIL
            overall_confidence = ScientificConfidence.BLOCKED
        route_status[route.route_id] = overall_status
        route_confidence[route.route_id] = overall_confidence
        if overall_status == ScientificGateStatus.FAIL:
            blocking_route_ids.append(route.route_id)
    selected_status = route_status.get(selected_route_id, ScientificGateStatus.SCREENING_ONLY if selected_route_id else ScientificGateStatus.PASS)
    selected_confidence = route_confidence.get(selected_route_id, ScientificConfidence.SCREENING if selected_route_id else ScientificConfidence.METHOD_DERIVED)
    markdown = "\n".join(
        [
            "| Route | Step | Status | Confidence | Rationale |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {step.route_id} | {step.step_id} | {step.status.value} | {step.confidence.value} | {step.rationale} |"
                for step in steps
            ],
        ]
    )
    return KineticsAdmissibilityArtifact(
        selected_route_id=selected_route_id,
        selected_route_status=selected_status,
        selected_route_confidence=selected_confidence,
        route_status=route_status,
        route_confidence=route_confidence,
        steps=steps,
        blocking_route_ids=sorted(set(blocking_route_ids)),
        markdown=markdown,
        citations=sorted({citation for step in steps for citation in step.citations}),
        assumptions=["Kinetics admissibility separates seeded method-derived support from screening-only or blocked unseen-route kinetics."],
    )


def build_flowsheet_intent_artifact(blueprint: FlowsheetBlueprintArtifact) -> FlowsheetIntentArtifact:
    intents = [
        FlowsheetIntentItem(
            route_id=blueprint.route_id,
            step_id=step.step_id,
            intent_type=step.step_role,
            unit_id=step.unit_id,
            service=step.service,
            phase_basis=step.phase_basis,
            upstream_intent_ids=step.upstream_step_ids,
            basis=step.separation_basis_ref or step.reaction_step_ref or step.service,
            citations=step.citations,
            assumptions=step.assumptions,
        )
        for step in blueprint.steps
    ]
    markdown = "\n".join(
        [
            "| Intent | Unit | Service | Phase Basis | Upstream |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {item.intent_type} | {item.unit_id} | {item.service} | {item.phase_basis or '-'} | "
                f"{', '.join(item.upstream_intent_ids) or '-'} |"
                for item in intents
            ],
        ]
    )
    return FlowsheetIntentArtifact(
        route_id=blueprint.route_id,
        blueprint_id=blueprint.blueprint_id,
        batch_capable=blueprint.batch_capable,
        intents=intents,
        markdown=markdown,
        citations=blueprint.citations,
        assumptions=blueprint.assumptions,
    )


def build_topology_candidate_artifact(
    candidate_set,
    species_resolution: SpeciesResolutionArtifact,
    reaction_network: ReactionNetworkV2Artifact,
    *,
    selected_route_id: str = "",
) -> TopologyCandidateArtifact:
    species_lookup = {record.route_id: record for record in species_resolution.routes}
    network_lookup = {record.route_id: record for record in reaction_network.routes}
    candidates: list[TopologyCandidateRecord] = []
    selected_blueprint_id = ""
    screening_balance_allowed = False
    route_to_unit_map: list[str] = []
    for blueprint in candidate_set.blueprints:
        record = species_lookup.get(blueprint.route_id)
        network = network_lookup.get(blueprint.route_id)
        reasons: list[str] = []
        if record is None or record.status == ScientificGateStatus.FAIL:
            status = ScientificGateStatus.FAIL
            reasons.append("invalid_species_basis")
        elif network is None or network.status == ScientificGateStatus.FAIL:
            status = ScientificGateStatus.FAIL
            reasons.append("invalid_reaction_network")
        elif not blueprint.steps:
            status = ScientificGateStatus.FAIL
            reasons.append("missing_topology_steps")
        elif record.status == ScientificGateStatus.SCREENING_ONLY or network.status == ScientificGateStatus.SCREENING_ONLY:
            status = ScientificGateStatus.SCREENING_ONLY
            reasons.append("screening_only_species_or_reaction_basis")
        else:
            status = ScientificGateStatus.PASS
        can_screen = status != ScientificGateStatus.FAIL and bool(blueprint.steps)
        if blueprint.route_id == selected_route_id:
            selected_blueprint_id = blueprint.blueprint_id
            screening_balance_allowed = can_screen
            route_to_unit_map = [f"{step.step_role}:{step.unit_id}" for step in blueprint.steps]
        candidates.append(
            TopologyCandidateRecord(
                blueprint_id=blueprint.blueprint_id,
                route_id=blueprint.route_id,
                route_name=blueprint.route_name,
                step_count=len(blueprint.steps),
                tagged_unit_count=len(blueprint.selected_unit_tags),
                status=status,
                screening_balance_allowed=can_screen,
                reasons=reasons,
                citations=blueprint.citations,
                assumptions=blueprint.assumptions,
            )
        )
    markdown = "\n".join(
        [
            "| Route | Status | Steps | Tagged Units | Screening Balance Allowed | Reasons |",
            "| --- | --- | --- | --- | --- | --- |",
            *[
                f"| {item.route_name} | {item.status.value} | {item.step_count} | {item.tagged_unit_count} | "
                f"{'yes' if item.screening_balance_allowed else 'no'} | {', '.join(item.reasons) or '-'} |"
                for item in candidates
            ],
        ]
    )
    return TopologyCandidateArtifact(
        selected_route_id=selected_route_id,
        selected_blueprint_id=selected_blueprint_id,
        screening_balance_allowed=screening_balance_allowed,
        candidates=candidates,
        route_to_unit_map=route_to_unit_map,
        markdown=markdown,
        citations=sorted({citation for item in candidates for citation in item.citations}),
        assumptions=["Topology candidates are only design-valid once the route species and reaction network pass scientific gates."],
    )


def build_design_confidence_artifact(
    *,
    selected_route_id: str,
    topology_candidates: TopologyCandidateArtifact | None,
    thermo_admissibility: ThermoAdmissibilityArtifact | None,
    kinetics_admissibility: KineticsAdmissibilityArtifact | None,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None = None,
    flowsheet_case: FlowsheetCase | None = None,
    solve_result: SolveResult | None = None,
    reactor_design=None,
    column_design=None,
    equipment_list=None,
) -> DesignConfidenceArtifact:
    def _unit_solver_confidence(step) -> ScientificConfidence:
        if solve_result is None:
            return ScientificConfidence.SCREENING
        candidate_unit_ids = [item for item in [step.solver_anchor_unit_id, step.unit_id] if item]
        if flowsheet_case is not None:
            candidate_unit_ids.extend(
                unit.unit_id
                for unit in flowsheet_case.units
                if unit.unit_type == step.unit_type
            )
        seen: set[str] = set()
        ordered_ids: list[str] = []
        for unit_id in candidate_unit_ids:
            if unit_id not in seen:
                seen.add(unit_id)
                ordered_ids.append(unit_id)
        best = ScientificConfidence.SCREENING
        for unit_id in ordered_ids:
            status = solve_result.unitwise_status.get(unit_id)
            coverage = solve_result.unitwise_coverage_status.get(unit_id)
            unresolved = solve_result.unitwise_unresolved_sensitivities.get(unit_id, [])
            blockers = solve_result.unitwise_blockers.get(unit_id, [])
            if status == "blocked" or coverage == "blocked" or blockers:
                return ScientificConfidence.BLOCKED
            if status == "converged" and coverage in {"complete", "partial"} and not unresolved:
                best = ScientificConfidence.METHOD_DERIVED
                break
            if status in {"converged", "estimated"} and coverage in {"complete", "partial"}:
                best = ScientificConfidence.SCREENING
        if best == ScientificConfidence.SCREENING and solve_result.convergence_status == "converged":
            section_status = solve_result.section_status.get(step.section_id, "")
            if section_status == "converged":
                best = ScientificConfidence.METHOD_DERIVED
        return best

    def _major_process_step(step_role: str) -> bool:
        return step_role in {"reaction", "phase_split", "primary_separation", "purification", "filtration", "drying"}

    units: list[UnitDesignConfidence] = []
    blocked_unit_ids: list[str] = []
    overall_confidence = ScientificConfidence.DETAILED
    major_confidence = ScientificConfidence.DETAILED
    topology_status = ScientificGateStatus.SCREENING_ONLY
    if topology_candidates is not None:
        selected = next((item for item in topology_candidates.candidates if item.route_id == selected_route_id), None)
        if selected is not None:
            topology_status = selected.status
    if flowsheet_blueprint is not None:
        for step in flowsheet_blueprint.steps:
            confidence = ScientificConfidence.SCREENING
            reasons: list[str] = []
            solver_confidence = _unit_solver_confidence(step)
            if topology_status == ScientificGateStatus.FAIL:
                confidence = ScientificConfidence.BLOCKED
                reasons.append("topology_not_admissible")
            elif step.step_role == "reaction":
                kinetics_confidence = kinetics_admissibility.selected_route_confidence if kinetics_admissibility is not None else ScientificConfidence.SCREENING
                thermo_confidence = thermo_admissibility.selected_route_confidence if thermo_admissibility is not None else ScientificConfidence.SCREENING
                if reactor_design is not None and kinetics_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED} and thermo_confidence != ScientificConfidence.BLOCKED:
                    confidence = ScientificConfidence.METHOD_DERIVED if kinetics_confidence == ScientificConfidence.METHOD_DERIVED else ScientificConfidence.DETAILED
                elif (
                    solver_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}
                    and kinetics_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}
                    and thermo_confidence != ScientificConfidence.BLOCKED
                    and topology_status == ScientificGateStatus.PASS
                ):
                    confidence = ScientificConfidence.METHOD_DERIVED
                elif kinetics_confidence == ScientificConfidence.BLOCKED:
                    confidence = ScientificConfidence.BLOCKED
                    reasons.append("kinetics_not_admissible")
                else:
                    confidence = ScientificConfidence.SCREENING
                    reasons.append("screening_reactor_basis")
            elif step.step_role in {"phase_split", "primary_separation", "purification", "filtration", "drying"}:
                thermo_confidence = thermo_admissibility.selected_route_confidence if thermo_admissibility is not None else ScientificConfidence.SCREENING
                if column_design is not None and thermo_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}:
                    confidence = thermo_confidence
                elif (
                    solver_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}
                    and thermo_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}
                    and topology_status == ScientificGateStatus.PASS
                ):
                    confidence = ScientificConfidence.METHOD_DERIVED
                elif thermo_confidence == ScientificConfidence.BLOCKED:
                    confidence = ScientificConfidence.BLOCKED
                    reasons.append("thermo_not_admissible")
                else:
                    confidence = ScientificConfidence.SCREENING
                    reasons.append("screening_separation_basis")
            else:
                if equipment_list is not None:
                    confidence = ScientificConfidence.METHOD_DERIVED
                elif solver_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED} and topology_status == ScientificGateStatus.PASS:
                    confidence = ScientificConfidence.METHOD_DERIVED
                else:
                    confidence = ScientificConfidence.SCREENING
                    reasons.append("support_design_not_built")
            if solve_result is not None and solve_result.unitwise_status.get(step.solver_anchor_unit_id or step.unit_id) == "blocked":
                confidence = ScientificConfidence.BLOCKED
                reasons.append("solver_blocked")
            if confidence == ScientificConfidence.BLOCKED:
                blocked_unit_ids.append(step.unit_id)
            if _major_process_step(step.step_role) and _confidence_rank(confidence) > _confidence_rank(major_confidence):
                major_confidence = confidence
            elif confidence == ScientificConfidence.BLOCKED and _confidence_rank(confidence) > _confidence_rank(major_confidence):
                major_confidence = confidence
            if _confidence_rank(confidence) > _confidence_rank(overall_confidence):
                overall_confidence = confidence
            units.append(
                UnitDesignConfidence(
                    unit_id=step.unit_id,
                    unit_type=step.unit_type,
                    confidence=confidence,
                    rationale=step.service,
                    blocking_reasons=reasons,
                )
            )
    markdown = "\n".join(
        [
            "| Unit | Type | Confidence | Reasons |",
            "| --- | --- | --- | --- |",
            *[
                f"| {unit.unit_id} | {unit.unit_type} | {unit.confidence.value} | {', '.join(unit.blocking_reasons) or '-'} |"
                for unit in units
            ],
        ]
    )
    return DesignConfidenceArtifact(
        selected_route_id=selected_route_id,
        overall_confidence=major_confidence if units else ScientificConfidence.SCREENING,
        blocked_unit_ids=sorted(set(blocked_unit_ids)),
        units=units,
        markdown=markdown,
        citations=[],
        assumptions=["Detailed unit confidence cannot exceed the admissibility of the upstream thermo and kinetics basis."],
    )


def build_economic_coverage_decision(
    *,
    route_id: str,
    route_economic_basis,
    route_site_fit,
    design_confidence: DesignConfidenceArtifact | None,
) -> EconomicCoverageDecision:
    missing_basis: list[str] = []
    if route_economic_basis is None:
        missing_basis.append("route_economic_basis")
    if route_site_fit is None:
        missing_basis.append("route_site_fit")
    if design_confidence is None:
        missing_basis.append("design_confidence")
    if missing_basis:
        status = "blocked"
        rationale = "Economics cannot proceed because route-derived science is incomplete."
    elif design_confidence.overall_confidence == ScientificConfidence.BLOCKED:
        status = "blocked"
        rationale = "Detailed economics is blocked because one or more major units remain scientifically blocked."
    elif route_economic_basis.coverage_status == "grounded" and design_confidence.overall_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED}:
        status = "detailed"
        rationale = "Economics is grounded in route-derived BOM, site fit, and admissible major-unit design basis."
    else:
        status = "screening"
        rationale = "Economics is available only at screening level because science or market coverage is not fully detailed."
    markdown = "\n".join(
        [
            f"- status: {status}",
            f"- missing_basis: {', '.join(missing_basis) or 'none'}",
            f"- rationale: {rationale}",
        ]
    )
    return EconomicCoverageDecision(
        route_id=route_id,
        status=status,
        missing_basis=missing_basis,
        rationale=rationale,
        markdown=markdown,
        citations=[],
        assumptions=["Economic coverage is gated by route-derived scientific confidence rather than chapter availability."],
    )


def build_scientific_gate_matrix_artifact(
    *,
    species_resolution: SpeciesResolutionArtifact | None,
    thermo_admissibility: ThermoAdmissibilityArtifact | None,
    kinetics_admissibility: KineticsAdmissibilityArtifact | None,
    topology_candidates: TopologyCandidateArtifact | None,
    design_confidence: DesignConfidenceArtifact | None = None,
    economic_coverage: EconomicCoverageDecision | None = None,
) -> ScientificGateMatrixArtifact:
    entries: list[ScientificGateEntry] = []
    if species_resolution is not None and species_resolution.selected_route_id:
        record = next((item for item in species_resolution.routes if item.route_id == species_resolution.selected_route_id), None)
        if record is not None:
            entries.append(
                ScientificGateEntry(
                    gate_id="species_basis",
                    domain="species",
                    status=record.status,
                    confidence=ScientificConfidence.DETAILED if record.status == ScientificGateStatus.PASS else ScientificConfidence.SCREENING if record.status == ScientificGateStatus.SCREENING_ONLY else ScientificConfidence.BLOCKED,
                    rationale="Core species identity gate for the selected route.",
                    citations=record.citations,
                    assumptions=record.assumptions,
                )
            )
    if thermo_admissibility is not None and thermo_admissibility.selected_route_id:
        entries.append(
            ScientificGateEntry(
                gate_id="thermo_basis",
                domain="thermo",
                status=thermo_admissibility.selected_route_status,
                confidence=thermo_admissibility.selected_route_confidence,
                rationale="Section-level thermo admissibility gate for the selected route.",
                citations=thermo_admissibility.citations,
                assumptions=thermo_admissibility.assumptions,
            )
        )
    if kinetics_admissibility is not None and kinetics_admissibility.selected_route_id:
        entries.append(
            ScientificGateEntry(
                gate_id="kinetics_basis",
                domain="kinetics",
                status=kinetics_admissibility.selected_route_status,
                confidence=kinetics_admissibility.selected_route_confidence,
                rationale="Reaction-step kinetics admissibility gate for the selected route.",
                citations=kinetics_admissibility.citations,
                assumptions=kinetics_admissibility.assumptions,
            )
        )
    if topology_candidates is not None and topology_candidates.selected_route_id:
        selected = next((item for item in topology_candidates.candidates if item.route_id == topology_candidates.selected_route_id), None)
        if selected is not None:
            entries.append(
                ScientificGateEntry(
                    gate_id="topology_basis",
                    domain="topology",
                    status=selected.status,
                    confidence=ScientificConfidence.METHOD_DERIVED if selected.status == ScientificGateStatus.PASS else ScientificConfidence.SCREENING if selected.status == ScientificGateStatus.SCREENING_ONLY else ScientificConfidence.BLOCKED,
                    rationale="Topology synthesis gate for the selected route.",
                    citations=selected.citations,
                    assumptions=selected.assumptions,
                )
            )
    if design_confidence is not None and design_confidence.selected_route_id:
        entries.append(
            ScientificGateEntry(
                gate_id="design_confidence",
                domain="design",
                status=ScientificGateStatus.FAIL if design_confidence.overall_confidence == ScientificConfidence.BLOCKED else ScientificGateStatus.SCREENING_ONLY if design_confidence.overall_confidence == ScientificConfidence.SCREENING else ScientificGateStatus.PASS,
                confidence=design_confidence.overall_confidence,
                rationale="Per-unit design confidence gate.",
                citations=design_confidence.citations,
                assumptions=design_confidence.assumptions,
            )
        )
    if economic_coverage is not None and economic_coverage.route_id:
        entries.append(
            ScientificGateEntry(
                gate_id="economic_basis",
                domain="economics",
                status=ScientificGateStatus.PASS if economic_coverage.status == "detailed" else ScientificGateStatus.SCREENING_ONLY if economic_coverage.status == "screening" else ScientificGateStatus.FAIL,
                confidence=ScientificConfidence.DETAILED if economic_coverage.status == "detailed" else ScientificConfidence.SCREENING if economic_coverage.status == "screening" else ScientificConfidence.BLOCKED,
                rationale=economic_coverage.rationale,
                citations=economic_coverage.citations,
                assumptions=economic_coverage.assumptions,
            )
        )
    markdown = "\n".join(
        [
            "| Gate | Domain | Status | Confidence |",
            "| --- | --- | --- | --- |",
            *[
                f"| {entry.gate_id} | {entry.domain} | {entry.status.value} | {entry.confidence.value} |"
                for entry in entries
            ],
        ]
    )
    return ScientificGateMatrixArtifact(
        entries=entries,
        markdown=markdown,
        citations=sorted({citation for entry in entries for citation in entry.citations}),
        assumptions=sorted({assumption for entry in entries for assumption in entry.assumptions}),
    )


def build_claim_graph_artifact(
    *,
    stage_id: str,
    previous: ClaimGraphArtifact | None,
    selected_route_id: str,
    species_resolution: SpeciesResolutionArtifact | None,
    reaction_network: ReactionNetworkV2Artifact | None,
    route_process_claims: RouteProcessClaimsArtifact | None,
    route_selection: RouteSelectionArtifact | None,
    thermo_admissibility: ThermoAdmissibilityArtifact | None,
    kinetics_admissibility: KineticsAdmissibilityArtifact | None,
    topology_candidates: TopologyCandidateArtifact | None,
    stream_table: StreamTable | None = None,
    energy_balance: UtilitySummaryArtifact | None = None,
    design_confidence: DesignConfidenceArtifact | None = None,
    economic_coverage: EconomicCoverageDecision | None = None,
) -> ClaimGraphArtifact:
    previous_by_id = {claim.claim_id: claim for claim in previous.claims} if previous is not None else {}
    claims: list[ScientificClaim] = []
    process_claim_lookup = {
        claim.claim_type: claim
        for claim in (route_process_claims.claims if route_process_claims is not None else [])
        if claim.route_id == selected_route_id
    }
    if species_resolution is not None and selected_route_id:
        record = next((item for item in species_resolution.routes if item.route_id == selected_route_id), None)
        if record is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"species:{selected_route_id}",
                    stage_id=stage_id,
                    domain="species",
                    subject=selected_route_id,
                    value_text=record.status.value,
                    status=ClaimStatus.RESOLVED if record.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL if record.status == ScientificGateStatus.SCREENING_ONLY else ClaimStatus.BLOCKED,
                    provenance=ScientificClaimProvenance.SOURCED,
                    uncertainty_class="identity",
                    dependency_ids=[],
                    blocking=record.status == ScientificGateStatus.FAIL,
                    citations=record.citations,
                    assumptions=record.assumptions,
                )
            )
    if reaction_network is not None and selected_route_id:
        record = next((item for item in reaction_network.routes if item.route_id == selected_route_id), None)
        if record is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"reaction_network:{selected_route_id}",
                    stage_id=stage_id,
                    domain="reaction_network",
                    subject=selected_route_id,
                    value_text=f"{record.step_count} step(s)",
                    status=ClaimStatus.RESOLVED if record.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL if record.status == ScientificGateStatus.SCREENING_ONLY else ClaimStatus.BLOCKED,
                    provenance=ScientificClaimProvenance.SOURCED,
                    uncertainty_class="route_step_truth",
                    dependency_ids=[f"species:{selected_route_id}"],
                    blocking=record.status == ScientificGateStatus.FAIL,
                    citations=record.citations,
                    assumptions=record.assumptions,
                )
            )
    if selected_route_id and process_claim_lookup:
        recycle_claim = process_claim_lookup.get("reagent_recycle")
        if recycle_claim is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"recycle_basis:{selected_route_id}",
                    stage_id=stage_id,
                    domain="recycle_basis",
                    subject=selected_route_id,
                    value_text=", ".join(recycle_claim.items) or "no explicit recoverable species",
                    status=ClaimStatus.RESOLVED if recycle_claim.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL,
                    provenance=ScientificClaimProvenance.METHOD_DERIVED,
                    uncertainty_class="process_recycle",
                    dependency_ids=[f"reaction_network:{selected_route_id}"],
                    citations=recycle_claim.citations,
                    assumptions=recycle_claim.assumptions,
                )
            )
        impurity_claim = process_claim_lookup.get("impurity_classes")
        if impurity_claim is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"impurity_classes:{selected_route_id}",
                    stage_id=stage_id,
                    domain="impurity_classes",
                    subject=selected_route_id,
                    value_text=", ".join(impurity_claim.items) or "no explicit impurity class",
                    status=ClaimStatus.RESOLVED if impurity_claim.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL,
                    provenance=ScientificClaimProvenance.METHOD_DERIVED,
                    uncertainty_class="impurity_handling",
                    dependency_ids=[f"reaction_network:{selected_route_id}"],
                    citations=impurity_claim.citations,
                    assumptions=impurity_claim.assumptions,
                )
            )
        waste_claim = process_claim_lookup.get("waste_modes")
        if waste_claim is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"waste_modes:{selected_route_id}",
                    stage_id=stage_id,
                    domain="waste_modes",
                    subject=selected_route_id,
                    value_text=", ".join(waste_claim.items) or "no explicit waste mode",
                    status=ClaimStatus.RESOLVED if waste_claim.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL,
                    provenance=ScientificClaimProvenance.METHOD_DERIVED,
                    uncertainty_class="waste_handling",
                    dependency_ids=[f"reaction_network:{selected_route_id}"],
                    citations=waste_claim.citations,
                    assumptions=waste_claim.assumptions,
                )
            )
    if route_selection is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"route_selection:{selected_route_id}",
                stage_id=stage_id,
                domain="route",
                subject=selected_route_id,
                value_text=route_selection.justification[:240],
                status=ClaimStatus.RESOLVED,
                provenance=ScientificClaimProvenance.METHOD_DERIVED,
                uncertainty_class="decision",
                dependency_ids=[f"reaction_network:{selected_route_id}"],
                citations=route_selection.citations,
                assumptions=route_selection.assumptions,
            )
        )
    if thermo_admissibility is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"thermo:{selected_route_id}",
                stage_id=stage_id,
                domain="thermo",
                subject=selected_route_id,
                value_text=thermo_admissibility.selected_route_status.value,
                status=ClaimStatus.RESOLVED if thermo_admissibility.selected_route_status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL if thermo_admissibility.selected_route_status == ScientificGateStatus.SCREENING_ONLY else ClaimStatus.BLOCKED,
                provenance=ScientificClaimProvenance.METHOD_DERIVED if thermo_admissibility.selected_route_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED} else ScientificClaimProvenance.ENVELOPE_MODEL,
                uncertainty_class="method_admissibility",
                dependency_ids=[f"species:{selected_route_id}"],
                blocking=thermo_admissibility.selected_route_status == ScientificGateStatus.FAIL,
                citations=thermo_admissibility.citations,
                assumptions=thermo_admissibility.assumptions,
            )
        )
    if kinetics_admissibility is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"kinetics:{selected_route_id}",
                stage_id=stage_id,
                domain="kinetics",
                subject=selected_route_id,
                value_text=kinetics_admissibility.selected_route_status.value,
                status=ClaimStatus.RESOLVED if kinetics_admissibility.selected_route_status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL if kinetics_admissibility.selected_route_status == ScientificGateStatus.SCREENING_ONLY else ClaimStatus.BLOCKED,
                provenance=ScientificClaimProvenance.METHOD_DERIVED if kinetics_admissibility.selected_route_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED} else ScientificClaimProvenance.ENVELOPE_MODEL,
                uncertainty_class="method_admissibility",
                dependency_ids=[f"reaction_network:{selected_route_id}"],
                blocking=kinetics_admissibility.selected_route_status == ScientificGateStatus.FAIL,
                citations=kinetics_admissibility.citations,
                assumptions=kinetics_admissibility.assumptions,
            )
        )
    if topology_candidates is not None and selected_route_id:
        selected = next((item for item in topology_candidates.candidates if item.route_id == selected_route_id), None)
        if selected is not None:
            claims.append(
                ScientificClaim(
                    claim_id=f"topology:{selected_route_id}",
                    stage_id=stage_id,
                    domain="topology",
                    subject=selected.route_id,
                    value_text=f"{selected.step_count} mapped step(s)",
                    status=ClaimStatus.RESOLVED if selected.status == ScientificGateStatus.PASS else ClaimStatus.PARTIAL if selected.status == ScientificGateStatus.SCREENING_ONLY else ClaimStatus.BLOCKED,
                    provenance=ScientificClaimProvenance.METHOD_DERIVED,
                    uncertainty_class="topology",
                    dependency_ids=[f"species:{selected_route_id}", f"reaction_network:{selected_route_id}"],
                    blocking=selected.status == ScientificGateStatus.FAIL,
                    citations=selected.citations,
                    assumptions=selected.assumptions,
                )
            )
    if stream_table is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"material_balance:{selected_route_id}",
                stage_id=stage_id,
                domain="material_balance",
                subject=selected_route_id,
                value_text=f"{len(stream_table.streams)} stream(s)",
                status=ClaimStatus.RESOLVED,
                provenance=ScientificClaimProvenance.ENVELOPE_MODEL,
                uncertainty_class="balance",
                dependency_ids=[f"topology:{selected_route_id}", f"kinetics:{selected_route_id}"],
                citations=stream_table.citations,
                assumptions=stream_table.assumptions,
            )
        )
    if design_confidence is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"design_confidence:{selected_route_id}",
                stage_id=stage_id,
                domain="design",
                subject=selected_route_id,
                value_text=design_confidence.overall_confidence.value,
                status=ClaimStatus.RESOLVED if design_confidence.overall_confidence in {ScientificConfidence.DETAILED, ScientificConfidence.METHOD_DERIVED} else ClaimStatus.PARTIAL if design_confidence.overall_confidence == ScientificConfidence.SCREENING else ClaimStatus.BLOCKED,
                provenance=ScientificClaimProvenance.METHOD_DERIVED,
                uncertainty_class="design_confidence",
                dependency_ids=[f"thermo:{selected_route_id}", f"kinetics:{selected_route_id}", f"topology:{selected_route_id}"],
                blocking=design_confidence.overall_confidence == ScientificConfidence.BLOCKED,
                citations=design_confidence.citations,
                assumptions=design_confidence.assumptions,
            )
        )
    if economic_coverage is not None and selected_route_id:
        claims.append(
            ScientificClaim(
                claim_id=f"economics:{selected_route_id}",
                stage_id=stage_id,
                domain="economics",
                subject=selected_route_id,
                value_text=economic_coverage.status,
                status=ClaimStatus.RESOLVED if economic_coverage.status == "detailed" else ClaimStatus.PARTIAL if economic_coverage.status == "screening" else ClaimStatus.BLOCKED,
                provenance=ScientificClaimProvenance.METHOD_DERIVED if economic_coverage.status == "detailed" else ScientificClaimProvenance.ENVELOPE_MODEL,
                uncertainty_class="economics",
                dependency_ids=[f"design_confidence:{selected_route_id}", f"topology:{selected_route_id}"],
                blocking=economic_coverage.status == "blocked",
                citations=economic_coverage.citations,
                assumptions=economic_coverage.assumptions,
            )
        )
    changed_claim_ids: list[str] = []
    frozen_claim_ids: list[str] = []
    for claim in claims:
        previous_claim = previous_by_id.get(claim.claim_id)
        materially_changed = previous_claim is None or any(
            getattr(previous_claim, field) != getattr(claim, field)
            for field in ("value_text", "status", "provenance", "blocking")
        )
        if materially_changed:
            claim.revision_count = 1 if previous_claim is None else previous_claim.revision_count + 1
            changed_claim_ids.append(claim.claim_id)
        else:
            claim.revision_count = previous_claim.revision_count
            claim.frozen = previous_claim.frozen or not any(dep in changed_claim_ids for dep in claim.dependency_ids)
        if claim.frozen:
            frozen_claim_ids.append(claim.claim_id)
    markdown = "\n".join(
        [
            "| Claim | Domain | Status | Provenance | Revision Count | Frozen |",
            "| --- | --- | --- | --- | --- | --- |",
            *[
                f"| {claim.claim_id} | {claim.domain} | {claim.status.value} | {claim.provenance.value} | "
                f"{claim.revision_count} | {'yes' if claim.frozen else 'no'} |"
                for claim in claims
            ],
        ]
    )
    return ClaimGraphArtifact(
        claims=claims,
        changed_claim_ids=changed_claim_ids,
        frozen_claim_ids=frozen_claim_ids,
        markdown=markdown,
        citations=sorted({citation for claim in claims for citation in claim.citations}),
        assumptions=sorted({assumption for claim in claims for assumption in claim.assumptions}),
    )


def build_inference_question_queue(
    *,
    species_resolution: SpeciesResolutionArtifact | None,
    route_process_claims: RouteProcessClaimsArtifact | None,
    thermo_admissibility: ThermoAdmissibilityArtifact | None,
    kinetics_admissibility: KineticsAdmissibilityArtifact | None,
    topology_candidates: TopologyCandidateArtifact | None,
    economic_coverage: EconomicCoverageDecision | None,
) -> InferenceQuestionQueueArtifact:
    questions: list[InferenceQuestion] = []
    if species_resolution is not None:
        for route in species_resolution.routes:
            if route.invalid_core_species_names:
                questions.append(
                    InferenceQuestion(
                        question_id=f"species_{route.route_id}",
                        domain="species_identity",
                        prompt=f"What are the validated identities of the core species in route `{route.route_name}`?",
                        why_it_matters="Invalid core species block route elimination, thermo basis, and all downstream balances.",
                        dependent_claim_ids=[f"species:{route.route_id}", f"reaction_network:{route.route_id}"],
                        evidence_targets=["named reactants", "named products", "formula support"],
                        unanswered_effect="block",
                        priority_score=100.0,
                        citations=route.citations,
                        assumptions=route.assumptions,
                )
            )
    if route_process_claims is not None:
        claim_groups: dict[str, list[RouteProcessClaimRecord]] = {}
        for claim in route_process_claims.claims:
            claim_groups.setdefault(claim.route_id, []).append(claim)
        for route_id, claims in claim_groups.items():
            partial_claims = [claim.claim_type for claim in claims if claim.status != ScientificGateStatus.PASS]
            if partial_claims:
                questions.append(
                    InferenceQuestion(
                        question_id=f"process_claims_{route_id}",
                        domain="process_screening_facts",
                        prompt=f"Which recycle, impurity-class, or waste-handling facts remain under-specified for route `{route_id}`?",
                        why_it_matters="Route screening should use typed process facts before practical burden ranking is finalized.",
                        dependent_claim_ids=[
                            f"recycle_basis:{route_id}",
                            f"impurity_classes:{route_id}",
                            f"waste_modes:{route_id}",
                        ],
                        evidence_targets=["recoverable species", "impurity families", "cleanup sequence", "waste-treatment modes"],
                        unanswered_effect="downgrade",
                        priority_score=85.0,
                        citations=sorted({citation for claim in claims for citation in claim.citations}),
                        assumptions=sorted({assumption for claim in claims for assumption in claim.assumptions}),
                    )
                )
    if thermo_admissibility is not None and thermo_admissibility.selected_route_id and thermo_admissibility.selected_route_status != ScientificGateStatus.PASS:
        questions.append(
            InferenceQuestion(
                question_id=f"thermo_{thermo_admissibility.selected_route_id}",
                domain="thermo_method_admissibility",
                prompt="Which admissible thermodynamic method and anchor properties support the principal separation sections?",
                why_it_matters="Without an admissible thermo method, detailed energy and separation design should not proceed.",
                dependent_claim_ids=[f"thermo:{thermo_admissibility.selected_route_id}"],
                evidence_targets=["section method family", "required parameters", "key species anchors"],
                unanswered_effect="block",
                priority_score=90.0,
                citations=thermo_admissibility.citations,
                assumptions=thermo_admissibility.assumptions,
            )
        )
    if kinetics_admissibility is not None and kinetics_admissibility.selected_route_id and kinetics_admissibility.selected_route_status != ScientificGateStatus.PASS:
        questions.append(
            InferenceQuestion(
                question_id=f"kinetics_{kinetics_admissibility.selected_route_id}",
                domain="kinetics_requirement",
                prompt="What admissible kinetic basis supports the controlling reaction step for detailed design?",
                why_it_matters="Reactor design should not pretend to be detailed if only screening kinetics exist.",
                dependent_claim_ids=[f"kinetics:{kinetics_admissibility.selected_route_id}"],
                evidence_targets=["rate law", "fit method", "residence-time evidence"],
                unanswered_effect="block",
                priority_score=80.0,
                citations=kinetics_admissibility.citations,
                assumptions=kinetics_admissibility.assumptions,
            )
        )
    if topology_candidates is not None and topology_candidates.selected_route_id and not topology_candidates.screening_balance_allowed:
        questions.append(
            InferenceQuestion(
                question_id=f"topology_{topology_candidates.selected_route_id}",
                domain="topology_consequence",
                prompt="Which admissible unit-train topology closes the selected route without violating the species and reaction basis?",
                why_it_matters="Topology screening can proceed only when route steps map into a coherent unit train.",
                dependent_claim_ids=[f"topology:{topology_candidates.selected_route_id}"],
                evidence_targets=["unit train", "section order", "recycle closure"],
                unanswered_effect="block",
                priority_score=70.0,
                citations=topology_candidates.citations,
                assumptions=topology_candidates.assumptions,
            )
        )
    if economic_coverage is not None and economic_coverage.status != "detailed":
        questions.append(
            InferenceQuestion(
                question_id=f"economics_{economic_coverage.route_id}",
                domain="economics_coverage",
                prompt="Which missing route-derived BOM, service, or market anchors prevent detailed economics?",
                why_it_matters="Detailed finance should not be released while economics remains only screening-grade.",
                dependent_claim_ids=[f"economics:{economic_coverage.route_id}"],
                evidence_targets=["BOM", "service burdens", "site fit", "market anchors"],
                unanswered_effect="downgrade" if economic_coverage.status == "screening" else "block",
                priority_score=60.0,
                citations=economic_coverage.citations,
                assumptions=economic_coverage.assumptions,
            )
        )
    questions.sort(key=lambda item: item.priority_score, reverse=True)
    markdown = "\n".join(
        [
            "| Priority | Domain | Question | Effect |",
            "| --- | --- | --- | --- |",
            *[
                f"| {question.priority_score:.1f} | {question.domain} | {question.prompt} | {question.unanswered_effect} |"
                for question in questions
            ],
        ]
    )
    return InferenceQuestionQueueArtifact(
        active_questions=questions,
        resolved_answers=[],
        markdown=markdown,
        citations=sorted({citation for question in questions for citation in question.citations}),
        assumptions=sorted({assumption for question in questions for assumption in question.assumptions}),
    )


def build_revision_ledger(
    *,
    previous: RevisionLedgerArtifact | None,
    stage_id: str,
    state_revision_counts: dict[str, int],
    route_selection_comparison: RouteSelectionComparisonArtifact | None,
    thermo_admissibility: ThermoAdmissibilityArtifact | None,
    kinetics_admissibility: KineticsAdmissibilityArtifact | None,
) -> RevisionLedgerArtifact:
    tickets: list[RevisionTicket] = []
    active_ticket_ids: list[str] = []
    revision_counts = dict(state_revision_counts)
    if previous is not None:
        tickets.extend(ticket for ticket in previous.tickets if ticket.status != "open")
    selected_row = None
    alternative_exists = False
    if route_selection_comparison is not None:
        selected_row = next((row for row in route_selection_comparison.rows if row.selected), None)
        alternative_exists = any(
            not row.selected and row.scientific_status in {"design_feasible", "screening_feasible"}
            for row in route_selection_comparison.rows
        )
    reopen_reason = ""
    if stage_id == "thermodynamic_feasibility" and thermo_admissibility is not None and thermo_admissibility.selected_route_status == ScientificGateStatus.FAIL:
        reopen_reason = "Selected route failed thermo admissibility after detailed section evaluation."
    if stage_id == "kinetic_feasibility" and kinetics_admissibility is not None and kinetics_admissibility.selected_route_status == ScientificGateStatus.FAIL:
        reopen_reason = "Selected route failed kinetics admissibility after detailed step evaluation."
    if reopen_reason and alternative_exists:
        current_count = revision_counts.get("route_selection", 0)
        limit = _ROUTE_REVISION_LIMITS["route_selection"]
        status = "open" if current_count < limit else "skipped"
        ticket = RevisionTicket(
            ticket_id=f"{stage_id}_route_selection_reopen",
            target_stage_id="route_selection",
            triggered_by_stage_id=stage_id,
            reason=reopen_reason,
            dependent_claim_ids=[f"route_selection:{route_selection_comparison.selected_route_id}"] if route_selection_comparison is not None else [],
            status=status,
            revision_limit=limit,
            citations=route_selection_comparison.citations if route_selection_comparison is not None else [],
            assumptions=route_selection_comparison.assumptions if route_selection_comparison is not None else [],
        )
        tickets.append(ticket)
        if status == "open":
            active_ticket_ids.append(ticket.ticket_id)
    markdown = "\n".join(
        [
            "| Ticket | Target Stage | Triggered By | Status | Reason |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {ticket.ticket_id} | {ticket.target_stage_id} | {ticket.triggered_by_stage_id} | {ticket.status} | {ticket.reason} |"
                for ticket in tickets
            ],
        ]
    )
    return RevisionLedgerArtifact(
        tickets=tickets,
        active_ticket_ids=active_ticket_ids,
        revision_counts_by_stage=revision_counts,
        markdown=markdown,
        citations=sorted({citation for ticket in tickets for citation in ticket.citations}),
        assumptions=sorted({assumption for ticket in tickets for assumption in ticket.assumptions}),
    )
