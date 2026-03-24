from __future__ import annotations

import json

from aoc.llm import GoogleGeminiClient
from aoc.models import (
    ControlLoop,
    ControlPlanArtifact,
    GeographicScope,
    IndianLocationDatum,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    MarketAssessmentArtifact,
    NarrativeArtifact,
    ProcessNarrativeArtifact,
    ProcessTemplate,
    ProductProfileArtifact,
    ProjectBasis,
    PropertyRecord,
    ProvenanceTag,
    ReactionParticipant,
    RouteHazard,
    RouteOption,
    RouteSelectionArtifact,
    RouteSurveyArtifact,
    SiteOption,
    SiteSelectionArtifact,
    SourceDiscoveryArtifact,
    SourceDomain,
    SourceKind,
    SourceRecord,
    ThermoAssessmentArtifact,
)


class BaseReasoningService:
    def discover_sources(self, basis: ProjectBasis) -> SourceDiscoveryArtifact:
        raise NotImplementedError

    def build_product_profile(self, basis: ProjectBasis, sources, corpus: str) -> ProductProfileArtifact:
        raise NotImplementedError

    def build_market_assessment(self, basis: ProjectBasis, sources, corpus: str) -> MarketAssessmentArtifact:
        raise NotImplementedError

    def survey_routes(self, basis: ProjectBasis, sources, corpus: str) -> RouteSurveyArtifact:
        raise NotImplementedError

    def select_route(self, basis: ProjectBasis, route_survey: RouteSurveyArtifact, preferred_route_id: str | None = None) -> RouteSelectionArtifact:
        raise NotImplementedError

    def select_site(self, basis: ProjectBasis, sources, corpus: str) -> SiteSelectionArtifact:
        raise NotImplementedError

    def build_thermo_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ThermoAssessmentArtifact:
        raise NotImplementedError

    def build_kinetic_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> KineticAssessmentArtifact:
        raise NotImplementedError

    def build_process_narrative(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ProcessNarrativeArtifact:
        raise NotImplementedError

    def build_mechanical_design(self, basis: ProjectBasis, route: RouteOption, equipment_json: str) -> NarrativeArtifact:
        raise NotImplementedError

    def build_control_strategy(self, basis: ProjectBasis, equipment_json: str, utilities_json: str) -> ControlPlanArtifact:
        raise NotImplementedError

    def build_safety_environment(self, basis: ProjectBasis, route_json: str, hazop_json: str) -> NarrativeArtifact:
        raise NotImplementedError

    def build_layout_plan(self, basis: ProjectBasis, equipment_json: str, utilities_json: str, site_json: str) -> NarrativeArtifact:
        raise NotImplementedError

    def build_executive_summary(self, basis: ProjectBasis, report_excerpt: str) -> NarrativeArtifact:
        raise NotImplementedError

    def build_conclusion(self, basis: ProjectBasis, financial_json: str) -> NarrativeArtifact:
        raise NotImplementedError


class GeminiReasoningService(BaseReasoningService):
    def __init__(self, model_name: str, temperature: float = 0.2):
        self.llm = GoogleGeminiClient(model_name=model_name)
        self.temperature = temperature
        self.system_instruction = (
            "You are a principal chemical-process design copilot. Use only conservative, engineer-facing outputs. "
            "Return cited content, keep assumptions explicit, and never fabricate unsupported critical numbers. "
            "When India-only mode is active, keep all sites, prices, logistics, labor, utilities, and regulatory evidence grounded in India."
        )

    def _template_hint(self, basis: ProjectBasis) -> str:
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            return (
                "Project template: ethylene_glycol_india. Prioritize industrial ethylene glycol routes, especially ethylene oxide hydration and competing industrial route families. "
                "All market, site, tariff, logistics, labor, and financial evidence must be India-specific and normalized to INR."
            )
        return "Project template: generic_small_molecule."

    def _source_context(self, sources, corpus: str) -> str:
        source_lines = [
            f"- {source.source_id}: {source.title} [{source.source_kind.value}/{source.source_domain.value}/{source.geographic_scope.value}] {source.url_or_doi or source.local_path or 'local'}"
            for source in sources
        ]
        return "Available source ids:\n" + "\n".join(source_lines) + f"\n\nResearch corpus:\n{corpus[:24000]}"

    def _generate(self, schema, prompt: str, *, use_search: bool = False):
        return self.llm.generate_structured(
            prompt,
            schema,
            system_instruction=self.system_instruction,
            use_search=use_search,
            temperature=self.temperature,
        )

    def discover_sources(self, basis: ProjectBasis) -> SourceDiscoveryArtifact:
        india_requirement = "At least 5 sources must be India-grounded." if basis.india_only else ""
        prompt = f"""
Discover 8 to 12 authoritative sources for designing a plant for {basis.target_product}.
{self._template_hint(basis)}
Cover technical chemistry, hazards/SDS, literature/patents, market, Indian site candidates, Indian utility/tariff references, Indian company or government references, and regulatory context.
Every source record must include source_domain, geographic_scope, reference_year when available, country when known, and a short extraction snippet.
Use source_kind values aligned with the schema. {india_requirement}
Return JSON matching the requested schema.
"""
        return self._generate(SourceDiscoveryArtifact, prompt, use_search=True)

    def build_product_profile(self, basis: ProjectBasis, sources, corpus: str) -> ProductProfileArtifact:
        prompt = f"""
Build a cited product profile for {basis.target_product}.
Required properties: Molecular weight, Melting point, Boiling point, Density.
Include uses, industrial relevance, and safety notes tied to plant design.
Only cite source ids from the provided context.
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(ProductProfileArtifact, prompt)

    def build_market_assessment(self, basis: ProjectBasis, sources, corpus: str) -> MarketAssessmentArtifact:
        prompt = f"""
Build a market and capacity justification for {basis.target_product} at {basis.capacity_tpa} TPA in {basis.region}.
If India-only mode is active, use INR and India-grounded evidence only.
Populate india_price_data with cited Indian prices for at least product price, one major raw material, one utility, and labor or operating burden.
Only cite provided source ids.
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(MarketAssessmentArtifact, prompt)

    def survey_routes(self, basis: ProjectBasis, sources, corpus: str) -> RouteSurveyArtifact:
        route_instruction = (
            "Produce at least 3 industrially plausible ethylene glycol routes. Include direct EO hydration, a direct oxidation/hydration style route, and one older or less-preferred industrial route."
            if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA
            else f"Produce at least 3 industrially plausible route options for {basis.target_product}."
        )
        prompt = f"""
{route_instruction}
For each route, include balanced participants, conditions, yield/selectivity, hazards, separations, scale-up notes, and route score.
Only cite provided source ids.
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(RouteSurveyArtifact, prompt)

    def select_route(self, basis: ProjectBasis, route_survey: RouteSurveyArtifact, preferred_route_id: str | None = None) -> RouteSelectionArtifact:
        prompt = f"""
Select one preferred route for {basis.target_product}.
Preferred route id: {preferred_route_id or 'none'}
If the template is ethylene_glycol_india, prefer the route that best balances industrial precedent, selectivity, separation tractability, hazard control, and India feedstock ecosystem.
Route survey JSON:
{route_survey.model_dump_json(indent=2)}
Return the selected route id, justification, and comparison markdown.
"""
        return self._generate(RouteSelectionArtifact, prompt)

    def select_site(self, basis: ProjectBasis, sources, corpus: str) -> SiteSelectionArtifact:
        prompt = f"""
Select the best site region for {basis.target_product} in India.
Use only India site candidates. Consider feedstock access, ports, utilities, industrial ecosystem, and regulatory/logistics fit.
Populate india_location_data with cited Indian site/location evidence.
Only cite provided source ids.
{self._template_hint(basis)}
Preferred states: {', '.join(filter(None, [basis.target_state])) or 'not specified'}
{self._source_context(sources, corpus)}
"""
        return self._generate(SiteSelectionArtifact, prompt)

    def build_thermo_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ThermoAssessmentArtifact:
        prompt = f"""
Build a thermodynamic feasibility assessment for the selected route for {basis.target_product}.
Route JSON:
{route.model_dump_json(indent=2)}
Use only provided sources. If exact values are missing, label assumptions explicitly and keep them conservative.
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(ThermoAssessmentArtifact, prompt)

    def build_kinetic_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> KineticAssessmentArtifact:
        prompt = f"""
Build a kinetics assessment for the selected route for {basis.target_product}.
Return activation energy, pre-exponential factor, apparent order, design residence time, and markdown.
Use only provided source ids and label any estimated basis explicitly.
Route JSON:
{route.model_dump_json(indent=2)}
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(KineticAssessmentArtifact, prompt)

    def build_process_narrative(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ProcessNarrativeArtifact:
        prompt = f"""
Build a block-flow narrative for {basis.target_product}.
Return Mermaid BFD text and markdown body. The process narrative should describe the material journey, recycle/purge logic, and major purification blocks.
Only use provided source ids.
Route JSON:
{route.model_dump_json(indent=2)}
{self._template_hint(basis)}
{self._source_context(sources, corpus)}
"""
        return self._generate(ProcessNarrativeArtifact, prompt)

    def build_mechanical_design(self, basis: ProjectBasis, route: RouteOption, equipment_json: str) -> NarrativeArtifact:
        prompt = f"""
Write the mechanical design and material-of-construction section for {basis.target_product}.
Use the equipment JSON and route context below. Focus on shell thickness basis, corrosion allowance logic, vessel internals, and MoC decisions at conceptual-design depth.
Equipment JSON:
{equipment_json}
Route JSON:
{route.model_dump_json(indent=2)}
"""
        return self._generate(NarrativeArtifact, prompt)

    def build_control_strategy(self, basis: ProjectBasis, equipment_json: str, utilities_json: str) -> ControlPlanArtifact:
        prompt = f"""
Write the instrumentation and process-control strategy for {basis.target_product}.
Return at least 5 control loops and supporting markdown tied to the actual equipment and utilities below.
Equipment JSON:
{equipment_json}
Utilities JSON:
{utilities_json}
"""
        return self._generate(ControlPlanArtifact, prompt)

    def build_safety_environment(self, basis: ProjectBasis, route_json: str, hazop_json: str) -> NarrativeArtifact:
        prompt = f"""
Write the safety, health, environment, and waste management chapter for {basis.target_product}.
Tie the narrative to the selected route and the HAZOP nodes below. Keep it specific to the actual plant.
Route JSON:
{route_json}
HAZOP JSON:
{hazop_json}
"""
        return self._generate(NarrativeArtifact, prompt)

    def build_layout_plan(self, basis: ProjectBasis, equipment_json: str, utilities_json: str, site_json: str) -> NarrativeArtifact:
        prompt = f"""
Write the project and plant layout chapter for {basis.target_product}.
Use the equipment, utility, and selected Indian site context below. Address access, piping economy, maintenance, emergency response, and future expansion.
Equipment JSON:
{equipment_json}
Utilities JSON:
{utilities_json}
Site JSON:
{site_json}
"""
        return self._generate(NarrativeArtifact, prompt)

    def build_executive_summary(self, basis: ProjectBasis, report_excerpt: str) -> NarrativeArtifact:
        prompt = f"""
Write an executive summary for a plant-design report on {basis.target_product}.
Summarize route, site, process, key design units, India-specific economics, and final feasibility view.
Use the following report excerpt:
{report_excerpt[:16000]}
Return a NarrativeArtifact.
"""
        return self._generate(NarrativeArtifact, prompt)

    def build_conclusion(self, basis: ProjectBasis, financial_json: str) -> NarrativeArtifact:
        prompt = f"""
Write a concise conclusion for the {basis.target_product} plant-design report.
Financial JSON:
{financial_json}
Return a NarrativeArtifact.
"""
        return self._generate(NarrativeArtifact, prompt)


class MockReasoningService(BaseReasoningService):
    def _citations(self, sources, count: int = 3) -> list[str]:
        return [source.source_id for source in sources[:count]] or ["seed_source_1"]

    def discover_sources(self, basis: ProjectBasis) -> SourceDiscoveryArtifact:
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            sources = [
                SourceRecord(
                    source_id="eg_handbook",
                    source_kind=SourceKind.HANDBOOK,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Ethylene glycol handbook properties",
                    citation_text="Compiled thermophysical property note for ethylene glycol.",
                    url_or_doi="https://example.com/eg/properties",
                    extraction_snippet="Ethylene glycol molecular weight, boiling point, density, and handling note.",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2024,
                ),
                SourceRecord(
                    source_id="eg_kinetics",
                    source_kind=SourceKind.LITERATURE,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Ethylene oxide hydration kinetics note",
                    citation_text="Seed kinetics note for ethylene oxide hydration to ethylene glycol.",
                    url_or_doi="https://example.com/eg/kinetics",
                    extraction_snippet="Hydration kinetics, heat of reaction, and route comparison note.",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2022,
                ),
                SourceRecord(
                    source_id="eg_market_india",
                    source_kind=SourceKind.MARKET,
                    source_domain=SourceDomain.ECONOMICS,
                    title="India MEG market note",
                    citation_text="Seed India market note for monoethylene glycol.",
                    url_or_doi="https://example.com/india/meg-market",
                    extraction_snippet="India demand, pricing, and downstream polyester/resins context.",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
                SourceRecord(
                    source_id="eg_sites_india",
                    source_kind=SourceKind.COMPANY_REPORT,
                    source_domain=SourceDomain.SITE,
                    title="India petrochemical cluster siting note",
                    citation_text="Seed cluster comparison across Gujarat, Maharashtra, and Odisha.",
                    url_or_doi="https://example.com/india/sites",
                    extraction_snippet="Dahej, Jamnagar, and Paradip compared on logistics, feedstock, and utilities.",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                ),
                SourceRecord(
                    source_id="eg_utilities_gujarat",
                    source_kind=SourceKind.UTILITY,
                    source_domain=SourceDomain.UTILITIES,
                    title="India utility tariff note",
                    citation_text="Seed utility tariff note for industrial Gujarat service.",
                    url_or_doi="https://example.com/india/utilities",
                    extraction_snippet="Industrial steam, power, and cooling water tariff placeholders normalized to 2025 INR.",
                    geographic_scope=GeographicScope.STATE,
                    geographic_label="Gujarat",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
                SourceRecord(
                    source_id="eg_safety",
                    source_kind=SourceKind.SDS,
                    source_domain=SourceDomain.SAFETY,
                    title="Ethylene oxide and ethylene glycol SDS note",
                    citation_text="Seed SDS summary for EO and EG handling hazards.",
                    url_or_doi="https://example.com/eg/safety",
                    extraction_snippet="EO flammability, toxicity, and EG handling controls.",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2024,
                ),
            ]
            return SourceDiscoveryArtifact(
                sources=sources,
                summary="Seed research bundle for India-mode ethylene glycol including technical, safety, market, site, and utility references.",
            )

        product_slug = basis.target_product.lower().replace(" ", "-")
        sources = [
            SourceRecord(
                source_id="seed_source_1",
                source_kind=SourceKind.HANDBOOK,
                source_domain=SourceDomain.TECHNICAL,
                title=f"{basis.target_product} property note",
                citation_text=f"Seed property note for {basis.target_product}",
                url_or_doi=f"https://example.com/{product_slug}/properties",
                extraction_snippet="Compiled product property note used for deterministic test runs.",
                geographic_scope=GeographicScope.GLOBAL,
                reference_year=2024,
            ),
            SourceRecord(
                source_id="seed_source_2",
                source_kind=SourceKind.LITERATURE,
                source_domain=SourceDomain.TECHNICAL,
                title=f"{basis.target_product} route note",
                citation_text=f"Seed route note for {basis.target_product}",
                url_or_doi=f"https://example.com/{product_slug}/routes",
                extraction_snippet="Route selection note with yields and operating conditions.",
                geographic_scope=GeographicScope.GLOBAL,
                reference_year=2024,
            ),
            SourceRecord(
                source_id="seed_source_3",
                source_kind=SourceKind.SDS,
                source_domain=SourceDomain.SAFETY,
                title=f"{basis.target_product} safety note",
                citation_text=f"Seed safety note for {basis.target_product}",
                url_or_doi=f"https://example.com/{product_slug}/safety",
                extraction_snippet="Safety note with exposure and hazard summary.",
                geographic_scope=GeographicScope.GLOBAL,
                reference_year=2024,
            ),
            SourceRecord(
                source_id="seed_source_4",
                source_kind=SourceKind.MARKET,
                source_domain=SourceDomain.MARKET,
                title=f"{basis.target_product} market note",
                citation_text=f"Seed market note for {basis.target_product}",
                url_or_doi=f"https://example.com/{product_slug}/market",
                extraction_snippet="Market note with plausible specialty chemical pricing.",
                geographic_scope=GeographicScope.INDIA if basis.india_only else GeographicScope.GLOBAL,
                geographic_label="India" if basis.india_only else "global",
                country="India" if basis.india_only else None,
                reference_year=2025 if basis.india_only else 2024,
                normalization_year=2025 if basis.india_only else None,
            ),
        ]
        return SourceDiscoveryArtifact(sources=sources, summary=f"Seed research bundle for {basis.target_product}.")

    def build_product_profile(self, basis: ProjectBasis, sources, corpus: str) -> ProductProfileArtifact:
        citations = self._citations(sources, 3)
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            properties = [
                PropertyRecord(name="Molecular weight", value="62.07", units="g/mol", supporting_sources=citations, citations=citations),
                PropertyRecord(name="Melting point", value="-12.9", units="C", supporting_sources=citations, citations=citations),
                PropertyRecord(name="Boiling point", value="197.3", units="C", supporting_sources=citations, citations=citations),
                PropertyRecord(name="Density", value="1.113", units="g/cm3", supporting_sources=citations, citations=citations),
                PropertyRecord(name="Water solubility", value="Miscible", units="-", supporting_sources=citations, citations=citations, method=ProvenanceTag.SOURCED),
            ]
            uses = ["Polyester and PET chain", "Antifreeze and coolants", "Resins, fibers, and solvents"]
            safety = [
                "Ethylene oxide feed handling dominates the process hazard envelope because of flammability, toxicity, and polymerization risk.",
                "Ethylene glycol product handling is materially easier, but hot glycol service still requires burn and leak control.",
            ]
            markdown = (
                "Ethylene glycol is a high-volume petrochemical intermediate with deep downstream demand in polyester, PET resin, coolants, and solvent applications. "
                "For a 200000 TPA India project, the product profile must be tied directly to feedstock integration, high-water hydration chemistry, and energy-intensive purification rather than written as a generic chemistry summary.\n\n"
                "The design basis therefore uses cited thermophysical properties, continuous operation, and India-specific market relevance as direct inputs to route, site, and economics decisions."
            )
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=properties,
                uses=uses,
                industrial_relevance="Bulk petrochemical demand and India polyester integration justify a large continuous plant basis.",
                safety_notes=safety,
                markdown=markdown,
                citations=citations,
                assumptions=["Mock EG product profile uses seeded but realistic property values."],
            )

        properties = [
            PropertyRecord(name="Molecular weight", value="150.00", units="g/mol", supporting_sources=citations, citations=citations),
            PropertyRecord(name="Melting point", value="60", units="C", supporting_sources=citations, citations=citations),
            PropertyRecord(name="Boiling point", value="240", units="C", supporting_sources=citations, citations=citations),
            PropertyRecord(name="Density", value="1.10", units="g/cm3", supporting_sources=citations, citations=citations),
        ]
        return ProductProfileArtifact(
            product_name=basis.target_product,
            properties=properties,
            uses=["Specialty chemical intermediate", "Downstream formulation feedstock"],
            industrial_relevance="Specialty-intermediate demand favors a moderate-scale, citation-driven plant-design approach.",
            safety_notes=["Use conservative aromatic-organic handling controls."],
            markdown=f"{basis.target_product} is treated in v1 as an organic small-molecule specialty chemical with commercial value as a downstream intermediate.",
            citations=citations,
            assumptions=["Mock product profile uses seeded property values for deterministic testing."],
        )

    def build_market_assessment(self, basis: ProjectBasis, sources, corpus: str) -> MarketAssessmentArtifact:
        citations = self._citations(sources, 3)
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            price_data = [
                IndianPriceDatum(datum_id="meg_product_price", category="product", item_name="Monoethylene glycol", region="India", units="INR/kg", value_inr=63.0, reference_year=2025, normalization_year=2025, citations=[citations[2] if len(citations) > 2 else citations[0]]),
                IndianPriceDatum(datum_id="eo_feed_price", category="raw_material", item_name="Ethylene oxide", region="India", units="INR/kg", value_inr=62.0, reference_year=2025, normalization_year=2025, citations=[citations[2] if len(citations) > 2 else citations[0]]),
                IndianPriceDatum(datum_id="power_tariff", category="utility", item_name="Electricity", region="Gujarat", units="INR/kWh", value_inr=8.5, reference_year=2025, normalization_year=2025, citations=[citations[2] if len(citations) > 2 else citations[0]]),
                IndianPriceDatum(datum_id="labor_burden", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=650000.0, reference_year=2025, normalization_year=2025, citations=[citations[2] if len(citations) > 2 else citations[0]]),
            ]
            markdown = (
                "The 200000 TPA basis is framed as a large continuous petrochemical train aligned with India polyester and resin demand rather than a niche batch-chemical facility. "
                "The market case depends on large throughput, stable EO integration, and India-based logistics and tariff assumptions, all normalized in INR."
            )
            return MarketAssessmentArtifact(
                estimated_price_per_kg=63.0,
                price_range="INR 58-70 per kg in an India commodity-petrochemical window.",
                competitor_notes=["Domestic demand is linked to polyester and PET chains.", "Feedstock integration and logistics materially influence margin resilience."],
                demand_drivers=["Polyester fiber", "PET resin", "Coolants and industrial formulations"],
                capacity_rationale="200000 TPA is large enough to justify continuous purification, utility integration, and capital recovery for an EO-based route.",
                india_price_data=price_data,
                markdown=markdown,
                citations=citations,
                assumptions=["Mock India market assessment uses seeded price points normalized to 2025 INR."],
            )

        return MarketAssessmentArtifact(
            estimated_price_per_kg=320.0,
            price_range="INR 280-360 per kg in a specialty-intermediate market window.",
            competitor_notes=["Fragmented specialty producers with import competition."],
            demand_drivers=["Dyes and pigments", "Pharmaceutical intermediate demand", "Custom synthesis demand"],
            capacity_rationale=f"{basis.capacity_tpa:.0f} TPA balances manageable capex with enough throughput for meaningful cost recovery.",
            markdown="Seeded market assessment for the generic template.",
            citations=citations,
            assumptions=["Mock market assessment uses seeded pricing rather than live market retrieval."],
        )

    def survey_routes(self, basis: ProjectBasis, sources, corpus: str) -> RouteSurveyArtifact:
        citations = self._citations(sources, 4)
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            routes = [
                RouteOption(
                    route_id="eo_hydration",
                    name="Ethylene oxide hydration",
                    reaction_equation="C2H4O + H2O -> C2H6O2",
                    participants=[
                        ReactionParticipant(name="Ethylene oxide", formula="C2H4O", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.05, phase="liquid"),
                        ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                        ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1.0, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
                    ],
                    catalysts=[],
                    operating_temperature_c=190.0,
                    operating_pressure_bar=14.0,
                    residence_time_hr=0.75,
                    yield_fraction=0.92,
                    selectivity_fraction=0.93,
                    byproducts=["Diethylene glycol", "Triethylene glycol"],
                    separations=["EO flash", "Water removal", "Vacuum distillation", "Heavy glycol split"],
                    scale_up_notes="Industrial precedent is strong; energy demand is dominated by dehydration and purification.",
                    hazards=[RouteHazard(severity="high", description="Ethylene oxide flammability and toxicity", safeguard="Inerted closed handling and relief design")],
                    route_score=9.5,
                    rationale="Best industrial maturity and strongest fit for a high-capacity India plant.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="omega_catalytic",
                    name="OMEGA catalytic route via ethylene carbonate",
                    reaction_equation="C2H4 + 0.5 O2 + H2O -> C2H6O2",
                    participants=[
                        ReactionParticipant(name="Ethylene", formula="C2H4", coefficient=1.0, role="reactant", molecular_weight_g_mol=28.05, phase="gas"),
                        ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.00, phase="gas"),
                        ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                        ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1.0, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
                    ],
                    catalysts=["CO2 catalytic loop", "Carbonate hydrolysis catalyst"],
                    operating_temperature_c=240.0,
                    operating_pressure_bar=18.0,
                    residence_time_hr=1.0,
                    yield_fraction=0.96,
                    selectivity_fraction=0.99,
                    byproducts=["Trace heavy glycols"],
                    separations=["Carbonate loop cleanup", "Hydrolysis", "Low-water purification"],
                    scale_up_notes="Modern high-selectivity route with a far lower dehydration burden than thermal hydration.",
                    hazards=[RouteHazard(severity="moderate", description="Catalytic loop and CO2 handling complexity", safeguard="Closed-loop catalyst management and pressure control")],
                    route_score=8.9,
                    rationale="State-of-the-art route with strong selectivity and materially lower steam intensity.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="ethylene_chlorohydrin",
                    name="Ethylene chlorohydrin hydrolysis",
                    reaction_equation="C2H5ClO + NaOH -> C2H6O2 + NaCl",
                    participants=[
                        ReactionParticipant(name="Ethylene chlorohydrin", formula="C2H5ClO", coefficient=1.0, role="reactant", molecular_weight_g_mol=80.51, phase="liquid"),
                        ReactionParticipant(name="Sodium hydroxide", formula="NaOH", coefficient=1.0, role="reactant", molecular_weight_g_mol=40.00, phase="liquid"),
                        ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1.0, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
                        ReactionParticipant(name="Sodium chloride", formula="NaCl", coefficient=1.0, role="byproduct", molecular_weight_g_mol=58.44, phase="solid"),
                    ],
                    catalysts=[],
                    operating_temperature_c=95.0,
                    operating_pressure_bar=3.0,
                    residence_time_hr=1.8,
                    yield_fraction=0.75,
                    selectivity_fraction=0.82,
                    byproducts=["Saline waste", "chlorinated residues"],
                    separations=["Salt removal", "Water removal", "Distillation"],
                    scale_up_notes="Older route with corrosive service and undesirable waste burden.",
                    hazards=[RouteHazard(severity="moderate", description="Caustic and chlorinated service", safeguard="Corrosion control and brine management")],
                    route_score=5.9,
                    rationale="Inferior sustainability and waste profile versus modern EO hydration.",
                    citations=citations,
                ),
            ]
            markdown = (
                "The route survey compares industrial EG pathways on maturity, selectivity, safety, utility intensity, and India feedstock fit. "
                "Ethylene oxide hydration remains the strongest basis because it is the most defensible large-scale route for a 200000 TPA feasibility-style home paper."
            )
            return RouteSurveyArtifact(routes=routes, markdown=markdown, citations=citations, assumptions=["Mock EG route survey uses seeded industrial route families."])

        routes = [
            RouteOption(
                route_id="generic_route_1",
                name="Generic primary route",
                reaction_equation="A + B -> P",
                participants=[
                    ReactionParticipant(name="A", formula="CH4", coefficient=1.0, role="reactant", molecular_weight_g_mol=16.0),
                    ReactionParticipant(name="B", formula="O2", coefficient=1.0, role="reactant", molecular_weight_g_mol=32.0),
                    ReactionParticipant(name="P", formula="CH4O2", coefficient=1.0, role="product", molecular_weight_g_mol=48.0),
                ],
                catalysts=["Generic catalyst"],
                operating_temperature_c=90.0,
                operating_pressure_bar=2.0,
                residence_time_hr=2.0,
                yield_fraction=0.85,
                selectivity_fraction=0.88,
                scale_up_notes="Generic seeded route.",
                route_score=8.0,
                rationale="Generic highest scoring route.",
                citations=citations,
            )
        ]
        return RouteSurveyArtifact(routes=routes, markdown="Seeded generic route survey.", citations=citations, assumptions=["Generic route survey fallback."])

    def select_route(self, basis: ProjectBasis, route_survey: RouteSurveyArtifact, preferred_route_id: str | None = None) -> RouteSelectionArtifact:
        routes = {route.route_id: route for route in route_survey.routes}
        chosen = routes.get(preferred_route_id) if preferred_route_id else None
        if not chosen:
            chosen = max(route_survey.routes, key=lambda route: route.route_score)
        comparison = "| Route | Score | Yield | Selectivity | Key risk |\n| --- | --- | --- | --- | --- |\n" + "\n".join(
            f"| {route.name} | {route.route_score:.1f} | {route.yield_fraction:.2f} | {route.selectivity_fraction:.2f} | {route.hazards[0].description if route.hazards else 'Manageable'} |"
            for route in route_survey.routes
        )
        justification = (
            "Ethylene oxide hydration is selected because it combines the strongest industrial precedent, manageable purification logic, and the clearest India-relevant petrochemical scale-up case."
            if chosen.route_id == "eo_hydration"
            else f"{chosen.name} is selected because it offers the strongest route score and the cleanest downstream sequence for a conceptual study."
        )
        return RouteSelectionArtifact(
            selected_route_id=chosen.route_id,
            justification=justification,
            comparison_markdown=comparison,
            citations=route_survey.citations,
            assumptions=route_survey.assumptions,
        )

    def select_site(self, basis: ProjectBasis, sources, corpus: str) -> SiteSelectionArtifact:
        citations = self._citations(sources, 4)
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            candidates = [
                SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="Strong petrochemical ecosystem, port access, and utility backbone.", citations=citations),
                SiteOption(name="Jamnagar", state="Gujarat", raw_material_score=9, logistics_score=8, utility_score=8, business_score=8, total_score=33, rationale="Refining and petrochemical integration advantages.", citations=citations),
                SiteOption(name="Paradip", state="Odisha", raw_material_score=7, logistics_score=8, utility_score=7, business_score=7, total_score=29, rationale="Port access and eastern India logistics upside, but weaker integration than Gujarat.", citations=citations),
            ]
            location_data = [
                IndianLocationDatum(location_id="loc_dahej", site_name="Dahej", state="Gujarat", port_access="Dahej/Hazira marine access", utility_note="Mature industrial utility ecosystem and steam/power availability.", logistics_note="Strong chemical-cluster logistics and export connectivity.", regulatory_note="Established chemical-zone operating context with mature compliance ecosystem.", reference_year=2025, citations=citations),
                IndianLocationDatum(location_id="loc_jamnagar", site_name="Jamnagar", state="Gujarat", port_access="West coast port connectivity", utility_note="Integrated refining-petrochemical utility environment.", logistics_note="Good feedstock and product dispatch linkages.", regulatory_note="Industrial cluster advantage but site-specific compliance envelope still required.", reference_year=2025, citations=citations),
                IndianLocationDatum(location_id="loc_paradip", site_name="Paradip", state="Odisha", port_access="Deep-water east-coast port access", utility_note="Industrial utility support available with project-specific development.", logistics_note="Useful for eastern dispatch but less dense chemical services.", regulatory_note="Would need stronger project-specific ecosystem build-out.", reference_year=2025, citations=citations),
            ]
            markdown = "Dahej, Gujarat is selected because it best combines petrochemical integration, port logistics, utilities, industrial services, and a defendable India cost basis for a 200000 TPA EG plant."
            return SiteSelectionArtifact(
                candidates=candidates,
                selected_site="Dahej",
                india_location_data=location_data,
                markdown=markdown,
                citations=citations,
                assumptions=["Mock India site selection uses seeded cluster scoring rather than full geospatial analysis."],
            )

        candidates = [
            SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="Strong chemical ecosystem and port access.", citations=citations),
            SiteOption(name="Navi Mumbai", state="Maharashtra", raw_material_score=7, logistics_score=8, utility_score=8, business_score=6, total_score=29, rationale="Good market access but tighter land and compliance envelope.", citations=citations),
        ]
        return SiteSelectionArtifact(candidates=candidates, selected_site="Dahej", markdown="Dahej is selected in the seeded run because the cluster offers strong logistics and utilities.", citations=citations, assumptions=["Mock site selection uses seed scoring rather than geospatial optimization."])

    def build_thermo_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ThermoAssessmentArtifact:
        citations = self._citations(sources, 3)
        if route.route_id == "eo_hydration":
            return ThermoAssessmentArtifact(
                feasible=True,
                estimated_reaction_enthalpy_kj_per_mol=-90.4,
                estimated_gibbs_kj_per_mol=-31.5,
                equilibrium_comment="EO hydration is thermodynamically favorable and exothermic, so heat removal and side-product control matter more than equilibrium limitation.",
                markdown="The selected EO hydration route is thermodynamically favorable under the chosen liquid-phase operating window. Negative Gibbs free energy supports conversion, while the exothermic enthalpy demands controlled heat removal to protect selectivity and containment.",
                citations=citations,
                assumptions=["Mock EG thermodynamic values are seeded from a realistic industrial range for deterministic execution."],
            )
        return ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-68.0,
            estimated_gibbs_kj_per_mol=-24.0,
            equilibrium_comment="The selected route is thermodynamically favorable under the proposed liquid-phase operating conditions.",
            markdown="The selected reaction is treated as thermodynamically favorable, with a negative Gibbs free energy and exothermic heat release that supports conversion but requires controlled heat removal.",
            citations=citations,
            assumptions=["Mock thermodynamic values are seeded for deterministic test runs and must be replaced by cited values in production use."],
        )

    def build_kinetic_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> KineticAssessmentArtifact:
        citations = self._citations(sources, 3)
        if route.route_id == "eo_hydration":
            return KineticAssessmentArtifact(
                feasible=True,
                activation_energy_kj_per_mol=73.0,
                pre_exponential_factor=4.8e8,
                apparent_order=1.0,
                design_residence_time_hr=route.residence_time_hr,
                markdown="The seeded kinetics basis supports a short, continuous hydrator residence time and reinforces the need for high water dilution to preserve MEG selectivity over heavier glycols.",
                citations=citations,
                assumptions=["Mock EG kinetic parameters are seeded for workflow verification and should be replaced by cited literature in live use."],
            )
        return KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=58.0,
            pre_exponential_factor=1.2e7,
            apparent_order=1.0,
            design_residence_time_hr=route.residence_time_hr,
            markdown="The seeded kinetics package supports a practical residence-time basis for preliminary equipment sizing.",
            citations=citations,
            assumptions=["Mock kinetic parameters are seeded values for workflow verification."],
        )

    def build_process_narrative(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ProcessNarrativeArtifact:
        citations = self._citations(sources, 3)
        if route.route_id == "eo_hydration":
            mermaid = "\n".join(
                [
                    "flowchart LR",
                    "  A[EO Storage] --> B[Feed Conditioning]",
                    "  W[Process Water] --> B",
                    "  B --> C[Hydrator R-102]",
                    "  C --> D[EO Flash V-101]",
                    "  D --> E[Water Removal / D-101]",
                    "  E --> F[MEG Finishing]",
                    "  E --> G[Heavy Glycol Split]",
                    "  F --> H[MEG Storage]",
                    "  D --> I[EO Purge / Recovery]",
                    "  E --> J[Recovered Water Recycle]",
                ]
            )
            markdown = (
                "Ethylene oxide and high-excess process water are conditioned before entering the hydrator, where the main MEG formation reaction is carried out under controlled exothermic conditions. "
                "The reactor effluent first enters EO flash service to remove light material and stabilize downstream purification. "
                "Water is then removed and recycled, while vacuum distillation and finishing steps recover on-spec monoethylene glycol and separate heavy glycols."
            )
            return ProcessNarrativeArtifact(bfd_mermaid=mermaid, markdown=markdown, citations=citations, assumptions=["Seeded EG BFD reflects a conventional industrial hydration and purification path."])

        mermaid = "\n".join(
            [
                "flowchart LR",
                "  A[Feed Storage] --> B[Feed Preparation]",
                "  B --> C[Reactor]",
                "  C --> D[Separation]",
                "  D --> E[Purification]",
                "  E --> F[Product Storage]",
            ]
        )
        return ProcessNarrativeArtifact(
            bfd_mermaid=mermaid,
            markdown="Raw materials are metered, reacted, and purified through a simple seeded sequence.",
            citations=citations,
            assumptions=["Seeded BFD used for deterministic stage execution."],
        )

    def build_mechanical_design(self, basis: ProjectBasis, route: RouteOption, equipment_json: str) -> NarrativeArtifact:
        if route.route_id == "eo_hydration":
            markdown = (
                "The mechanical design basis uses pressure-rated welded vessels for EO-containing sections, conservative corrosion allowance in hot aqueous glycol service, and SS316L as the default wetted metallurgy for reactor, flash, and column sections. "
                "The distillation system is treated as vacuum-capable service with nozzle and flange ratings selected against the hot glycol envelope. Storage service is relaxed to SS304 where chloride-rich or EO-containing service is absent."
            )
            assumptions = ["Mechanical design remains preliminary and must be converted into code calculations during detailed design."]
        else:
            markdown = "The mechanical design basis assumes welded process vessels with corrosion allowance and conservative nozzle sizing."
            assumptions = ["Mechanical design remains preliminary and factor-based pending code calculations."]
        return NarrativeArtifact(
            artifact_id="mechanical_design",
            title="Mechanical Design and Materials of Construction",
            markdown=markdown,
            summary="Mechanical design ties vessel integrity, corrosion control, and maintainability back to process hazards and thermal duty.",
            citations=route.citations,
            assumptions=assumptions,
        )

    def build_control_strategy(self, basis: ProjectBasis, equipment_json: str, utilities_json: str) -> ControlPlanArtifact:
        loops = [
            ControlLoop(control_id="TIC-102", controlled_variable="Hydrator temperature", manipulated_variable="Jacket cooling flow", sensor="RTD", actuator="Control valve", notes="Prevents selectivity loss and thermal upset."),
            ControlLoop(control_id="PIC-102", controlled_variable="Hydrator pressure", manipulated_variable="Back-pressure valve", sensor="Pressure transmitter", actuator="Control valve", notes="Maintains liquid-phase operating window."),
            ControlLoop(control_id="FIC-101", controlled_variable="EO feed rate", manipulated_variable="EO feed pump speed", sensor="Mass flow meter", actuator="VFD", notes="Maintains conversion basis and feed ratio."),
            ControlLoop(control_id="FIC-102", controlled_variable="Water-to-EO ratio", manipulated_variable="Process-water control valve", sensor="Flow transmitter", actuator="Control valve", notes="Preserves high dilution for MEG selectivity."),
            ControlLoop(control_id="LIC-101", controlled_variable="Flash drum level", manipulated_variable="Bottoms withdrawal", sensor="Level transmitter", actuator="Control valve", notes="Protects downstream purification from carryover."),
            ControlLoop(control_id="PIC-201", controlled_variable="Column pressure", manipulated_variable="Vacuum system duty", sensor="Pressure transmitter", actuator="Vacuum control valve", notes="Maintains gentle glycol purification conditions."),
        ]
        markdown = "The control philosophy focuses on EO feed containment, hydrator temperature-pressure stability, water dilution ratio, flash level control, and vacuum-column stability."
        return ControlPlanArtifact(control_loops=loops, markdown=markdown, citations=[], assumptions=["Control strategy is preliminary and should be refined during FEED."])

    def build_safety_environment(self, basis: ProjectBasis, route_json: str, hazop_json: str) -> NarrativeArtifact:
        return NarrativeArtifact(
            artifact_id="safety_environment",
            title="Safety, Health, Environment, and Waste Management",
            markdown="The SHE basis prioritizes EO containment, inerting, high-integrity relief and vent routing, hot glycol burn protection, wastewater segregation, and recovery of water and heavy glycol side streams before discharge or disposal. Vent, spill, and emergency response provisions are tied directly to the hydrator, flash, and column sections rather than presented as generic safety text.",
            summary="SHE narrative ties process hazards to operating controls, emergency response, and waste handling.",
            citations=[],
            assumptions=["Waste treatment remains conceptual until detailed composition data is available."],
        )

    def build_layout_plan(self, basis: ProjectBasis, equipment_json: str, utilities_json: str, site_json: str) -> NarrativeArtifact:
        return NarrativeArtifact(
            artifact_id="layout_plan",
            title="Layout",
            markdown="EO and feed storage are placed at the controlled receiving edge of the site, the hydrator-flash-distillation train is grouped for short high-integrity pipe runs, the utility block is kept on the service side of the process area, and MEG storage is located toward dispatch. The control room remains outside the primary hazard envelope, while maintenance and firefighting access are preserved around the reactor and vacuum-column zone.",
            summary="Layout is driven by piping economy, operability, hazard segregation, and emergency access.",
            citations=[],
            assumptions=["Layout remains conceptual and is not a plot-plan drawing."],
        )

    def build_executive_summary(self, basis: ProjectBasis, report_excerpt: str) -> NarrativeArtifact:
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            markdown = (
                f"## Executive Summary\n\nThis report develops an India-mode conceptual plant design for {basis.target_product} at {basis.capacity_tpa:.0f} TPA. "
                "The selected basis uses ethylene oxide hydration, India-specific siting and tariff assumptions, traceable calculations for balances and major equipment, and approval gates around route, design basis, reactor/column basis, HAZOP, India economics, and final release."
            )
            assumptions = ["Executive summary compiled from deterministic workflow artifacts."]
        else:
            markdown = f"## Executive Summary\n\nThis v1 report develops a cited conceptual plant-design package for {basis.target_product} at {basis.capacity_tpa:.0f} TPA."
            assumptions = ["Executive summary compiled from seeded workflow artifacts."]
        return NarrativeArtifact(
            artifact_id="executive_summary",
            title="Executive Summary",
            markdown=markdown,
            summary="Executive summary compiled from deterministic report state.",
            citations=[],
            assumptions=assumptions,
        )

    def build_conclusion(self, basis: ProjectBasis, financial_json: str) -> NarrativeArtifact:
        data = json.loads(financial_json)
        if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
            markdown = (
                f"The India-mode conceptual study indicates that {basis.target_product} production can be framed credibly around the selected EO hydration route, Dahej-style cluster siting logic, and a high-capacity continuous plant basis. "
                f"With headline payback of {data['payback_years']:.2f} years and IRR of {data['irr']:.2f}%, the current feasibility case supports progression to deeper engineering, provided live-cited tariffs, market references, and detailed mechanical code design are carried into the next phase."
            )
        else:
            markdown = (
                f"The conceptual study indicates that {basis.target_product} can be framed as a buildable project under the selected route and site assumptions. "
                f"With headline payback of {data['payback_years']:.2f} years and IRR of {data['irr']:.2f}%, the seeded economics support progression to a more detailed package."
            )
        return NarrativeArtifact(
            artifact_id="conclusion",
            title="Conclusion",
            markdown=markdown,
            summary="Conclusion closes on route, economics, and next-step maturity.",
            citations=[],
            assumptions=["Conclusion reflects preliminary feasibility-level economics and design assumptions."],
        )


def build_reasoning_service(model_settings) -> BaseReasoningService:
    if model_settings.backend == "mock":
        return MockReasoningService()
    return GeminiReasoningService(model_name=model_settings.model_name, temperature=model_settings.temperature)
