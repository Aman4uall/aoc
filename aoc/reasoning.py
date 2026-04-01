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

    def _product_key(self, basis: ProjectBasis) -> str:
        return basis.target_product.strip().lower().replace(" ", "_")

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
        if basis.india_only:
            sources.extend(
                [
                    SourceRecord(
                        source_id="seed_source_5",
                        source_kind=SourceKind.COMPANY_REPORT,
                        source_domain=SourceDomain.SITE,
                        title=f"{basis.target_product} India site note",
                        citation_text=f"Seed India site note for {basis.target_product}",
                        url_or_doi=f"https://example.com/{product_slug}/india-site",
                        extraction_snippet="India site comparison note with Gujarat-focused industrial clusters.",
                        geographic_scope=GeographicScope.INDIA,
                        geographic_label="India",
                        country="India",
                        reference_year=2025,
                    ),
                    SourceRecord(
                        source_id="seed_source_6",
                        source_kind=SourceKind.UTILITY,
                        source_domain=SourceDomain.UTILITIES,
                        title=f"{basis.target_product} India utility note",
                        citation_text=f"Seed India utility note for {basis.target_product}",
                        url_or_doi=f"https://example.com/{product_slug}/india-utilities",
                        extraction_snippet="India power, steam, and industrial utility basis note normalized to 2025 INR.",
                        geographic_scope=GeographicScope.INDIA,
                        geographic_label="India",
                        country="India",
                        reference_year=2025,
                        normalization_year=2025,
                    ),
                ]
            )
        return SourceDiscoveryArtifact(sources=sources, summary=f"Seed research bundle for {basis.target_product}.")

    def build_product_profile(self, basis: ProjectBasis, sources, corpus: str) -> ProductProfileArtifact:
        citations = self._citations(sources, 3)
        product_key = self._product_key(basis)
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

        if product_key == "acetic_acid":
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=[
                    PropertyRecord(name="Molecular weight", value="60.05", units="g/mol", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Melting point", value="16.6", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Boiling point", value="118.1", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Density", value="1.049", units="g/cm3", supporting_sources=citations, citations=citations),
                ],
                uses=["Vinyl acetate monomer chain", "Acetic anhydride and solvents", "Food and pharma intermediates"],
                industrial_relevance="Acetic acid is a large liquid-organic intermediate where route choice and purification economics both matter materially.",
                safety_notes=["Corrosive liquid service requires leak control and metallurgy discipline."],
                markdown="Acetic acid is treated as a continuous liquid-organic benchmark with strong separation and economics sensitivity.",
                citations=citations,
                assumptions=["Mock acetic acid profile uses seeded public values for deterministic testing."],
            )
        if product_key == "sulfuric_acid":
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=[
                    PropertyRecord(name="Molecular weight", value="98.08", units="g/mol", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Melting point", value="10.3", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Boiling point", value="337.0", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Density", value="1.84", units="g/cm3", supporting_sources=citations, citations=citations),
                ],
                uses=["Fertilizer chain", "Metallurgy and pickling", "Chemical manufacture and drying service"],
                industrial_relevance="Sulfuric acid is a strong inorganic benchmark for gas handling, catalytic conversion, absorption, and energy recovery.",
                safety_notes=["Highly corrosive acid mist and SOx handling dominate the hazard envelope."],
                markdown="Sulfuric acid is treated as an inorganic gas-absorption and energy-recovery benchmark rather than a generic liquid product.",
                citations=citations,
                assumptions=["Mock sulfuric acid profile uses seeded public values for deterministic testing."],
            )
        if product_key == "sodium_bicarbonate":
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=[
                    PropertyRecord(name="Molecular weight", value="84.01", units="g/mol", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Melting point", value="50", units="C", supporting_sources=citations, citations=citations, assumptions=["Decomposes rather than boiling cleanly."]),
                    PropertyRecord(name="Boiling point", value="Decomposes", units="-", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Density", value="2.20", units="g/cm3", supporting_sources=citations, citations=citations),
                ],
                uses=["Food and pharma grade uses", "Flue-gas treatment", "Detergents and specialty formulations"],
                industrial_relevance="Sodium bicarbonate is a solids-handling benchmark with crystallization, filtration, drying, and logistics sensitivity.",
                safety_notes=["Dust handling and dryer operation are more important than liquid hazard control."],
                markdown="Sodium bicarbonate is treated as a solids-heavy process benchmark rather than a liquid-organic plant.",
                citations=citations,
                assumptions=["Mock sodium bicarbonate profile uses seeded public values for deterministic testing."],
            )
        if product_key == "phenol":
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=[
                    PropertyRecord(name="Molecular weight", value="94.11", units="g/mol", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Melting point", value="40.5", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Boiling point", value="181.7", units="C", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Density", value="1.07", units="g/cm3", supporting_sources=citations, citations=citations),
                ],
                uses=["Bisphenol and epoxy chain", "Caprolactam and resin intermediates", "Pharmaceutical and specialty derivatives"],
                industrial_relevance="Phenol is treated as an oxidation-led liquid-organic benchmark where byproduct recovery, offgas handling, and purification govern feasibility.",
                safety_notes=["Toxic aromatic liquid handling and oxidation-service safeguards remain central to design."],
                markdown="Phenol is treated as an oxidation and recovery benchmark rather than a generic small-molecule specialty product.",
                citations=citations,
                assumptions=["Mock phenol profile uses seeded public values for deterministic testing."],
            )
        if product_key == "benzalkonium_chloride":
            active_pct = basis.nominal_active_wt_pct or 50.0
            carrier_components = basis.carrier_components or ["water", "ethanol"]
            homolog_distribution = basis.homolog_distribution or {"c12": 0.40, "c14": 0.50, "c16": 0.10}
            product_form = basis.product_form or "50_wt_pct_aqueous_or_alcohol_solution"
            quality_targets = basis.quality_targets or [
                "Residual free benzyl chloride below finished-goods limit",
                "Residual free tertiary amine below finished-goods limit",
                "Color and odor acceptable for formulation service",
            ]
            homolog_text = ", ".join(f"{key.upper()} {value * 100.0:.0f} wt%" for key, value in homolog_distribution.items())
            carrier_text = ", ".join(carrier_components)
            commercial_basis = (
                f"Commercial basis is a {active_pct:.0f} wt% active benzalkonium chloride solution on a "
                f"{basis.throughput_basis.replace('_', ' ')} basis, carried in {carrier_text}. "
                f"The active phase is treated as a homolog bundle ({homolog_text}) rather than a single pure compound."
            )
            return ProductProfileArtifact(
                product_name=basis.target_product,
                properties=[
                    PropertyRecord(name="Molecular weight", value="368.04", units="g/mol", supporting_sources=citations, citations=citations, assumptions=["Representative active MW for a commercial BAC homolog bundle."]),
                    PropertyRecord(name="Melting point", value="-5.0", units="C", supporting_sources=citations, citations=citations, assumptions=["Representative active-solution handling point for seeded BAC service."]),
                    PropertyRecord(name="Boiling point", value="100.0", units="C", supporting_sources=citations, citations=citations, assumptions=["Finished-product BAC is treated as a solution service rather than a neat distillation product."]),
                    PropertyRecord(name="Density", value="0.995", units="g/cm3", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Finished-product active content", value=f"{active_pct:.0f}", units="wt%", supporting_sources=citations, citations=citations),
                    PropertyRecord(name="Representative viscosity", value="0.0025", units="Pa.s", supporting_sources=citations, citations=citations),
                ],
                uses=["Hard-surface disinfectant formulations", "Preservative systems", "Industrial biocide and sanitation service"],
                industrial_relevance="Benzalkonium chloride is treated as a formulated quaternary-ammonium active where continuous quaternization, residual-reactant cleanup, and active-content control matter more than pure-component finishing.",
                safety_notes=[
                    "Benzyl chloride handling and residual control dominate the acute hazard envelope because of lachrymatory and toxic exposure risk.",
                    "Continuous quaternization requires exotherm management, controlled amine feed quality, and color-body suppression through mild thermal history.",
                ],
                commercial_basis_summary=commercial_basis + " Quality targets: " + "; ".join(quality_targets) + ".",
                nominal_active_wt_pct=active_pct,
                product_form=product_form,
                carrier_components=list(carrier_components),
                homolog_distribution=dict(homolog_distribution),
                quality_targets=list(quality_targets),
                markdown=(
                    "Benzalkonium chloride is not treated here as a single neat molecule. The product basis is a 50 wt% commercial active solution built around a homolog bundle and carrier phase, "
                    "so process design must focus on active-content control, residual benzyl chloride / free amine cleanup, color management, and continuous liquid handling.\n\n"
                    + commercial_basis
                ),
                citations=citations,
                assumptions=["Mock BAC product profile uses a representative 50 wt% commercial active-solution basis for deterministic testing."],
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
        product_key = self._product_key(basis)
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

        if product_key == "acetic_acid":
            return MarketAssessmentArtifact(
                estimated_price_per_kg=52.0,
                price_range="INR 46-58 per kg in an India bulk-chemical window.",
                competitor_notes=["Large commodity exposure with import parity sensitivity."],
                demand_drivers=["VAM chain", "Solvents", "Anhydride and downstream esters"],
                capacity_rationale=f"{basis.capacity_tpa:.0f} TPA supports continuous purification and commodity-style fixed-cost recovery.",
                india_price_data=[
                    IndianPriceDatum(datum_id="aa_product", category="product", item_name="Acetic acid", region="India", units="INR/kg", value_inr=52.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="aa_methanol", category="raw_material", item_name="Methanol", region="India", units="INR/kg", value_inr=28.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="aa_power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.2, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="aa_labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=620000.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                ],
                markdown="Acetic acid is treated as a large continuous commodity chemical where route, purification duty, and India logistics jointly control feasibility.",
                citations=citations,
                assumptions=["Mock acetic acid market values are seeded and INR-normalized."],
            )
        if product_key == "sulfuric_acid":
            return MarketAssessmentArtifact(
                estimated_price_per_kg=11.0,
                price_range="INR 8-14 per kg in an India sulfuric acid commodity window.",
                competitor_notes=["Strong fertilizer and industrial acid demand but thinner per-kg margins."],
                demand_drivers=["Fertilizers", "Metal processing", "Chemical manufacture"],
                capacity_rationale=f"{basis.capacity_tpa:.0f} TPA supports absorber and heat-recovery economics.",
                india_price_data=[
                    IndianPriceDatum(datum_id="sa_product", category="product", item_name="Sulfuric acid", region="India", units="INR/kg", value_inr=11.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sa_sulfur", category="raw_material", item_name="Sulfur", region="India", units="INR/kg", value_inr=13.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sa_power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sa_labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=600000.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                ],
                markdown="Sulfuric acid economics are thin on a per-kilogram basis, so heat recovery and plant scale are central to viability.",
                citations=citations,
                assumptions=["Mock sulfuric acid market values are seeded and INR-normalized."],
            )
        if product_key == "sodium_bicarbonate":
            return MarketAssessmentArtifact(
                estimated_price_per_kg=24.0,
                price_range="INR 20-30 per kg in an India industrial/food-grade window.",
                competitor_notes=["Product mix and solids handling efficiency materially affect margin."],
                demand_drivers=["Food and pharma", "Detergents", "Flue-gas treatment"],
                capacity_rationale=f"{basis.capacity_tpa:.0f} TPA balances solids handling with defensible market absorption.",
                india_price_data=[
                    IndianPriceDatum(datum_id="sb_product", category="product", item_name="Sodium bicarbonate", region="India", units="INR/kg", value_inr=24.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sb_soda_ash", category="raw_material", item_name="Soda ash", region="India", units="INR/kg", value_inr=22.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sb_power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.4, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="sb_labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=580000.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                ],
                markdown="Sodium bicarbonate economics depend on solids yield, dryer duty, grading, and India distribution assumptions.",
                citations=citations,
                assumptions=["Mock sodium bicarbonate market values are seeded and INR-normalized."],
            )
        if product_key == "phenol":
            return MarketAssessmentArtifact(
                estimated_price_per_kg=96.0,
                price_range="INR 84-110 per kg in an India bulk aromatic/intermediate window.",
                competitor_notes=["Feedstock linkage to aromatics and byproduct acetone recovery both influence margin resilience."],
                demand_drivers=["Bisphenol-A chain", "Phenolic resins", "Caprolactam and downstream intermediates"],
                capacity_rationale=f"{basis.capacity_tpa:.0f} TPA supports continuous oxidation, recovery distillation, and shared utility economics.",
                india_price_data=[
                    IndianPriceDatum(datum_id="phenol_product", category="product", item_name="Phenol", region="India", units="INR/kg", value_inr=96.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="phenol_cumene", category="raw_material", item_name="Cumene", region="India", units="INR/kg", value_inr=74.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="phenol_power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.3, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="phenol_labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=640000.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                ],
                markdown="Phenol is treated as a large continuous aromatic intermediate where oxidation selectivity, acetone credit, and India aromatics logistics together shape the business case.",
                citations=citations,
                assumptions=["Mock phenol market values are seeded and INR-normalized."],
            )
        if product_key == "benzalkonium_chloride":
            active_pct = basis.nominal_active_wt_pct or 50.0
            return MarketAssessmentArtifact(
                estimated_price_per_kg=185.0,
                price_range="INR 165-220 per kg on a commercial BAC solution basis.",
                competitor_notes=[
                    "Commercial pricing is usually quoted on active-solution grade, not on an isolated pure active basis.",
                    "Margin resilience depends on feed amine cost, benzyl chloride quality, and solution-basis logistics rather than only on reaction yield.",
                ],
                demand_drivers=["Institutional and household disinfectants", "Industrial sanitation", "Preservative and antimicrobial formulations"],
                capacity_rationale=(
                    f"{basis.capacity_tpa:.0f} TPA is framed as a large continuous formulation-active train on a finished-product basis, "
                    f"with product sold as roughly {active_pct:.0f} wt% active solution rather than as a purified neat salt."
                ),
                india_price_data=[
                    IndianPriceDatum(datum_id="bac_product", category="product", item_name="Benzalkonium chloride solution", region="India", units="INR/kg", value_inr=185.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="bac_benzyl_chloride", category="raw_material", item_name="Benzyl chloride", region="India", units="INR/kg", value_inr=92.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="bac_amine", category="raw_material", item_name="Alkyldimethylamine blend", region="India", units="INR/kg", value_inr=148.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="bac_power", category="utility", item_name="Electricity", region="India", units="INR/kWh", value_inr=8.4, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                    IndianPriceDatum(datum_id="bac_labor", category="labor", item_name="Operating labour", region="India", units="INR/person-year", value_inr=640000.0, reference_year=2025, normalization_year=2025, citations=[citations[0]]),
                ],
                markdown="Benzalkonium chloride is treated as a continuous quaternary-ammonium active solution business where active-content basis, residual cleanup, and formulation-grade logistics govern feasibility more than neat-product purification.",
                citations=citations,
                assumptions=["Mock BAC market values are seeded on a 50 wt% finished-product solution basis normalized to 2025 INR."],
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
        product_key = self._product_key(basis)
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

        if product_key == "acetic_acid":
            routes = [
                RouteOption(route_id="methanol_carbonylation", name="Methanol carbonylation", reaction_equation="CH4O + CO -> C2H4O2", participants=[ReactionParticipant(name="Methanol", formula="CH4O", coefficient=1.0, role="reactant", molecular_weight_g_mol=32.04, phase="liquid"), ReactionParticipant(name="Carbon monoxide", formula="CO", coefficient=1.0, role="reactant", molecular_weight_g_mol=28.01, phase="gas"), ReactionParticipant(name="Acetic acid", formula="C2H4O2", coefficient=1.0, role="product", molecular_weight_g_mol=60.05, phase="liquid")], catalysts=["Rhodium/iodide system"], operating_temperature_c=190.0, operating_pressure_bar=30.0, residence_time_hr=1.1, yield_fraction=0.96, selectivity_fraction=0.98, byproducts=["trace propionic acid"], separations=["flash", "distillation", "light-ends removal"], scale_up_notes="Commodity route with strong industrial maturity.", route_score=9.4, rationale="Best industrial fit and strongest economics.", citations=citations),
                RouteOption(route_id="acetaldehyde_oxidation", name="Acetaldehyde oxidation", reaction_equation="C2H4O + 0.5 O2 -> C2H4O2", participants=[ReactionParticipant(name="Acetaldehyde", formula="C2H4O", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.05, phase="liquid"), ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"), ReactionParticipant(name="Acetic acid", formula="C2H4O2", coefficient=1.0, role="product", molecular_weight_g_mol=60.05, phase="liquid")], catalysts=["Metal salt catalyst"], operating_temperature_c=65.0, operating_pressure_bar=5.0, residence_time_hr=2.0, yield_fraction=0.88, selectivity_fraction=0.91, byproducts=["CO2"], separations=["gas vent", "distillation"], scale_up_notes="Older liquid oxidation route.", route_score=7.1, rationale="Technically feasible but weaker than carbonylation.", citations=citations),
                RouteOption(route_id="butane_oxidation", name="Butane oxidation", reaction_equation="C4H10 + 2.5 O2 -> 2 C2H4O2 + H2O", participants=[ReactionParticipant(name="n-Butane", formula="C4H10", coefficient=1.0, role="reactant", molecular_weight_g_mol=58.12, phase="gas"), ReactionParticipant(name="Oxygen", formula="O2", coefficient=2.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"), ReactionParticipant(name="Acetic acid", formula="C2H4O2", coefficient=2.0, role="product", molecular_weight_g_mol=60.05, phase="liquid"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="byproduct", molecular_weight_g_mol=18.015, phase="liquid")], catalysts=["Co/Mn catalyst"], operating_temperature_c=180.0, operating_pressure_bar=55.0, residence_time_hr=1.6, yield_fraction=0.80, selectivity_fraction=0.84, byproducts=["CO2", "formic acid"], separations=["gas quench", "distillation"], scale_up_notes="High-pressure oxidation with wider byproduct spread.", route_score=6.5, rationale="Lower selectivity and harsher conditions.", citations=citations),
            ]
            return RouteSurveyArtifact(routes=routes, markdown="Acetic acid route survey compares methanol carbonylation against oxidation routes on selectivity, duty, and industrial maturity.", citations=citations, assumptions=["Mock acetic acid route survey uses seeded industrial route families."])
        if product_key == "sulfuric_acid":
            routes = [
                RouteOption(route_id="contact_double_absorption", name="Contact process with double absorption", reaction_equation="SO2 + 0.5 O2 + H2O -> H2SO4", participants=[ReactionParticipant(name="Sulfur dioxide", formula="SO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=64.07, phase="gas"), ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"), ReactionParticipant(name="Sulfuric acid", formula="H2SO4", coefficient=1.0, role="product", molecular_weight_g_mol=98.08, phase="liquid")], catalysts=["V2O5 catalyst"], operating_temperature_c=430.0, operating_pressure_bar=1.6, residence_time_hr=0.8, yield_fraction=0.98, selectivity_fraction=0.995, byproducts=["trace SO3 mist"], separations=["catalytic conversion", "interpass absorption", "final absorption"], scale_up_notes="Industry-standard route with strong energy recovery potential.", route_score=9.6, rationale="Best precedent and energy integration basis.", citations=citations),
                RouteOption(route_id="wet_sulfuric_acid", name="Wet sulfuric acid route", reaction_equation="SO2 + 0.5 O2 + H2O -> H2SO4", participants=[ReactionParticipant(name="Sulfur dioxide", formula="SO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=64.07, phase="gas"), ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"), ReactionParticipant(name="Sulfuric acid", formula="H2SO4", coefficient=1.0, role="product", molecular_weight_g_mol=98.08, phase="liquid")], catalysts=["V2O5 catalyst"], operating_temperature_c=420.0, operating_pressure_bar=1.4, residence_time_hr=1.0, yield_fraction=0.95, selectivity_fraction=0.98, byproducts=["acid mist"], separations=["gas drying", "condensation/absorption"], scale_up_notes="Useful when feed gas is wet or offgas-based.", route_score=8.2, rationale="Viable but more feed-specific than the standard contact route.", citations=citations),
                RouteOption(route_id="spent_acid_regeneration", name="Spent acid regeneration", reaction_equation="H2SO4 -> H2SO4", participants=[ReactionParticipant(name="Spent acid", formula="H2SO4", coefficient=1.0, role="reactant", molecular_weight_g_mol=98.08, phase="liquid"), ReactionParticipant(name="Sulfuric acid", formula="H2SO4", coefficient=1.0, role="product", molecular_weight_g_mol=98.08, phase="liquid")], catalysts=[], operating_temperature_c=900.0, operating_pressure_bar=1.2, residence_time_hr=1.5, yield_fraction=0.90, selectivity_fraction=0.94, byproducts=["SOx offgas"], separations=["thermal decomposition", "gas cleanup", "absorption"], scale_up_notes="Useful as a regeneration service rather than greenfield commodity route.", route_score=5.8, rationale="Not the best primary route for a new commodity acid plant.", citations=citations),
            ]
            return RouteSurveyArtifact(routes=routes, markdown="Sulfuric acid route survey compares contact-process and related gas-absorption pathways.", citations=citations, assumptions=["Mock sulfuric acid route survey uses seeded industrial route families."])
        if product_key == "sodium_bicarbonate":
            routes = [
                RouteOption(route_id="soda_ash_carboxylation", name="Soda ash carbonation", reaction_equation="Na2CO3 + CO2 + H2O -> 2 NaHCO3", participants=[ReactionParticipant(name="Soda ash", formula="Na2CO3", coefficient=1.0, role="reactant", molecular_weight_g_mol=105.99, phase="solid"), ReactionParticipant(name="Carbon dioxide", formula="CO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.01, phase="gas"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"), ReactionParticipant(name="Sodium bicarbonate", formula="NaHCO3", coefficient=2.0, role="product", molecular_weight_g_mol=84.01, phase="solid")], catalysts=[], operating_temperature_c=40.0, operating_pressure_bar=3.0, residence_time_hr=2.4, yield_fraction=0.93, selectivity_fraction=0.97, byproducts=[], separations=["crystallization", "filtration", "drying"], scale_up_notes="Simple solids route with strong fit for food/industrial grade production.", route_score=9.1, rationale="Best fit for a dedicated sodium bicarbonate plant.", citations=citations),
                RouteOption(route_id="solvay_liquor_route", name="Solvay liquor route", reaction_equation="NaCl + NH3 + CO2 + H2O -> NaHCO3 + NH4Cl", participants=[ReactionParticipant(name="Sodium chloride", formula="NaCl", coefficient=1.0, role="reactant", molecular_weight_g_mol=58.44, phase="liquid"), ReactionParticipant(name="Ammonia", formula="NH3", coefficient=1.0, role="reactant", molecular_weight_g_mol=17.03, phase="gas"), ReactionParticipant(name="Carbon dioxide", formula="CO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.01, phase="gas"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"), ReactionParticipant(name="Sodium bicarbonate", formula="NaHCO3", coefficient=1.0, role="product", molecular_weight_g_mol=84.01, phase="solid"), ReactionParticipant(name="Ammonium chloride", formula="NH4Cl", coefficient=1.0, role="byproduct", molecular_weight_g_mol=53.49, phase="solid")], catalysts=[], operating_temperature_c=35.0, operating_pressure_bar=2.0, residence_time_hr=3.0, yield_fraction=0.84, selectivity_fraction=0.90, byproducts=["Ammonium chloride mother liquor"], separations=["crystallization", "filtration", "ammonia recovery", "drying"], scale_up_notes="More integrated but more complex solids/liquor handling route.", route_score=7.6, rationale="Possible when upstream Solvay integration exists.", citations=citations),
                RouteOption(route_id="trona_refining", name="Trona refining and bicarbonation", reaction_equation="Na2CO3 + CO2 + H2O -> 2 NaHCO3", participants=[ReactionParticipant(name="Sodium carbonate liquor", formula="Na2CO3", coefficient=1.0, role="reactant", molecular_weight_g_mol=105.99, phase="liquid"), ReactionParticipant(name="Carbon dioxide", formula="CO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.01, phase="gas"), ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"), ReactionParticipant(name="Sodium bicarbonate", formula="NaHCO3", coefficient=2.0, role="product", molecular_weight_g_mol=84.01, phase="solid")], catalysts=[], operating_temperature_c=45.0, operating_pressure_bar=4.0, residence_time_hr=2.1, yield_fraction=0.88, selectivity_fraction=0.93, byproducts=["Insoluble solids"], separations=["clarification", "crystallization", "filtration", "drying"], scale_up_notes="Feedstock dependent and more impurity-sensitive.", route_score=7.0, rationale="Feed-sensitive route with additional solids cleanup burden.", citations=citations),
            ]
            return RouteSurveyArtifact(routes=routes, markdown="Sodium bicarbonate route survey compares direct carbonation, integrated Solvay liquor handling, and trona-derived pathways.", citations=citations, assumptions=["Mock sodium bicarbonate route survey uses seeded industrial route families."])
        if product_key == "phenol":
            routes = [
                RouteOption(
                    route_id="cumene_oxidation_cleavage",
                    name="Cumene oxidation and cleavage",
                    reaction_equation="C9H12 + O2 -> C6H6O + C3H6O",
                    participants=[
                        ReactionParticipant(name="Cumene", formula="C9H12", coefficient=1.0, role="reactant", molecular_weight_g_mol=120.19, phase="liquid"),
                        ReactionParticipant(name="Oxygen", formula="O2", coefficient=1.0, role="reactant", molecular_weight_g_mol=32.0, phase="gas"),
                        ReactionParticipant(name="Phenol", formula="C6H6O", coefficient=1.0, role="product", molecular_weight_g_mol=94.11, phase="liquid"),
                        ReactionParticipant(name="Acetone", formula="C3H6O", coefficient=1.0, role="byproduct", molecular_weight_g_mol=58.08, phase="liquid"),
                    ],
                    catalysts=["Oxidation promoter", "Acid cleavage catalyst"],
                    operating_temperature_c=95.0,
                    operating_pressure_bar=4.5,
                    residence_time_hr=2.2,
                    yield_fraction=0.95,
                    selectivity_fraction=0.93,
                    byproducts=["alpha-methylstyrene", "acetophenone"],
                    separations=["air oxidation", "phase split", "caustic wash", "acetone recovery", "phenol distillation"],
                    scale_up_notes="Strong industrial precedent with oxidation control, byproduct management, and recovery distillation.",
                    hazards=[RouteHazard(severity="moderate", description="Oxidation service and peroxide inventory control", safeguard="Tight oxidation temperature control and staged quench/relief handling")],
                    route_score=9.2,
                    rationale="Best industrial fit with credible byproduct recovery and established aromatics value chain logic.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="chlorobenzene_hydrolysis",
                    name="Chlorobenzene caustic hydrolysis",
                    reaction_equation="C6H5Cl + NaOH -> C6H6O + NaCl",
                    participants=[
                        ReactionParticipant(name="Chlorobenzene", formula="C6H5Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=112.56, phase="liquid"),
                        ReactionParticipant(name="Sodium hydroxide", formula="NaOH", coefficient=1.0, role="reactant", molecular_weight_g_mol=40.0, phase="liquid"),
                        ReactionParticipant(name="Phenol", formula="C6H6O", coefficient=1.0, role="product", molecular_weight_g_mol=94.11, phase="liquid"),
                        ReactionParticipant(name="Sodium chloride", formula="NaCl", coefficient=1.0, role="byproduct", molecular_weight_g_mol=58.44, phase="solid"),
                    ],
                    catalysts=[],
                    operating_temperature_c=350.0,
                    operating_pressure_bar=18.0,
                    residence_time_hr=3.0,
                    yield_fraction=0.82,
                    selectivity_fraction=0.86,
                    byproducts=["saline purge", "chlorinated heavies"],
                    separations=["salt removal", "caustic wash", "phenol distillation"],
                    scale_up_notes="Legacy hydrolysis route with heavy chloride burden and harsher metallurgy requirements.",
                    hazards=[RouteHazard(severity="high", description="Hot caustic and chloride-rich service", safeguard="High-alloy metallurgy, brine control, and aggressive relief/isolation design")],
                    route_score=5.8,
                    rationale="Technically possible but penalized by waste, corrosion burden, and lower industrial preference.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="benzene_direct_hydroxylation",
                    name="Direct benzene oxidation to phenol",
                    reaction_equation="C6H6 + 0.5 O2 -> C6H6O",
                    participants=[
                        ReactionParticipant(name="Benzene", formula="C6H6", coefficient=1.0, role="reactant", molecular_weight_g_mol=78.11, phase="liquid"),
                        ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"),
                        ReactionParticipant(name="Phenol", formula="C6H6O", coefficient=1.0, role="product", molecular_weight_g_mol=94.11, phase="liquid"),
                    ],
                    catalysts=["Oxidation catalyst"],
                    operating_temperature_c=210.0,
                    operating_pressure_bar=10.0,
                    residence_time_hr=1.7,
                    yield_fraction=0.72,
                    selectivity_fraction=0.76,
                    byproducts=["catechol", "hydroquinone", "tar"],
                    separations=["gas vent", "wash", "solvent recovery", "phenol distillation"],
                    scale_up_notes="Conceptually attractive but selectivity-sensitive and less commercially mature than the cumene route.",
                    hazards=[RouteHazard(severity="moderate", description="Oxidation selectivity and hot aromatic service", safeguard="Oxygen control, staged quench, and byproduct bleed management")],
                    route_score=6.7,
                    rationale="Interesting direct-oxidation alternative, but weaker maturity and byproduct spread than cumene oxidation.",
                    citations=citations,
                ),
            ]
            return RouteSurveyArtifact(
                routes=routes,
                markdown="Phenol route survey compares the industrially dominant cumene oxidation route against chlorinated hydrolysis and direct oxidation concepts, emphasizing offgas handling, byproduct recovery, and purification burden.",
                citations=citations,
                assumptions=["Mock phenol route survey uses seeded oxidation and recovery route families for deterministic testing."],
            )
        if product_key == "benzalkonium_chloride":
            routes = [
                RouteOption(
                    route_id="benzyl_chloride_quaternization_ethanol",
                    name="Benzyl chloride quaternization in alcohol medium",
                    reaction_equation="Alkyldimethylamine + Benzyl chloride -> Benzalkonium chloride",
                    participants=[
                        ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                        ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                        ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
                    ],
                    evidence_score=0.88,
                    chemistry_completeness_score=0.95,
                    separation_complexity_score=0.58,
                    catalysts=[],
                    solvents=["Ethanol", "Water"],
                    operating_temperature_c=82.0,
                    operating_pressure_bar=2.5,
                    residence_time_hr=2.0,
                    yield_fraction=0.96,
                    selectivity_fraction=0.97,
                    byproducts=["trace benzyl alcohol from hydrolysis", "residual free amine", "residual benzyl chloride"],
                    separations=["feed drying and conditioning", "continuous quaternization", "ethanol recovery", "light-ends stripping", "active dilution and polishing"],
                    scale_up_notes="Industrial BAC route using a C12-C16 alkyldimethylamine blend and benzyl chloride in alcohol medium. Continuous quaternization gives a solution-phase active that is sold on a 50 wt% finished-product solution basis after residual-reactant cleanup and dilution.",
                    hazards=[
                        RouteHazard(severity="high", description="Benzyl chloride toxicity and liquid-phase quaternization exotherm", safeguard="Closed feed handling, staged reactant addition, and residual benzyl chloride stripping/polishing"),
                    ],
                    route_score=9.1,
                    rationale="Best industrial fit because it matches commercial BAC solution manufacture, gives manageable continuous operation, and keeps solvent recovery and residual cleanup within a familiar liquid train.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="benzyl_chloride_quaternization_high_strength",
                    name="High-strength continuous quaternization with low-solvent finishing",
                    reaction_equation="Alkyldimethylamine + Benzyl chloride -> Benzalkonium chloride",
                    participants=[
                        ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                        ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                        ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
                    ],
                    evidence_score=0.76,
                    chemistry_completeness_score=0.93,
                    separation_complexity_score=0.66,
                    catalysts=[],
                    solvents=["Ethanol", "Water"],
                    operating_temperature_c=88.0,
                    operating_pressure_bar=3.0,
                    residence_time_hr=1.6,
                    yield_fraction=0.95,
                    selectivity_fraction=0.95,
                    byproducts=["residual free amine", "residual benzyl chloride", "color bodies"],
                    separations=["feed drying and conditioning", "high-strength quaternization", "light-ends flashing", "vacuum polishing", "water/alcohol trim blend"],
                    scale_up_notes="Higher active-content route with less solvent circulation, but stronger viscosity, color, and exotherm-control burden. Useful where solvent load must be minimized, but residual cleanup is tighter.",
                    hazards=[
                        RouteHazard(severity="high", description="Higher adiabatic temperature rise and tighter residual-reactant window", safeguard="Intensified heat removal, narrow feed-ratio control, and continuous residual polish"),
                    ],
                    route_score=7.8,
                    rationale="Credible continuous variant, but operability and product-color burden are harder than the alcohol-medium base case.",
                    citations=citations,
                ),
                RouteOption(
                    route_id="benzyl_alcohol_activation_quaternization",
                    name="Integrated benzyl alcohol activation followed by quaternization",
                    reaction_equation="Benzyl alcohol + HCl + Alkyldimethylamine -> Benzalkonium chloride + H2O",
                    participants=[
                        ReactionParticipant(name="Benzyl alcohol", formula="C7H8O", coefficient=1.0, role="reactant", molecular_weight_g_mol=108.14, phase="liquid"),
                        ReactionParticipant(name="Hydrogen chloride", formula="HCl", coefficient=1.0, role="reactant", molecular_weight_g_mol=36.46, phase="gas"),
                        ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                        ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
                        ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="byproduct", molecular_weight_g_mol=18.015, phase="liquid"),
                    ],
                    evidence_score=0.62,
                    chemistry_completeness_score=0.88,
                    separation_complexity_score=0.74,
                    catalysts=[],
                    solvents=["Water"],
                    operating_temperature_c=95.0,
                    operating_pressure_bar=3.5,
                    residence_time_hr=3.0,
                    yield_fraction=0.90,
                    selectivity_fraction=0.91,
                    byproducts=["hydrolyzed benzyl species", "aqueous chloride purge", "residual free amine"],
                    separations=["benzyl activation", "quaternization", "water removal", "chloride-bearing purge cleanup", "product polishing"],
                    scale_up_notes="Chemically plausible integrated route, but extra water and chloride-handling burden make it less attractive than direct benzyl chloride quaternization for a large continuous BAC plant.",
                    hazards=[
                        RouteHazard(severity="high", description="HCl handling, chloride corrosion, and added water-removal burden", safeguard="Corrosion-resistant metallurgy, dry-feed control, and chloride purge management"),
                    ],
                    route_score=6.4,
                    rationale="Provides a real alternative hypothesis, but the added activation and water-removal burden make it weaker for this basis.",
                    citations=citations,
                ),
            ]
            return RouteSurveyArtifact(
                routes=routes,
                markdown="Benzalkonium chloride route survey compares continuous quaternization variants built around benzyl chloride and alkyldimethylamine feed bundles, with screening focused on exotherm control, residual benzyl chloride cleanup, solvent recovery, and active-solution product quality.",
                citations=citations,
                assumptions=["Mock BAC route survey uses seeded quaternization route hypotheses anchored to a commercial active-solution product basis."],
            )
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
        product_key = self._product_key(basis)
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

        if product_key == "acetic_acid":
            return SiteSelectionArtifact(
                candidates=[
                    SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="Carbonylation-style commodity service fits a strong chemical cluster.", citations=citations),
                    SiteOption(name="Hazira", state="Gujarat", raw_material_score=8, logistics_score=8, utility_score=8, business_score=7, total_score=31, rationale="Good west-coast logistics and chemical support services.", citations=citations),
                ],
                selected_site="Dahej",
                india_location_data=[
                    IndianLocationDatum(location_id="aa_dahej", site_name="Dahej", state="Gujarat", port_access="West coast chemical-port access", utility_note="Mature utility backbone for continuous chemicals.", logistics_note="Strong raw-material and product dispatch links.", regulatory_note="Established industrial operating ecosystem.", reference_year=2025, citations=citations),
                    IndianLocationDatum(location_id="aa_hazira", site_name="Hazira", state="Gujarat", port_access="Hazira marine access", utility_note="Good utility and gas infrastructure.", logistics_note="Good west-coast logistics fit.", regulatory_note="Established but slightly tighter land envelope than Dahej.", reference_year=2025, citations=citations),
                ],
                markdown="Dahej is selected because it best balances utility infrastructure, carbonylation-style raw material logistics, and chemical cluster services.",
                citations=citations,
                assumptions=["Mock acetic acid site scoring uses seeded India cluster logic."],
            )
        if product_key == "sulfuric_acid":
            return SiteSelectionArtifact(
                candidates=[
                    SiteOption(name="Paradip", state="Odisha", raw_material_score=9, logistics_score=8, utility_score=8, business_score=7, total_score=32, rationale="Strong sulfur and port linkage.", citations=citations),
                    SiteOption(name="Dahej", state="Gujarat", raw_material_score=8, logistics_score=9, utility_score=9, business_score=8, total_score=34, rationale="Strong industrial utility and dispatch infrastructure.", citations=citations),
                ],
                selected_site="Dahej",
                india_location_data=[
                    IndianLocationDatum(location_id="sa_dahej", site_name="Dahej", state="Gujarat", port_access="West coast chemical-port access", utility_note="Strong industrial utilities and services.", logistics_note="Strong fertilizer and chemical dispatch linkage.", regulatory_note="Established industrial compliance environment.", reference_year=2025, citations=citations),
                    IndianLocationDatum(location_id="sa_paradip", site_name="Paradip", state="Odisha", port_access="East coast port access", utility_note="Useful port-driven sulfur import basis.", logistics_note="Good for east India distribution.", regulatory_note="Project-specific development burden remains higher.", reference_year=2025, citations=citations),
                ],
                markdown="Dahej is selected because utility, logistics, and industrial services slightly outweigh Paradip's sulfur import advantage in the seeded benchmark.",
                citations=citations,
                assumptions=["Mock sulfuric acid site scoring uses seeded India cluster logic."],
            )
        if product_key == "sodium_bicarbonate":
            return SiteSelectionArtifact(
                candidates=[
                    SiteOption(name="Mithapur", state="Gujarat", raw_material_score=9, logistics_score=7, utility_score=8, business_score=8, total_score=32, rationale="Strong alkali and soda-ash ecosystem for bicarbonate service.", citations=citations),
                    SiteOption(name="Dahej", state="Gujarat", raw_material_score=8, logistics_score=9, utility_score=9, business_score=8, total_score=34, rationale="Strong logistics and utilities with solids dispatch options.", citations=citations),
                ],
                selected_site="Dahej",
                india_location_data=[
                    IndianLocationDatum(location_id="sb_dahej", site_name="Dahej", state="Gujarat", port_access="West coast chemical-port access", utility_note="Strong utility backbone and industrial services.", logistics_note="Good solids dispatch and bulk truck connectivity.", regulatory_note="Established industrial operating context.", reference_year=2025, citations=citations),
                    IndianLocationDatum(location_id="sb_mithapur", site_name="Mithapur", state="Gujarat", port_access="Regional port and road connectivity", utility_note="Strong soda-ash ecosystem support.", logistics_note="Good raw-material fit but narrower dispatch ecosystem than Dahej.", regulatory_note="Industrially credible but more feedstock-specific.", reference_year=2025, citations=citations),
                ],
                markdown="Dahej is selected because logistics and utilities outweigh the feedstock-specific advantage of Mithapur in the seeded benchmark.",
                citations=citations,
                assumptions=["Mock sodium bicarbonate site scoring uses seeded India cluster logic."],
            )
        if product_key == "phenol":
            return SiteSelectionArtifact(
                candidates=[
                    SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="Strong west-coast aromatics logistics, utilities, and recovery-service ecosystem.", citations=citations),
                    SiteOption(name="Hazira", state="Gujarat", raw_material_score=8, logistics_score=8, utility_score=8, business_score=7, total_score=31, rationale="Credible aromatics and export linkage with a slightly tighter cluster envelope.", citations=citations),
                ],
                selected_site="Dahej",
                india_location_data=[
                    IndianLocationDatum(location_id="phenol_dahej", site_name="Dahej", state="Gujarat", port_access="West coast chemical-port access for aromatics and solvent logistics", utility_note="Strong steam, power, cooling water, and industrial services for continuous oxidation-recovery plants.", logistics_note="Good feedstock receipt and liquid product dispatch through established chemical-cluster infrastructure.", regulatory_note="Established industrial operating context suited to continuous aromatic chemical manufacture.", reference_year=2025, citations=citations),
                    IndianLocationDatum(location_id="phenol_hazira", site_name="Hazira", state="Gujarat", port_access="Hazira marine access and west-coast dispatch links", utility_note="Good utility and gas infrastructure for oxidation-led service.", logistics_note="Strong export and western India dispatch options.", regulatory_note="Credible industrial site basis, though with a narrower expansion envelope than Dahej.", reference_year=2025, citations=citations),
                ],
                markdown="Dahej is selected because it best combines aromatics logistics, continuous utility support, and chemical-cluster services for a phenol oxidation and recovery train.",
                citations=citations,
                assumptions=["Mock phenol site scoring uses seeded India aromatics-cluster logic."],
            )
        candidates = [
            SiteOption(name="Dahej", state="Gujarat", raw_material_score=9, logistics_score=9, utility_score=9, business_score=8, total_score=35, rationale="Strong chemical ecosystem and port access.", citations=citations),
            SiteOption(name="Navi Mumbai", state="Maharashtra", raw_material_score=7, logistics_score=8, utility_score=8, business_score=6, total_score=29, rationale="Good market access but tighter land and compliance envelope.", citations=citations),
        ]
        return SiteSelectionArtifact(
            candidates=candidates,
            selected_site="Dahej",
            india_location_data=[
                IndianLocationDatum(location_id="generic_dahej", site_name="Dahej", state="Gujarat", port_access="West coast chemical-port access", utility_note="Strong continuous utility backbone for steam, power, and cooling water.", logistics_note="Strong liquid-chemical logistics and cluster services.", regulatory_note="Established chemical-zone operating context.", reference_year=2025, citations=citations),
                IndianLocationDatum(location_id="generic_navi_mumbai", site_name="Navi Mumbai", state="Maharashtra", port_access="JNPT and western India logistics connectivity", utility_note="Credible urban industrial utility basis.", logistics_note="Good market access with higher land and compliance friction.", regulatory_note="More constrained land and permitting envelope than Dahej.", reference_year=2025, citations=citations),
            ],
            markdown="Dahej is selected in the seeded run because the cluster offers strong logistics, utilities, and India deployment support for generic benchmark expansion.",
            citations=citations,
            assumptions=["Mock site selection uses seeded India cluster scoring rather than geospatial optimization."],
        )

    def build_thermo_assessment(self, basis: ProjectBasis, route: RouteOption, sources, corpus: str) -> ThermoAssessmentArtifact:
        citations = self._citations(sources, 3)
        product_key = self._product_key(basis)
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
        if product_key == "acetic_acid":
            return ThermoAssessmentArtifact(feasible=True, estimated_reaction_enthalpy_kj_per_mol=-140.0, estimated_gibbs_kj_per_mol=-95.0, equilibrium_comment="The selected acetic-acid route is thermodynamically favorable and strongly biased toward products under the selected operating window.", markdown="The seeded acetic-acid thermodynamic basis indicates a favorable reaction with manageable thermal load but meaningful purification consequences.", citations=citations, assumptions=["Mock acetic acid thermodynamic values are seeded for deterministic testing."])
        if product_key == "sulfuric_acid":
            return ThermoAssessmentArtifact(feasible=True, estimated_reaction_enthalpy_kj_per_mol=-227.0, estimated_gibbs_kj_per_mol=-140.0, equilibrium_comment="Sulfuric acid formation is highly favorable and strongly exothermic, making heat recovery central to feasibility.", markdown="The seeded sulfuric acid thermodynamic basis is strongly exothermic and therefore pushes the design toward heat recovery and robust absorption control.", citations=citations, assumptions=["Mock sulfuric acid thermodynamic values are seeded for deterministic testing."])
        if product_key == "sodium_bicarbonate":
            return ThermoAssessmentArtifact(feasible=True, estimated_reaction_enthalpy_kj_per_mol=-31.0, estimated_gibbs_kj_per_mol=-18.0, equilibrium_comment="The sodium bicarbonate route is moderately favorable under cool carbonation and crystallization conditions.", markdown="The seeded sodium bicarbonate thermodynamic basis supports low-temperature carbonation and downstream crystallization.", citations=citations, assumptions=["Mock sodium bicarbonate thermodynamic values are seeded for deterministic testing."])
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
        product_key = self._product_key(basis)
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
        if product_key == "acetic_acid":
            return KineticAssessmentArtifact(feasible=True, activation_energy_kj_per_mol=82.0, pre_exponential_factor=6.4e8, apparent_order=1.0, design_residence_time_hr=route.residence_time_hr, markdown="The seeded acetic-acid kinetics basis supports continuous reactor sizing and strengthens the case for catalytic continuous service.", citations=citations, assumptions=["Mock acetic acid kinetic values are seeded for deterministic testing."])
        if product_key == "sulfuric_acid":
            return KineticAssessmentArtifact(feasible=True, activation_energy_kj_per_mol=96.0, pre_exponential_factor=1.8e9, apparent_order=1.0, design_residence_time_hr=route.residence_time_hr, markdown="The seeded sulfuric-acid kinetics basis supports catalytic converter sizing at short gas-phase residence time.", citations=citations, assumptions=["Mock sulfuric acid kinetic values are seeded for deterministic testing."])
        if product_key == "sodium_bicarbonate":
            return KineticAssessmentArtifact(feasible=True, activation_energy_kj_per_mol=38.0, pre_exponential_factor=7.5e5, apparent_order=1.0, design_residence_time_hr=route.residence_time_hr, markdown="The seeded sodium bicarbonate kinetics basis supports crystallizer residence-time sizing rather than high-severity reactor service.", citations=citations, assumptions=["Mock sodium bicarbonate kinetic values are seeded for deterministic testing."])
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
        product_key = self._product_key(basis)
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

        if product_key == "sulfuric_acid":
            mermaid = "\n".join(["flowchart LR", "A[SO2 Feed] --> B[Drying]", "B --> C[Converter]", "C --> D[Interpass Absorption]", "D --> E[Final Absorption]", "E --> F[Acid Storage]", "C --> G[Heat Recovery]"])
            return ProcessNarrativeArtifact(bfd_mermaid=mermaid, markdown="Sulfur dioxide feed is dried, catalytically converted, absorbed, and cooled through a heat-recovery-aware gas processing train.", citations=citations, assumptions=["Seeded sulfuric acid BFD reflects contact-process logic."])
        if product_key == "sodium_bicarbonate":
            mermaid = "\n".join(["flowchart LR", "A[Soda Ash] --> B[Carbonation]", "C[CO2] --> B", "B --> D[Crystallization]", "D --> E[Filtration]", "E --> F[Drying]", "F --> G[Product Storage]"])
            return ProcessNarrativeArtifact(bfd_mermaid=mermaid, markdown="Soda ash solution is carbonated, crystallized, filtered, dried, and sent to solids storage and dispatch.", citations=citations, assumptions=["Seeded sodium bicarbonate BFD reflects solids-processing logic."])
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
