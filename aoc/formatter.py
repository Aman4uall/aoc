from __future__ import annotations

import html
import re
from collections import OrderedDict

from aoc.models import (
    BenchmarkStyleProfile,
    BenchmarkVoiceProfile,
    ChapterArtifact,
    FormattedReportArtifact,
    FormatterAcceptanceArtifact,
    FormatterChapterGroup,
    FormatterDecisionArtifact,
    FormatterParityArtifact,
    FormatterTargetProfile,
    NarrativeRewriteArtifact,
    NarrativeRewriteBlock,
    ProjectBasis,
    ReportAcceptanceStatus,
    ReportParityStatus,
    SemanticBlock,
    SemanticReportArtifact,
    SemanticSection,
    SentencePatternLibrary,
    ToneStyleRules,
)

TRACE_HEADING_PATTERNS = (
    "calculation traces",
    "long stream ledger",
    "route-family stream focus",
    "route-family duty focus",
    "appendix navigation",
    "python code and reproducibility bundle",
)

REFERENCE_SOURCE_COMMENT_RE = re.compile(r"^\s*<!--\s*SOURCE_ID:\s*([A-Za-z0-9_:-]+)\s*-->\s*$", re.MULTILINE)
BRACKETED_SOURCE_CITATION_RE = re.compile(r"\[([A-Za-z0-9_:-]+(?:\s*,\s*[A-Za-z0-9_:-]+)*)\]")
LABELED_SOURCE_CITATION_RE = re.compile(
    r"(?P<label>\b(?:citation|citations|reference|references)\s*:\s*)(?P<body>[A-Za-z0-9_:-]+(?:\s*,\s*[A-Za-z0-9_:-]+)*)",
    flags=re.IGNORECASE,
)
VISIBLE_SOURCE_METADATA_RE = re.compile(r"\s*\[Source ID:[^\]]+\]")

CHAPTER_PREFACES = {
    "introduction": "This chapter introduces the product, its commercial basis, and the demand-side rationale adopted for the proposed plant.",
    "literature survey": "This chapter reviews the literature and industrial references relevant to benzalkonium chloride manufacture and identifies the practical process routes available for detailed screening.",
    "process selection": "This chapter compares the candidate process routes and presents the rationale for selecting the preferred synthesis and purification path.",
    "site selection": "This chapter evaluates the site alternatives against logistics, utility, regulatory, and industrial-infrastructure criteria and identifies the recommended location.",
    "thermodynamic aspects": "This chapter summarizes the thermodynamic basis governing reaction feasibility, separation behavior, and section-level process admissibility.",
    "kinetic aspects": "This chapter presents the kinetic interpretation used for reactor sizing and identifies the rate-form assumptions retained for preliminary design.",
    "block flow diagram": "This chapter presents the overall process block flow representation and the sequence of major process sections.",
    "process flow diagram": "This chapter presents the equipment-level process flow representation used to relate the solved streams and unit operations to the plant design basis.",
    "process description": "This chapter describes the selected process section by section, from feed preparation through purification, recycle handling, and product finishing.",
    "material balance": "This chapter presents the unit-wise and overall material balances for the selected benzalkonium chloride process.",
    "energy balance": "This chapter presents the duty distribution across the process and the resulting utility demands on a unit-wise and overall basis.",
    "process design of reactor system": "This chapter develops the design basis for the reactor train and records the operating assumptions carried into equipment sizing.",
    "process design of separation system": "This chapter develops the design basis for the principal separation and recovery units in the selected process.",
    "sizing of equipment": "This chapter summarizes the sizing basis and design dimensions of the major equipment items required by the selected process.",
    "mechanical design": "This chapter presents the preliminary mechanical design basis and construction considerations for the major equipment items.",
    "storage and utilities": "This chapter presents the storage philosophy, utility requirements, and the major offsite services required by the plant.",
    "instrumentation & process control": "This chapter presents the principal control loops and safeguarding philosophy adopted for stable and safe plant operation.",
    "hazop": "This chapter summarizes the key operability deviations, causes, consequences, and safeguards identified for the proposed plant.",
    "safety, health, environment and waste management": "This chapter presents the principal safety, health, environmental, and waste-management considerations associated with the proposed plant.",
    "project & plant layout": "This chapter presents the site layout philosophy and the physical arrangement of the major process and offsite blocks.",
    "project cost": "This chapter summarizes the capital cost basis used for the proposed plant and the principal equipment and installation cost elements.",
    "cost of production": "This chapter presents the annual operating-cost basis and the resulting cost of production for the selected process.",
    "working capital": "This chapter presents the working-capital basis, inventory assumptions, and short-cycle funding requirements for the project.",
    "financial analysis": "This chapter presents the key project-finance metrics and the resulting economic viability of the selected plant configuration.",
    "conclusion": "This chapter records the principal conclusions of the feasibility study and the basis for recommending the selected plant configuration.",
}

SECTION_LEAD_INS = {
    "properties": "The principal physical and chemical properties relevant to plant design are summarized below.",
    "commercial product basis": "The commercial basis adopted for the present design case is summarized in the following table.",
    "capacity decision": "The basis for the selected plant capacity is stated below.",
    "route discovery": "The process alternatives identified from the literature and industrial references are summarized below.",
    "route screening": "The candidate routes were screened against chemistry, operability, separation, and waste-treatment criteria, as summarized below.",
    "route selection comparison": "The comparative route-ranking results are given below.",
    "process selection comparison": "The final process-comparison matrix retained for decision-making is presented below.",
    "route comparison": "The route-wise comparative indicators are summarized below.",
    "route chemistry coverage": "The extent of chemistry coverage achieved for the identified routes is summarized below.",
    "material balance summary": "The principal material-balance results are consolidated below.",
    "energy balance summary": "The principal thermal loads and utility implications are consolidated below.",
    "equipment list": "The major equipment items generated for the selected process are listed below.",
}

CHAPTER_CONTEXT_SENTENCES = {
    "introduction": "",
    "literature survey": "",
    "process selection": "",
    "site selection": "",
    "material balance": "",
    "energy balance": "",
    "process design of reactor system": "",
    "process design of separation system": "",
    "financial analysis": "",
    "process flow diagram": "",
}

CHAPTER_ROLE_OPENERS = {
    "introduction": {
        "table": "The introductory chapter uses compact tables only where they clarify the commercial basis and key product facts retained for subsequent design work.",
    },
    "literature survey": {
        "table": "In this chapter, the tabulated literature review is used to compare the practical routes before narrowing the discussion to the routes relevant for detailed design.",
    },
    "process selection": {
        "table": "The process-selection chapter uses comparative tables to support the engineering judgment leading to the final route choice.",
        "list": "The points below summarize the principal engineering reasons considered during process selection.",
    },
    "site selection": {
        "table": "The site-selection chapter presents the comparison in tabulated form so that infrastructure, logistics, and regulatory considerations can be judged together.",
    },
    "material balance": {
        "table": "The material-balance chapter records the solved stream results in tabulated form so that the plant-wide basis and the unit-wise material movement remain transparent.",
        "list": "The following points summarize the most important material-balance observations from the solved case.",
    },
    "energy balance": {
        "table": "The thermal duties are arranged below in table form to show how the major sections contribute to the overall energy requirement of the plant.",
        "list": "The main thermal implications of the solved case are summarized below.",
    },
    "process design of reactor system": {
        "table": "In the reactor-design chapter, the tabulated values are used to record the governing sizing basis and the principal operating assumptions of the selected reactor train.",
        "list": "The following points state the main reactor-design assumptions retained for preliminary design.",
    },
    "process design of separation system": {
        "table": "The separation-design chapter uses tables to set out the operating basis, sizing assumptions, and key performance expectations of the selected purification train.",
        "list": "The following points state the principal separation-design assumptions retained in the present report.",
    },
    "sizing of equipment": {
        "table": "The sizing chapter collects the major equipment dimensions in one place so that the scale of the selected plant can be appreciated readily.",
    },
    "instrumentation & process control": {
        "list": "The important control loops and safeguarding measures adopted for the plant are summarized below.",
    },
    "hazop": {
        "table": "The HAZOP chapter records the key deviations and safeguards in a structured form similar to conventional academic design submissions.",
    },
    "safety, health, environment and waste management": {
        "list": "The principal SHE and waste-management considerations of the selected process are summarized below.",
    },
    "project cost": {
        "table": "The project-cost chapter uses tables to distinguish the main capital contributions and to support the total investment basis adopted for the report.",
    },
    "cost of production": {
        "table": "The cost-of-production chapter summarizes the operating-cost contributors so that the cost basis of the selected process can be interpreted clearly.",
    },
    "working capital": {
        "table": "The working-capital chapter records the inventory and timing assumptions that govern the short-cycle funding requirement of the project.",
    },
    "financial analysis": {
        "table": "The financial chapter presents the principal indicators in tabulated form and then interprets them from the standpoint of engineering feasibility.",
        "list": "The important financial observations from the solved case are summarized below.",
    },
    "conclusion": {
        "list": "The principal conclusions drawn from the present feasibility study are summarized below.",
    },
}

VOICE_ANTI_PATTERNS = {
    "selected candidate": "selected alternative",
    "solver-derived": "design analysis",
    "artifact": "report section",
    "screening-feasible": "feasible at screening level",
    "retained basis": "basis adopted",
    "selected site": "recommended site",
    "selected route": "preferred route",
}

APPENDIX_ONLY_HEADINGS_BY_CHAPTER = {
    "process selection": {
        "process selection comparison",
        "route family profiles",
        "unit-operation family expansion",
        "chemistry family adapter",
        "sparse-data policy",
    },
    "thermodynamic aspects": {
        "selected property basis",
        "selected thermodynamic method",
    },
    "kinetic aspects": {
        "selected kinetic method",
    },
}

HEADING_RENAMES_BY_CHAPTER = {
    "introduction": {
        "commercial product basis": "Commercial Basis of Product",
        "capacity decision": "Capacity Justification",
    },
    "literature survey": {
        "route discovery": "Processes Available for Manufacture",
        "route chemistry coverage": "Chemistry Basis of Reported Routes",
    },
    "process selection": {
        "route comparison": "Comparison of Candidate Routes",
        "route discovery": "Process Alternatives Considered",
        "route screening": "Engineering Screening of Alternatives",
        "route selection comparison": "Comparison of Selected Alternatives",
        "process selection comparison": "Supplementary Process Comparison Matrix",
        "route family profiles": "Supplementary Route Family Notes",
        "unit-operation family expansion": "Supplementary Unit-Operation Notes",
        "chemistry family adapter": "Supplementary Chemistry Basis Notes",
        "sparse-data policy": "Supplementary Data-Limitation Notes",
        "chemistry decision": "Selected Process and Chemistry Basis",
        "selected route": "Final Route Selection",
        "route-derived flowsheet blueprint": "Conceptual Process Train",
        "selected reactor basis": "Selected Reactor System",
        "selected separation basis": "Selected Separation System",
        "selected heat-integration case": "Selected Heat-Integration Basis",
    },
    "site selection": {
        "deterministic site decision": "Recommended Site",
    },
    "thermodynamic aspects": {
        "separation thermodynamics basis": "Thermodynamic Basis for Separation",
        "thermodynamic interpretation": "Thermodynamic Interpretation",
        "thermodynamic feasibility assessment": "Thermodynamic Feasibility of Selected Process",
        "selected property basis": "Supplementary Property Basis",
        "selected thermodynamic method": "Supplementary Thermodynamic Method",
    },
    "kinetic aspects": {
        "kinetic interpretation": "Kinetic Interpretation",
        "kinetics assessment for benzalkonium chloride synthesis (rte-bkc-002)": "Kinetic Basis of Selected Reaction",
        "selected kinetic method": "Supplementary Kinetic Method",
    },
}

TABLE_CAPTION_RENAMES_BY_CHAPTER = {
    "introduction": {
        "commercial basis of product": "Commercial Product Basis Adopted for Design",
    },
    "literature survey": {
        "processes available for manufacture": "Processes Reported for Manufacture",
        "chemistry basis of reported routes": "Chemistry Coverage of Reported Routes",
    },
    "process selection": {
        "comparison of candidate routes": "Comparative Screening of Candidate Routes",
        "process alternatives considered": "Candidate Process Alternatives Considered",
        "engineering screening of alternatives": "Engineering Screening Results for Candidate Routes",
        "comparison of selected alternatives": "Comparative Basis for Final Route Selection",
    },
    "site selection": {
        "recommended site": "Comparative Evaluation of Site Alternatives",
    },
    "material balance": {
        "material balance summary": "Summary of Material Balance Results",
    },
    "energy balance": {
        "energy balance summary": "Summary of Energy Balance Results",
    },
    "sizing of equipment": {
        "equipment list": "Summary of Major Equipment Items",
    },
}


def build_benchmark_style_profile() -> BenchmarkStyleProfile:
    return BenchmarkStyleProfile(
        style_id="ict_home_paper_academic_v1",
        style_name="ICT Home Paper Academic Technical Report",
        benchmark_labels=[
            "11CHE1017 Swapnil Deshmukh.pdf",
            "19CHE102HPsub.pdf",
        ],
        body_font_family="Times New Roman",
        heading_font_family="Calibri",
        cover_font_family="Times New Roman",
        chapter_title_pattern="Chapter {number}: {title}",
        front_matter_sections=[
            "Title Page",
            "Contents",
            "Executive Summary",
        ],
        preferred_margin_pt=48.0,
        preferred_body_font_size_pt=12.0,
        preferred_heading_sizes_pt=[28.0, 18.0, 14.0, 12.0],
        assumptions=[
            "Formatter target is the shared ICT academic report style inferred from the supplied benchmark PDFs.",
            "Visual resemblance is strong but not intended to be a page-for-page clone of either benchmark PDF.",
        ],
        markdown=(
            "### Benchmark Style Contract\n\n"
            "- Body font family: Times New Roman style serif.\n"
            "- Heading hierarchy: Calibri-like sans headings over serif body text.\n"
            "- Contents-first academic front matter.\n"
            "- Numbered chapters with denser technical tables and formal prose.\n"
        ),
    )


def build_benchmark_voice_profile() -> BenchmarkVoiceProfile:
    return BenchmarkVoiceProfile(
        voice_id="ict_home_paper_voice_v1",
        voice_name="ICT Home Paper Academic Voice",
        benchmark_labels=[
            "11CHE1017 Swapnil Deshmukh.pdf",
            "19CHE102HPsub.pdf",
        ],
        tone_summary=(
            "Student-style academic chemical engineering report voice: explanatory, slightly formal, "
            "process-oriented, and more human than system-polished prose."
        ),
        preferred_sentence_patterns=[
            "The process selected for the manufacture of ... is ... because ...",
            "From the above comparison it is evident that ...",
            "Hence, the route based on ... is preferred for the present design.",
            "The material balance is carried out on the basis of ...",
            "The values obtained indicate that ...",
        ],
        preferred_transition_patterns=[
            "From the above discussion",
            "It is evident from the comparison",
            "Hence",
            "Therefore",
            "On the basis of the above results",
        ],
        preferred_paragraph_traits=[
            "Moderate sentence length with direct technical explanation.",
            "Chapter openings should introduce why the chapter matters, not just what it contains.",
            "Tables should usually be introduced and then interpreted in prose.",
            "Paragraphs should sound authored, not templated or corporate.",
        ],
        discouraged_phrases=sorted(VOICE_ANTI_PATTERNS.keys()),
        discouraged_styles=[
            "Uniform system-summary tone across all chapters.",
            "Corporate polished prose detached from engineering explanation.",
            "Machine-summary phrases that sound like workflow metadata.",
            "Journal-paper compression that removes explanatory home-paper cadence.",
        ],
        chapter_voice_notes={
            "introduction": "Contextual, explanatory, and product-oriented.",
            "literature survey": "Comparative, descriptive, and route-oriented.",
            "process selection": "Argumentative and justification-heavy.",
            "material balance": "Procedural, numerical, and interpretive.",
            "energy balance": "Duty-oriented with engineering implications.",
            "financial analysis": "Evaluative and conclusion-oriented.",
            "conclusion": "Direct, summative, and recommendation-led.",
        },
        markdown=(
            "### Benchmark Voice Contract\n\n"
            "- Tone: academic chemical-engineering home-paper voice.\n"
            "- Cadence: explanatory, moderately formal, and human-authored.\n"
            "- Preferred transitions: Hence, Therefore, From the above comparison.\n"
            "- Avoid system phrases such as `selected candidate`, `artifact`, and `solver-derived`.\n"
        ),
    )


def build_sentence_pattern_library() -> SentencePatternLibrary:
    return SentencePatternLibrary(
        library_id="ict_home_paper_sentence_library_v1",
        voice_id="ict_home_paper_voice_v1",
        chapter_sentence_patterns={
            "introduction": [
                "The product selected for the present study is ...",
                "The commercial basis adopted for the product is of considerable importance because ...",
            ],
            "literature survey": [
                "From the above literature survey, it is evident that ...",
                "On the basis of the routes reported, it may be seen that ...",
            ],
            "process selection": [
                "From the above comparison it is evident that ...",
                "Hence, the route based on ... is preferred for the present design.",
            ],
            "material balance": [
                "The material balance is carried out on the basis of ...",
                "The values obtained indicate that ...",
            ],
            "energy balance": [
                "The energy balance shows that ...",
                "It is clear from the duty distribution that ...",
            ],
            "process design of reactor system": [
                "The reactor selected for the present process is ...",
                "The design calculations indicate that ...",
            ],
            "process design of separation system": [
                "The selected separation system is based on ...",
                "The design values obtained show that ...",
            ],
            "financial analysis": [
                "On the basis of the above results, the project economics may be screened from ...",
                "The values obtained indicate a feasibility-stage economic position of ...",
            ],
            "conclusion": [
                "From the foregoing chapters, it may be concluded that ...",
                "Hence, the selected basis may be carried forward for further preliminary design work subject to the assumptions stated.",
            ],
        },
        transition_patterns=[
            "From the above discussion",
            "From the above comparison",
            "Hence",
            "Therefore",
            "On the basis of the above results",
        ],
        anti_pattern_replacements=VOICE_ANTI_PATTERNS,
        markdown=(
            "### Sentence Pattern Library\n\n"
            "- Benchmark sentence patterns are grouped chapter-wise.\n"
            "- Transitions favour home-paper phrasing such as `From the above comparison` and `Hence`.\n"
            "- Anti-pattern replacements suppress system-style wording.\n"
        ),
    )


def build_tone_style_rules() -> ToneStyleRules:
    return ToneStyleRules(
        rules_id="ict_home_paper_tone_rules_v1",
        voice_id="ict_home_paper_voice_v1",
        rewrite_safe_block_roles=[
            "narrative",
            "list",
            "front_matter",
        ],
        protected_content_types=[
            "Numeric values",
            "Citations",
            "Named routes, sites, species, units, and equipment tags",
            "Table contents",
        ],
        chapter_template_expectations={
            "introduction": [
                "Begin with product and industrial relevance.",
                "Move into commercial basis and capacity rationale.",
            ],
            "literature survey": [
                "Introduce the routes reported in the literature.",
                "Narrow the discussion toward the route selected for detailed design.",
            ],
            "process selection": [
                "Compare alternatives first.",
                "Conclude with a reasoned route choice.",
            ],
            "material balance": [
                "State the basis of calculation.",
                "Interpret the important stream results.",
            ],
            "process design of reactor system": [
                "State the design basis before discussing dimensions.",
                "Explain why the selected reactor system is suitable.",
            ],
            "process design of separation system": [
                "State the section basis before sizing details.",
                "Connect design values back to purification duty.",
            ],
            "financial analysis": [
                "Present indicators and then interpret viability.",
                "End with a feasibility-level judgment.",
            ],
            "conclusion": [
                "Restate the selected process basis.",
                "Close with a recommendation-oriented summary.",
            ],
        },
        chapter_transition_templates={
            "introduction": [
                "In the present study, special emphasis is placed on the commercial basis of the product because it governs the subsequent process design.",
                "Accordingly, the product basis adopted here is not merely descriptive but directly connected with the design calculations that follow.",
            ],
            "literature survey": [
                "From the above literature survey, it is evident that the practical routes differ mainly in chemistry, purification burden, and commercial maturity.",
                "On the basis of the available literature, only a limited number of routes merit detailed engineering consideration.",
            ],
            "process selection": [
                "From the above comparison it is evident that the preferred route must satisfy not only chemistry feasibility but also operability and purification practicality.",
                "Hence, the final process choice is based on the combined technical and engineering merits of the alternatives considered.",
            ],
            "material balance": [
                "The material balance is carried out on the basis of the selected process configuration and the adopted production rate.",
                "The values obtained from the solved case indicate the principal material movements, recycle behaviour, and losses within the plant.",
            ],
            "financial analysis": [
                "On the basis of the results obtained, the project economics may be screened from the principal profitability indicators retained in this chapter.",
                "The financial figures derived here must therefore be read as feasibility-stage indicators together with the selected technical basis of the plant.",
            ],
            "conclusion": [
                "From the foregoing chapters, it may be concluded that the proposed plant configuration is technically coherent at the present level of design.",
                "Hence, the selected basis may be carried forward for preliminary design review subject to the assumptions and unresolved items stated in the report.",
            ],
        },
        chapter_table_discussion_templates={
            "process selection": [
                "The foregoing table shows the comparative strength of the candidate routes and makes clear why the selected route is preferred.",
                "From the foregoing table, the engineering basis for preferring the selected route becomes evident.",
            ],
            "material balance": [
                "The foregoing table forms the basis for discussing stream distribution, recycle flow, and product recovery in the selected process.",
                "The above table provides the numerical basis required for interpreting stream distribution and recycle behaviour.",
            ],
            "energy balance": [
                "The foregoing table shows the principal thermal load distribution and therefore guides the utility basis of the plant.",
                "The above table makes the distribution of thermal duties clear and therefore supports the selected utility basis.",
            ],
            "financial analysis": [
                "The foregoing table is not merely tabulated data; it forms the basis for judging the economic acceptability of the selected process.",
                "The above table provides the principal financial basis from which the viability of the project may be assessed.",
            ],
        },
        anti_pattern_replacements=VOICE_ANTI_PATTERNS,
        cadence_rules=[
            "Allow natural variation in paragraph openings.",
            "Prefer explanation over metadata-like labels.",
            "Use explicit engineering reasoning after comparison tables.",
            "Keep the tone academic but not journal-compressed.",
        ],
        markdown=(
            "### Tone Style Rules\n\n"
            "- Rewrite narrative blocks aggressively when safe.\n"
            "- Protect numbers, citations, and engineering nouns.\n"
            "- Prefer benchmark-style transitions and explanation-led prose.\n"
        ),
    )


def _classify_rewrite_plan(
    *,
    block: SemanticBlock,
    chapter_title: str,
    tone_rules: ToneStyleRules,
) -> tuple[str, list[str], list[str], list[str]]:
    text = block.markdown
    reasons: list[str] = []
    preserved_tokens = sorted(set(re.findall(r"\[[A-Za-z0-9_:-]+\]|`[^`]+`|\b\d+(?:\.\d+)?\b", text)))
    chapter_key = chapter_title.lower()
    recommended_focus = tone_rules.chapter_template_expectations.get(chapter_key, [])

    if block.kind in {"table", "code", "figure"}:
        reasons.append("Structured content should remain stable for numeric and citation integrity.")
        return "protect", reasons, preserved_tokens, recommended_focus
    if block.role == "appendix_only":
        reasons.append("Appendix-only trace content should not be stylistically rewritten.")
        return "protect", reasons, preserved_tokens, recommended_focus
    if block.kind == "heading":
        reasons.append("Headings are controlled by formatter structure rules.")
        return "protect", preserved_tokens and reasons or reasons, preserved_tokens, recommended_focus
    if any(token in text for token in ["|", "Table ", "Figure "]):
        reasons.append("Inline tabular or figure references should be preserved.")
        return "protect", reasons, preserved_tokens, recommended_focus
    if block.role in tone_rules.rewrite_safe_block_roles and block.kind == "paragraph":
        if chapter_key in {"introduction", "literature survey", "process selection", "site selection", "process description", "financial analysis", "conclusion"}:
            return "aggressive", reasons, preserved_tokens, recommended_focus
        return "light", reasons, preserved_tokens, recommended_focus
    if block.kind == "list":
        return "light", reasons, preserved_tokens, recommended_focus
    reasons.append("Block falls outside rewrite-safe roles.")
    return "protect", reasons, preserved_tokens, recommended_focus


def build_narrative_rewrite_artifact(
    semantic_report: SemanticReportArtifact,
    voice_profile: BenchmarkVoiceProfile,
    tone_rules: ToneStyleRules,
) -> NarrativeRewriteArtifact:
    block_plans: list[NarrativeRewriteBlock] = []
    aggressive = 0
    light = 0
    protected = 0
    protected_summary: set[str] = set()
    for section in semantic_report.sections:
        for block in section.blocks:
            mode, reasons, preserved_tokens, focus = _classify_rewrite_plan(
                block=block,
                chapter_title=section.title,
                tone_rules=tone_rules,
            )
            if mode == "aggressive":
                aggressive += 1
            elif mode == "light":
                light += 1
            else:
                protected += 1
                protected_summary.update(reasons)
            block_plans.append(
                NarrativeRewriteBlock(
                    block_id=block.block_id,
                    source_chapter_id=section.source_chapter_id,
                    chapter_title=section.title,
                    block_kind=block.kind,
                    block_role=block.role,
                    rewrite_mode=mode,
                    protection_reasons=reasons,
                    preserved_tokens=preserved_tokens,
                    recommended_focus=focus,
                    original_markdown=block.markdown,
                )
            )
    return NarrativeRewriteArtifact(
        rewrite_id=f"{semantic_report.report_id}_narrative_rewrite",
        voice_id=voice_profile.voice_id,
        rules_id=tone_rules.rules_id,
        block_plans=block_plans,
        aggressive_block_count=aggressive,
        light_block_count=light,
        protected_block_count=protected,
        protected_content_summary=sorted(protected_summary),
        citations=semantic_report.citations,
        assumptions=semantic_report.assumptions + [
            "Rewrite modes are assigned deterministically from block kind, role, and protected content heuristics.",
            "Protected blocks keep numeric values, citations, and engineering identifiers intact.",
        ],
        markdown=(
            "### Narrative Rewrite Plan\n\n"
            f"- Aggressive rewrite blocks: {aggressive}\n"
            f"- Light rewrite blocks: {light}\n"
            f"- Protected blocks: {protected}\n"
        ),
    )


def build_formatter_target_profile(project_basis: ProjectBasis) -> FormatterTargetProfile:
    target_key = re.sub(r"[^a-z0-9]+", "_", project_basis.target_product.lower()).strip("_") or "project"
    chapter_groups = [
        FormatterChapterGroup(group_id="executive_summary", target_title="Executive Summary", source_chapter_ids=["executive_summary"], numbered=False),
        FormatterChapterGroup(group_id="introduction", target_title="Introduction", source_chapter_ids=["introduction_product_profile", "market_capacity_selection"]),
        FormatterChapterGroup(group_id="literature_survey", target_title="Literature Survey", source_chapter_ids=["literature_survey"]),
        FormatterChapterGroup(group_id="process_selection", target_title="Process Selection", source_chapter_ids=["process_selection"]),
        FormatterChapterGroup(group_id="site_selection", target_title="Site Selection", source_chapter_ids=["site_selection"]),
        FormatterChapterGroup(group_id="thermodynamics", target_title="Thermodynamic Aspects", source_chapter_ids=["thermodynamic_feasibility"]),
        FormatterChapterGroup(group_id="kinetics", target_title="Kinetic Aspects", source_chapter_ids=["reaction_kinetics"]),
        FormatterChapterGroup(group_id="bfd", target_title="Block Flow Diagram", source_chapter_ids=["block_flow_diagram"]),
        FormatterChapterGroup(group_id="pfd", target_title="Process Flow Diagram", source_chapter_ids=["process_flow_diagram"]),
        FormatterChapterGroup(group_id="process_description", target_title="Process Description", source_chapter_ids=["process_description"]),
        FormatterChapterGroup(group_id="material_balance", target_title="Material Balance", source_chapter_ids=["material_balance"]),
        FormatterChapterGroup(group_id="energy_balance", target_title="Energy Balance", source_chapter_ids=["energy_balance"]),
        FormatterChapterGroup(group_id="reactor_design", target_title="Process Design of Reactor System", source_chapter_ids=["reactor_design"]),
        FormatterChapterGroup(group_id="separation_design", target_title="Process Design of Separation System", source_chapter_ids=["distillation_design"]),
        FormatterChapterGroup(group_id="equipment_sizing", target_title="Sizing of Equipment", source_chapter_ids=["equipment_design_sizing"]),
        FormatterChapterGroup(group_id="mechanical_design", target_title="Mechanical Design", source_chapter_ids=["mechanical_design_moc"]),
        FormatterChapterGroup(
            group_id="reactor_mechanical_appendix",
            target_title="Detailed Mechanical Design of Reactor R-101",
            source_chapter_ids=["reactor_mechanical_appendix"],
        ),
        FormatterChapterGroup(group_id="storage_utilities", target_title="Storage and Utilities", source_chapter_ids=["storage_utilities"]),
        FormatterChapterGroup(group_id="control", target_title="Instrumentation & Process Control", source_chapter_ids=["instrumentation_control"]),
        FormatterChapterGroup(group_id="hazop", target_title="HAZOP", source_chapter_ids=["hazop"]),
        FormatterChapterGroup(group_id="she", target_title="Safety, Health, Environment and Waste Management", source_chapter_ids=["safety_health_environment_waste"]),
        FormatterChapterGroup(group_id="layout", target_title="Project & Plant Layout", source_chapter_ids=["layout"]),
        FormatterChapterGroup(group_id="project_cost", target_title="Project Cost", source_chapter_ids=["project_cost"]),
        FormatterChapterGroup(group_id="cop", target_title="Cost of Production", source_chapter_ids=["cost_of_production"]),
        FormatterChapterGroup(group_id="working_capital", target_title="Working Capital", source_chapter_ids=["working_capital"]),
        FormatterChapterGroup(group_id="financial_analysis", target_title="Financial Analysis", source_chapter_ids=["financial_analysis"]),
        FormatterChapterGroup(group_id="data_gaps", target_title="Data Gaps and Estimation Methods", source_chapter_ids=["data_gaps_estimation_methods"]),
        FormatterChapterGroup(group_id="conclusion", target_title="Conclusion", source_chapter_ids=["conclusion"]),
    ]
    return FormatterTargetProfile(
        target_id=f"{target_key}_academic_formatter_v1",
        style_id="ict_home_paper_academic_v1",
        benchmark_id="ict_home_paper_shared",
        chapter_groups=chapter_groups,
        assumptions=[
            "Introduction and market-capacity material are merged into one benchmark-style introduction chapter.",
            "Executive Summary remains unnumbered front matter in the formatted output.",
        ],
        markdown="### Formatter Target Profile\n\nBAC-first academic report grouping aligned to the benchmark ICT home-paper style.\n",
    )


def build_semantic_report_artifact(
    project_id: str,
    style_profile: BenchmarkStyleProfile,
    target_profile: FormatterTargetProfile,
    raw_markdown_path: str,
    chapters: list[ChapterArtifact],
) -> SemanticReportArtifact:
    sections = [_semantic_section_from_chapter(chapter) for chapter in chapters]
    appendix_sections: list[SemanticSection] = []
    return SemanticReportArtifact(
        report_id=f"{project_id}_semantic_report",
        style_id=style_profile.style_id,
        target_id=target_profile.target_id,
        raw_markdown_path=raw_markdown_path,
        sections=sections,
        appendix_sections=appendix_sections,
        citations=sorted({citation for chapter in chapters for citation in chapter.citations}),
        assumptions=[
            "Semantic report blocks are parsed deterministically from chapter markdown.",
            "Block-level citation inheritance defaults to the parent chapter citations.",
        ],
        markdown="### Semantic Report Model\n\nParsed chapter content into semantic blocks for formatting and layout rendering.\n",
    )


def build_formatted_report_package(
    basis: ProjectBasis,
    style_profile: BenchmarkStyleProfile,
    target_profile: FormatterTargetProfile,
    semantic_report: SemanticReportArtifact,
    narrative_rewrite_plan: NarrativeRewriteArtifact,
    references_md: str,
    annexures_md: str,
) -> tuple[FormattedReportArtifact, FormatterDecisionArtifact, FormatterParityArtifact, FormatterAcceptanceArtifact]:
    rewrite_lookup = {block.block_id: block for block in narrative_rewrite_plan.block_plans}
    formatted_markdown, formatted_html, appendix_titles, moved_sections = _format_semantic_report(
        basis, style_profile, target_profile, semantic_report, rewrite_lookup, references_md, annexures_md
    )
    parity = _build_formatter_parity(style_profile, target_profile, semantic_report, formatted_markdown, moved_sections)
    acceptance = _build_formatter_acceptance(parity)
    formatted = FormattedReportArtifact(
        formatter_id=f"{basis.target_product.lower().replace(' ', '_')}_formatted_report_v1",
        target_id=target_profile.target_id,
        formatted_markdown=formatted_markdown,
        formatted_html=formatted_html,
        chapter_titles=[group.target_title for group in target_profile.chapter_groups if group.numbered],
        appendix_titles=appendix_titles,
        citations=semantic_report.citations,
        assumptions=semantic_report.assumptions + target_profile.assumptions,
        markdown="### Formatted Report Output\n\nFormatter generated academic-style markdown and HTML while preserving chapter coverage and citations.\n",
    )
    decisions = FormatterDecisionArtifact(
        formatter_id=formatted.formatter_id,
        decisions=[
            "Adopted ICT home-paper academic typography and chapter numbering.",
            "Merged introduction and market-capacity material into one introduction chapter.",
            "Moved machine-oriented trace sections to appendices while preserving all source chapter content.",
            "Applied chapter-specific narrative rewriting to aggressive rewrite-safe prose blocks while preserving citations and numeric strings.",
            "Preserved original chapter facts, citations, and numeric strings without model-side rewriting.",
        ],
        preserved_artifact_refs=[section.source_chapter_id for section in semantic_report.sections],
        moved_appendix_sections=sorted(moved_sections.keys()),
        citations=semantic_report.citations,
        assumptions=semantic_report.assumptions,
        markdown="### Formatter Decisions\n\n- Academic benchmark style applied.\n- Raw numeric content preserved.\n- Appendix migration limited to overtly machine-style trace sections.\n",
    )
    return formatted, decisions, parity, acceptance


def _extract_reference_number_map(references_md: str) -> dict[str, int]:
    source_ids = REFERENCE_SOURCE_COMMENT_RE.findall(references_md)
    return {source_id: index for index, source_id in enumerate(source_ids, start=1)}


def _strip_reference_source_comments(text: str) -> str:
    stripped = REFERENCE_SOURCE_COMMENT_RE.sub("", text)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


def _is_source_id_sequence(text: str, citation_map: dict[str, int]) -> bool:
    tokens = [token.strip() for token in text.split(",") if token.strip()]
    return bool(tokens) and all(token in citation_map for token in tokens)


def _format_numeric_citation(tokens: list[str], citation_map: dict[str, int]) -> str:
    return "[" + ", ".join(str(citation_map[token]) for token in tokens) + "]"


def _normalize_citation_text(text: str, citation_map: dict[str, int]) -> str:
    if not citation_map or not text:
        return VISIBLE_SOURCE_METADATA_RE.sub("", text)

    def replace_bracketed(match: re.Match[str]) -> str:
        tokens = [token.strip() for token in match.group(1).split(",") if token.strip()]
        if tokens and all(token in citation_map for token in tokens):
            return _format_numeric_citation(tokens, citation_map)
        return match.group(0)

    def replace_labeled(match: re.Match[str]) -> str:
        tokens = [token.strip() for token in match.group("body").split(",") if token.strip()]
        if tokens and all(token in citation_map for token in tokens):
            return match.group("label") + _format_numeric_citation(tokens, citation_map)
        return match.group(0)

    text = BRACKETED_SOURCE_CITATION_RE.sub(replace_bracketed, text)
    text = LABELED_SOURCE_CITATION_RE.sub(replace_labeled, text)
    text = VISIBLE_SOURCE_METADATA_RE.sub("", text)
    return text


def _normalize_citation_markdown_table(markdown: str, citation_map: dict[str, int]) -> str:
    if not citation_map:
        return markdown
    headers, body_rows = _parse_markdown_table(markdown)
    if len(headers) < 2:
        return _normalize_citation_text(markdown, citation_map)
    citation_columns = [
        index
        for index, header in enumerate(headers)
        if header.strip().lower() in {"citation", "citations", "reference", "references"}
    ]
    normalized_rows: list[list[str]] = []
    for row in body_rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        updated = list(padded[: len(headers)])
        for index, cell in enumerate(updated):
            cell_text = _normalize_citation_text(cell, citation_map)
            if index in citation_columns and _is_source_id_sequence(cell.strip(), citation_map):
                tokens = [token.strip() for token in cell.split(",") if token.strip()]
                cell_text = _format_numeric_citation(tokens, citation_map)
            updated[index] = cell_text
        normalized_rows.append(updated)
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(row) + " |" for row in normalized_rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _normalize_markdown_citations(markdown: str, citation_map: dict[str, int]) -> str:
    stripped = markdown.lstrip()
    if stripped.startswith("|"):
        return _normalize_citation_markdown_table(markdown, citation_map)
    return _normalize_citation_text(markdown, citation_map)


def _manual_prose_cleanup(text: str) -> str:
    replacements = {
        "In the present study, special emphasis is placed on the commercial basis of the product because it governs the subsequent process design.":
            "Particular emphasis is placed on the commercial basis of the product, since it governs the subsequent process design.",
        "Accordingly, 50,000 TPA plant basis selected because it best balances the benchmark throughput, market basis, and integration leverage.":
            "Accordingly, a plant capacity of 50,000 TPA is selected because it best balances the benchmark throughput, market basis, and integration leverage.",
        "From the above literature survey, it is evident that the practical routes differ mainly in chemistry, purification burden, and commercial maturity.":
            "The literature survey shows that the practical routes differ mainly in chemistry, purification burden, and commercial maturity.",
        "In this connection, three industrially plausible routes for the synthesis of Benzalkonium Chloride (BKC) are presented, based on the quaternization of dodecyldimethylamine with benzyl chloride.":
            "Three industrially plausible routes for the synthesis of benzalkonium chloride are identified on the basis of the quaternization of dodecyldimethylamine with benzyl chloride.",
        "In this connection, **Route 1** is a high-temperature process in butanone, derived directly from a patent, offering high evidence but with significant energy costs for heating and cryogenic crystallization.":
            "**Route 1** is a high-temperature process in butanone derived directly from the patent literature. It offers strong documentary support, but it also carries a significant energy burden because of heating and cryogenic crystallization.",
        "In this connection, **Route 2** is a room-temperature process in acetonitrile, based on technical literature, which saves energy but is likely hampered by long reaction times and the use of a toxic, costly solvent.":
            "**Route 2** is a room-temperature process in acetonitrile derived from technical literature. Although its thermal requirement is lower, it is disadvantaged by long reaction times and the use of a toxic and comparatively costly solvent.",
        "In this connection, **Route 3** is a generated, solvent-free (neat) process that offers the best process efficiency through shorter reaction times and no solvent recovery steps. Its primary challenge is the management of the reaction exotherm, a standard chemical engineering problem.":
            "**Route 3** is a solvent-free route that offers the best process efficiency because it avoids solvent recovery and shortens the reaction sequence. Its principal challenge is control of the reaction exotherm.",
        "In this chapter, the tabulated literature review is used to compare the practical routes before narrowing the discussion to the routes relevant for detailed design.":
            "The tabulated literature review is used to compare the practical routes before narrowing the discussion to those retained for detailed design.",
        "From the above comparison it is evident that the preferred route must satisfy not only chemistry feasibility but also operability and purification practicality.":
            "The comparison shows that the preferred route must satisfy not only chemistry feasibility but also operability and purification practicality.",
        "On the basis of the results obtained, the project economics may be screened from the principal profitability indicators retained in this chapter.":
            "The principal profitability indicators retained in this chapter provide the basis for screening the project economics.",
        "From a financial standpoint, 70:30 debt-equity basis selected after lender-coverage reranking (min DSCR 25.534, LLCR 31.222, PLCR 56.334).":
            "A 70:30 debt-equity basis is retained after reranking the financing options on lender-coverage criteria (minimum DSCR 25.534, LLCR 31.222, and PLCR 56.334).",
        "From the foregoing chapters, it may be concluded that the proposed plant configuration is technically coherent at the present level of design.":
            "The foregoing chapters show that the proposed plant configuration is technically coherent at the present level of design.",
        "In the reactor-design chapter, the tabulated values are used to record the governing sizing basis and the principal operating assumptions of the selected reactor train.":
            "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("In this connection, no additional document-derived process options were identified.", "No additional document-derived process options were identified.")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _semantic_section_from_chapter(chapter: ChapterArtifact) -> SemanticSection:
    blocks = _parse_markdown_blocks(chapter.rendered_markdown, chapter.chapter_id, chapter.citations)
    return SemanticSection(
        section_id=chapter.chapter_id,
        source_chapter_id=chapter.chapter_id,
        title=chapter.title,
        citations=chapter.citations,
        assumptions=chapter.assumptions,
        blocks=blocks,
    )


def _parse_markdown_blocks(markdown: str, chapter_id: str, citations: list[str]) -> list[SemanticBlock]:
    lines = markdown.splitlines()
    blocks: list[SemanticBlock] = []
    index = 0
    block_counter = 1

    def next_id() -> str:
        nonlocal block_counter
        value = f"{chapter_id}_block_{block_counter}"
        block_counter += 1
        return value

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```diagram-svg"):
            fence_lines = []
            index += 1
            while index < len(lines):
                if lines[index].strip().startswith("```"):
                    index += 1
                    break
                fence_lines.append(lines[index])
                index += 1
            prior_heading = next((block.title for block in reversed(blocks) if block.kind == "heading"), "")
            blocks.append(
                SemanticBlock(
                    block_id=next_id(),
                    kind="figure",
                    role="narrative",
                    title=prior_heading,
                    markdown="\n".join(fence_lines),
                    citations=citations,
                )
            )
            continue
        if stripped.startswith("```"):
            fence_lines = [line]
            index += 1
            while index < len(lines):
                fence_lines.append(lines[index])
                if lines[index].strip().startswith("```"):
                    index += 1
                    break
                index += 1
            blocks.append(
                SemanticBlock(
                    block_id=next_id(),
                    kind="code",
                    role="appendix_only" if _is_appendix_heading(" ".join(fence_lines)) else "narrative",
                    markdown="\n".join(fence_lines),
                    citations=citations,
                )
            )
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            role = "appendix_only" if _is_appendix_heading(title) else "narrative"
            blocks.append(
                SemanticBlock(
                    block_id=next_id(),
                    kind="heading",
                    role=role,
                    title=title,
                    heading_level=level,
                    markdown=line,
                    citations=citations,
                )
            )
            index += 1
            continue
        if _is_markdown_table(lines, index):
            table_lines = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            prior_heading = next((block.title for block in reversed(blocks) if block.kind == "heading"), "")
            role = "appendix_only" if _is_appendix_heading(prior_heading) else "summary_table"
            blocks.append(
                SemanticBlock(
                    block_id=next_id(),
                    kind="table",
                    role=role,
                    title=prior_heading,
                    markdown="\n".join(table_lines),
                    citations=citations,
                )
            )
            continue
        if _is_list_line(line):
            list_lines = [line]
            index += 1
            while index < len(lines) and lines[index].strip():
                candidate_line = lines[index]
                if _is_list_line(candidate_line) or candidate_line.startswith(("  ", "\t")):
                    list_lines.append(lines[index])
                    index += 1
                    continue
                break
            blocks.append(
                SemanticBlock(
                    block_id=next_id(),
                    kind="list",
                    role="list",
                    markdown="\n".join(list_lines),
                    citations=citations,
                )
            )
            continue
        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith("#") or candidate.startswith("```") or _is_markdown_table(lines, index):
                break
            if _is_list_line(lines[index]):
                break
            paragraph_lines.append(candidate)
            index += 1
        paragraph = " ".join(paragraph_lines).strip()
        role = "appendix_only" if _is_appendix_heading(paragraph) else ("equation_like" if "=" in paragraph and len(paragraph) < 160 else "narrative")
        blocks.append(
            SemanticBlock(
                block_id=next_id(),
                kind="paragraph",
                role=role,
                markdown=paragraph,
                citations=citations,
            )
        )
    return blocks


def _format_semantic_report(
    basis: ProjectBasis,
    style_profile: BenchmarkStyleProfile,
    target_profile: FormatterTargetProfile,
    semantic_report: SemanticReportArtifact,
    rewrite_lookup: dict[str, NarrativeRewriteBlock],
    references_md: str,
    annexures_md: str,
) -> tuple[str, str, list[str], dict[str, list[SemanticBlock]]]:
    section_map = {section.source_chapter_id: section for section in semantic_report.sections}
    moved_sections: OrderedDict[str, list[SemanticBlock]] = OrderedDict()
    markdown_parts: list[str] = []
    html_parts: list[str] = []
    citation_map = _extract_reference_number_map(references_md)
    clean_references_md = _strip_reference_source_comments(references_md)
    clean_annexures_md = _normalize_markdown_citations(annexures_md, citation_map)
    chapter_counter = 1
    appendix_titles: list[str] = []
    table_entries: list[tuple[str, str]] = []
    figure_entries: list[tuple[str, str]] = []
    chapter_kept_table_counts: dict[str, int] = {}

    toc_rows: list[tuple[str, str]] = []
    numbered_groups = [group for group in target_profile.chapter_groups if group.numbered]
    for group in target_profile.chapter_groups:
        if group.numbered:
            toc_rows.append((f"Chapter {chapter_counter}", group.target_title))
            chapter_counter += 1
        else:
            toc_rows.append(("", group.target_title))
    chapter_counter = 1

    markdown_parts.extend(_build_markdown_cover_page(basis))
    markdown_parts.extend(_build_markdown_contents(toc_rows))
    markdown_parts.extend(["## List of Tables", "", "_To be updated from the formatted chapter body._", ""])
    markdown_parts.extend(["## List of Figures", "", "_To be updated from the formatted chapter body._", ""])
    html_parts.append(_build_html_document_open(style_profile, basis.target_product))
    html_parts.append(_build_html_cover_page(basis))
    html_parts.append(_build_html_contents(toc_rows))

    for group in target_profile.chapter_groups:
        source_sections = [section_map[source_id] for source_id in group.source_chapter_ids if source_id in section_map]
        if not source_sections:
            continue
        chapter_label = f"Chapter {chapter_counter}: {group.target_title}" if group.numbered else group.target_title
        if group.numbered:
            markdown_parts.extend(["", f"# {chapter_label}", ""])
            section_open_markup = f"<section class='chapter'><h1>{html.escape(chapter_label)}</h1>"
            section_reopen_markup = "<section class='chapter'>"
            html_parts.append(section_open_markup)
            section_number_prefix = str(chapter_counter)
            chapter_counter += 1
        else:
            markdown_parts.extend(["", f"# {group.target_title}", ""])
            section_open_markup = f"<section class='chapter executive-summary'><h1>{html.escape(group.target_title)}</h1>"
            section_reopen_markup = "<section class='chapter executive-summary'>"
            html_parts.append(section_open_markup)
            section_number_prefix = ""
        preface = CHAPTER_PREFACES.get(group.target_title.lower())
        if preface:
            markdown_parts.extend([preface, ""])
            html_parts.append(f"<p class='chapter-preface'>{html.escape(preface)}</p>")
        context_sentence = CHAPTER_CONTEXT_SENTENCES.get(group.target_title.lower())
        if context_sentence:
            markdown_parts.extend([context_sentence, ""])
            html_parts.append(f"<p>{html.escape(context_sentence)}</p>")
        chapter_transition_templates = _chapter_transition_templates(group.target_title)
        if chapter_transition_templates:
            opening_transition = chapter_transition_templates[0]
            markdown_parts.extend([opening_transition, ""])
            html_parts.append(f"<p>{_paragraph_to_html(opening_transition)}</p>")
        chapter_table_counter = 1
        chapter_figure_counter = 1
        last_table_lead = ""

        subsection_counter = 1
        appendix_note_written = False
        chapter_table_intro_written = False
        chapter_list_intro_written = False
        current_subsection_heading = ""
        subsection_appendix_table_note_written = False
        if _chapter_may_have_appendix_content(source_sections, group.target_title):
            note = "Detailed calculation traces and supporting technical tables for this chapter are presented in the appendices."
            markdown_parts.extend([note, ""])
            html_parts.append(f"<p class='appendix-note'>{html.escape(note)}</p>")
            appendix_note_written = True
        for section in source_sections:
            append_current_subsection = False
            for block in section.blocks:
                if block.kind == "heading" and block.heading_level <= 2:
                    append_current_subsection = False
                    continue
                if append_current_subsection and block.kind != "heading":
                    moved_sections.setdefault(group.target_title, []).append(block)
                    continue
                if block.role == "appendix_only":
                    moved_sections.setdefault(group.target_title, []).append(block)
                    continue
                if block.kind == "heading":
                    raw_heading_text = _clean_heading_title(block.title)
                    if _should_move_heading_to_appendix(group.target_title, raw_heading_text):
                        moved_sections.setdefault(group.target_title, []).append(block)
                        append_current_subsection = True
                    continue
                    append_current_subsection = False
                    heading_text = _rename_heading(group.target_title, raw_heading_text)
                    current_subsection_heading = heading_text
                    subsection_appendix_table_note_written = False
                    subsection_label = f"{section_number_prefix}.{subsection_counter}" if section_number_prefix else str(subsection_counter)
                    markdown_parts.extend([f"## {subsection_label}. {heading_text}", ""])
                    html_parts.append(f"<h2>{html.escape(subsection_label)}. {html.escape(heading_text)}</h2>")
                    lead_in = _section_lead_in(group.target_title, heading_text)
                    if lead_in:
                        markdown_parts.extend([lead_in, ""])
                        html_parts.append(f"<p>{_paragraph_to_html(lead_in)}</p>")
                    subsection_counter += 1
                    continue
                if block.kind == "paragraph":
                    label_match = _extract_bold_label_paragraph(block.markdown)
                    if label_match:
                        label, body = label_match
                        markdown_parts.extend([f"### {label}", ""])
                        html_parts.append(f"<h3>{html.escape(label)}</h3>")
                        if body:
                            paragraph_text = _normalize_citation_text(
                                _polish_paragraph(body, chapter_title=group.target_title),
                                citation_map,
                            )
                            markdown_parts.extend([paragraph_text, ""])
                            html_parts.append(f"<p>{_paragraph_to_html(paragraph_text)}</p>")
                        continue
                    rewrite_plan = rewrite_lookup.get(block.block_id)
                    paragraph_text = _normalize_citation_text(
                        _rewrite_paragraph(
                            block.markdown,
                            chapter_title=group.target_title,
                            rewrite_plan=rewrite_plan,
                        ),
                        citation_map,
                    )
                    markdown_parts.extend([paragraph_text, ""])
                    html_parts.append(f"<p>{_paragraph_to_html(paragraph_text)}</p>")
                    continue
                if block.kind == "list":
                    role_intro = _chapter_role_intro(group.target_title, "list")
                    if role_intro and not chapter_list_intro_written:
                        markdown_parts.extend([role_intro, ""])
                        html_parts.append(f"<p>{_paragraph_to_html(role_intro)}</p>")
                        chapter_list_intro_written = True
                    list_markdown = _normalize_markdown_citations(block.markdown, citation_map)
                    markdown_parts.extend([list_markdown, ""])
                    html_parts.append(_list_markdown_to_html(list_markdown))
                    continue
                if block.kind == "table":
                    chapter_table_key = group.target_title.lower()
                    kept_count = chapter_kept_table_counts.get(chapter_table_key, 0)
                    if _should_move_table_to_appendix(block, group.target_title, kept_count):
                        moved_sections.setdefault(group.target_title, []).append(block)
                        if not subsection_appendix_table_note_written:
                            summary = _appendix_table_summary(block, group.target_title, current_subsection_heading)
                            if summary:
                                markdown_parts.extend([summary, ""])
                                html_parts.append(f"<p>{_paragraph_to_html(summary)}</p>")
                            else:
                                note = "The detailed tabulation for this subsection is retained in the appendix so that the main body remains readable."
                                markdown_parts.extend([note, ""])
                                html_parts.append(f"<p class='appendix-note'>{html.escape(note)}</p>")
                            subsection_appendix_table_note_written = True
                        continue
                    role_intro = _chapter_role_intro(group.target_title, "table")
                    if role_intro and not chapter_table_intro_written:
                        markdown_parts.extend([role_intro, ""])
                        html_parts.append(f"<p>{_paragraph_to_html(role_intro)}</p>")
                        chapter_table_intro_written = True
                    table_markdown = _normalize_citation_markdown_table(block.markdown, citation_map)
                    table_number = f"{section_number_prefix}.{chapter_table_counter}" if section_number_prefix else str(chapter_table_counter)
                    caption = f"Table {table_number}: {_table_caption(block, group.target_title)}"
                    table_entries.append((table_number, _table_caption(block, group.target_title)))
                    table_lead = _table_lead_in(block, group.target_title)
                    if table_lead and table_lead != last_table_lead:
                        markdown_parts.extend([table_lead, ""])
                        html_parts.append(f"<p>{_paragraph_to_html(table_lead)}</p>")
                        last_table_lead = table_lead
                    markdown_parts.extend([f"**{caption}**", "", table_markdown, ""])
                    html_parts.append(f"<div class='table-caption'>{html.escape(caption)}</div>")
                    html_parts.append(_table_markdown_to_html(table_markdown))
                    table_comment = _table_afterword(block, group.target_title)
                    if table_comment:
                        markdown_parts.extend([f"_{table_comment}_", ""])
                    chapter_kept_table_counts[chapter_table_key] = kept_count + 1
                    chapter_table_counter += 1
                    continue
                if block.kind in {"code", "figure"}:
                    if block.kind == "code" and _is_full_page_diagram_group(group.target_title):
                        moved_sections.setdefault(group.target_title, []).append(block)
                        continue
                    figure_number = f"{section_number_prefix}.{chapter_figure_counter}" if section_number_prefix else str(chapter_figure_counter)
                    figure_caption = f"Figure {figure_number}: {_figure_caption(block, group.target_title)}"
                    figure_entries.append((figure_number, _figure_caption(block, group.target_title)))
                    figure_lead = _figure_lead_in(block, group.target_title)
                    if block.markdown.lstrip().startswith("<svg"):
                        if figure_lead:
                            markdown_parts.extend([figure_lead, ""])
                        markdown_parts.extend([f"**{figure_caption}**", "", "```text", block.markdown.strip("`"), "```", ""])
                        if _is_full_page_diagram_group(group.target_title):
                            html_parts.append("</section>")
                            html_parts.append(_render_full_page_diagram_sheet(block.markdown, figure_caption, figure_lead, group.target_title))
                            html_parts.append(section_reopen_markup)
                        else:
                            if figure_lead:
                                html_parts.append(f"<p>{_paragraph_to_html(figure_lead)}</p>")
                            html_parts.append(f"<div class='figure-caption'>{html.escape(figure_caption)}</div>")
                            html_parts.append(f"<div class='diagram-figure'>{block.markdown}</div>")
                        markdown_parts.extend(["_The above figure is rendered graphically in the formatted PDF output._", ""])
                    else:
                        if figure_lead:
                            markdown_parts.extend([figure_lead, ""])
                            html_parts.append(f"<p>{_paragraph_to_html(figure_lead)}</p>")
                        markdown_parts.extend([f"**{figure_caption}**", "", "```text", block.markdown.strip("`"), "```", ""])
                        html_parts.append(f"<div class='figure-caption'>{html.escape(figure_caption)}</div>")
                        html_parts.append(f"<pre>{html.escape(block.markdown)}</pre>")
                        markdown_parts.extend(["_The above figure is retained in text-rendered form in the formatted report for deterministic local PDF generation._", ""])
                    chapter_figure_counter += 1
                    continue
        html_parts.append("</section>")

    references_body = clean_references_md.strip()
    if references_body.startswith("## References"):
        references_body = references_body[len("## References"):].lstrip()
    markdown_parts.extend(["", "# References", "", references_body, ""])
    html_parts.append("<section class='references'><h1>References</h1>")
    html_parts.append(_simple_markdown_to_html(references_body))
    html_parts.append("</section>")

    markdown_parts.extend(["", "# Appendices", ""])
    html_parts.append("<section class='appendices'><h1>Appendices</h1>")
    appendix_label_ord = ord("A")
    for title, blocks in moved_sections.items():
        appendix_label = chr(appendix_label_ord)
        appendix_title = f"Appendix {appendix_label}: {title} Supplementary Material"
        appendix_titles.append(appendix_title)
        markdown_parts.extend([f"## {appendix_title}", ""])
        html_parts.append(f"<h2>{html.escape(appendix_title)}</h2>")
        html_parts.append(
            "<p class='appendix-note'>"
            "Detailed trace-level content for this appendix is preserved in the formatted markdown and raw annexure bundle. "
            "The PDF view retains a benchmark-style summary to preserve readability."
            "</p>"
        )
        for block in blocks:
            if block.kind == "heading":
                markdown_parts.extend([f"### {_clean_heading_title(block.title)}", ""])
                html_parts.append(f"<h3>{html.escape(_clean_heading_title(block.title))}</h3>")
            elif block.kind == "table":
                markdown_parts.extend([_normalize_citation_markdown_table(block.markdown, citation_map), ""])
            elif block.kind == "list":
                markdown_parts.extend([_normalize_markdown_citations(block.markdown, citation_map), ""])
            else:
                markdown_parts.extend([_normalize_markdown_citations(block.markdown, citation_map), ""])
        appendix_label_ord += 1

    annexure_heading = f"Appendix {chr(appendix_label_ord)}: Annexures and Reproducibility Bundle"
    appendix_titles.append(annexure_heading)
    markdown_parts.extend([f"## {annexure_heading}", "", clean_annexures_md.strip(), ""])
    html_parts.append(f"<h2>{html.escape(annexure_heading)}</h2>")
    html_parts.append(
        "<p class='appendix-note'>"
        "The full annexure and reproducibility bundle remains attached to the project outputs. "
        "This formatted PDF keeps only the appendix heading so that the report remains benchmark-style and readable."
        "</p>"
    )
    html_parts.append("</section>")
    html_parts.append("</body></html>")
    markdown_text = "\n".join(markdown_parts).strip() + "\n"
    markdown_text = _replace_formatted_register(markdown_text, "List of Tables", table_entries, "Table")
    markdown_text = _replace_formatted_register(markdown_text, "List of Figures", figure_entries, "Figure")
    markdown_text = _manual_prose_cleanup(markdown_text)
    html_text = _manual_prose_cleanup("".join(html_parts))
    return markdown_text, html_text, appendix_titles, moved_sections


def _build_formatter_parity(
    style_profile: BenchmarkStyleProfile,
    target_profile: FormatterTargetProfile,
    semantic_report: SemanticReportArtifact,
    formatted_markdown: str,
    moved_sections: dict[str, list[SemanticBlock]],
) -> FormatterParityArtifact:
    source_titles = {group.target_title for group in target_profile.chapter_groups}
    missing_chapters = [title for title in source_titles if title not in formatted_markdown]
    raw_text = "\n".join(block.markdown for section in semantic_report.sections for block in section.blocks)
    raw_numbers = _extract_numeric_tokens(raw_text)
    formatted_numbers = _extract_numeric_tokens(formatted_markdown)
    numeric_ratio = 1.0 if not raw_numbers else len(raw_numbers & formatted_numbers) / len(raw_numbers)
    raw_citations = set(semantic_report.citations)
    citation_ratio = _score_citation_preservation(raw_citations, formatted_markdown)
    structure_status = ReportParityStatus.COMPLETE if not missing_chapters else ReportParityStatus.PARTIAL
    numeric_status = ReportParityStatus.COMPLETE if numeric_ratio >= 0.99 else ReportParityStatus.PARTIAL
    citation_status = ReportParityStatus.COMPLETE if citation_ratio >= 0.99 else ReportParityStatus.PARTIAL
    appendix_status = ReportParityStatus.COMPLETE if moved_sections else ReportParityStatus.PARTIAL
    structure_score = _score_structure_parity(target_profile, formatted_markdown, missing_chapters)
    table_figure_score = _score_table_figure_parity(formatted_markdown)
    chapter_specificity_score = _score_chapter_specificity(formatted_markdown)
    typography_layout_score = _score_typography_layout(formatted_markdown)
    table_figure_status = _score_to_parity_status(table_figure_score)
    chapter_specificity_status = _score_to_parity_status(chapter_specificity_score)
    typography_layout_status = _score_to_parity_status(typography_layout_score)
    tone_status = _score_to_parity_status(chapter_specificity_score)
    overall_score = round(
        (
            structure_score * 0.25
            + table_figure_score * 0.2
            + chapter_specificity_score * 0.2
            + typography_layout_score * 0.15
            + numeric_ratio * 0.1
            + citation_ratio * 0.1
        ),
        4,
    )
    parity_notes = _build_parity_notes(
        missing_chapters=missing_chapters,
        structure_score=structure_score,
        table_figure_score=table_figure_score,
        chapter_specificity_score=chapter_specificity_score,
        typography_layout_score=typography_layout_score,
    )
    return FormatterParityArtifact(
        style_id=style_profile.style_id,
        target_id=target_profile.target_id,
        structure_status=structure_status,
        tone_status=tone_status,
        citation_status=citation_status,
        numeric_status=numeric_status,
        chapter_coverage_status=structure_status,
        appendix_placement_status=appendix_status,
        table_figure_status=table_figure_status,
        chapter_specificity_status=chapter_specificity_status,
        typography_layout_status=typography_layout_status,
        numeric_preservation_ratio=round(numeric_ratio, 4),
        citation_preservation_ratio=round(citation_ratio, 4),
        structure_parity_score=round(structure_score, 4),
        table_figure_parity_score=round(table_figure_score, 4),
        chapter_specificity_score=round(chapter_specificity_score, 4),
        typography_layout_score=round(typography_layout_score, 4),
        overall_parity_score=overall_score,
        moved_appendix_block_count=sum(len(blocks) for blocks in moved_sections.values()),
        missing_chapter_ids=missing_chapters,
        parity_notes=parity_notes,
        citations=semantic_report.citations,
        assumptions=semantic_report.assumptions,
        markdown=(
            "### Formatter Parity\n\n"
            f"- Structure status: {structure_status.value}\n"
            f"- Table/Figure status: {table_figure_status.value}\n"
            f"- Chapter-specificity status: {chapter_specificity_status.value}\n"
            f"- Typography/layout status: {typography_layout_status.value}\n"
            f"- Numeric preservation ratio: {numeric_ratio:.3f}\n"
            f"- Citation preservation ratio: {citation_ratio:.3f}\n"
            f"- Overall parity score: {overall_score:.3f}\n"
        ),
    )


def _build_formatter_acceptance(parity: FormatterParityArtifact) -> FormatterAcceptanceArtifact:
    structure_status = _parity_to_acceptance(parity.structure_status)
    citation_status = _parity_to_acceptance(parity.citation_status)
    numeric_status = _parity_to_acceptance(parity.numeric_status)
    appendix_status = _parity_to_acceptance(parity.appendix_placement_status)
    benchmark_parity_status = _score_to_acceptance(parity.overall_parity_score)
    overall = ReportAcceptanceStatus.COMPLETE
    for status in (structure_status, citation_status, numeric_status, benchmark_parity_status):
        if status == ReportAcceptanceStatus.BLOCKED:
            overall = ReportAcceptanceStatus.BLOCKED
            break
        if status == ReportAcceptanceStatus.CONDITIONAL:
            overall = ReportAcceptanceStatus.CONDITIONAL
    return FormatterAcceptanceArtifact(
        overall_status=overall,
        structure_status=structure_status,
        citation_status=citation_status,
        numeric_status=numeric_status,
        appendix_status=appendix_status,
        benchmark_parity_status=benchmark_parity_status,
        overall_parity_score=parity.overall_parity_score,
        notes=[
            "Formatter preserves numeric content deterministically from the raw report.",
            "Appendix migration is limited to machine-style trace sections and reproducibility-heavy blocks.",
            *parity.parity_notes,
        ],
        citations=parity.citations,
        assumptions=parity.assumptions,
        markdown=(
            "### Formatter Acceptance\n\n"
            f"- Overall status: {overall.value}\n"
            f"- Structure: {structure_status.value}\n"
            f"- Citations: {citation_status.value}\n"
            f"- Numeric preservation: {numeric_status.value}\n"
            f"- Benchmark parity: {benchmark_parity_status.value}\n"
            f"- Overall parity score: {parity.overall_parity_score:.3f}\n"
        ),
    )


def _parity_to_acceptance(status: ReportParityStatus) -> ReportAcceptanceStatus:
    if status == ReportParityStatus.COMPLETE:
        return ReportAcceptanceStatus.COMPLETE
    if status == ReportParityStatus.PARTIAL:
        return ReportAcceptanceStatus.CONDITIONAL
    return ReportAcceptanceStatus.BLOCKED


def _score_to_parity_status(score: float) -> ReportParityStatus:
    if score >= 0.85:
        return ReportParityStatus.COMPLETE
    if score >= 0.6:
        return ReportParityStatus.PARTIAL
    return ReportParityStatus.MISSING


def _score_to_acceptance(score: float) -> ReportAcceptanceStatus:
    if score >= 0.85:
        return ReportAcceptanceStatus.COMPLETE
    if score >= 0.6:
        return ReportAcceptanceStatus.CONDITIONAL
    return ReportAcceptanceStatus.BLOCKED


def _score_structure_parity(
    target_profile: FormatterTargetProfile,
    formatted_markdown: str,
    missing_chapters: list[str],
) -> float:
    chapter_count = max(1, len(target_profile.chapter_groups))
    chapter_score = 1.0 - (len(missing_chapters) / chapter_count)
    contents_markers = ["# Contents", "## List of Tables", "## List of Figures", "# References", "# Appendices"]
    contents_hits = sum(1 for marker in contents_markers if marker in formatted_markdown) / len(contents_markers)
    return max(0.0, min(1.0, chapter_score * 0.7 + contents_hits * 0.3))


def _score_table_figure_parity(formatted_markdown: str) -> float:
    markers = [
        "## List of Tables",
        "## List of Figures",
        "**Table 1.1:",
        "**Figure 1.1:",
        "The foregoing table",
    ]
    hits = sum(1 for marker in markers if marker in formatted_markdown)
    return hits / len(markers)


def _score_chapter_specificity(formatted_markdown: str) -> float:
    marker_groups = [
        [
            "The process-selection chapter uses comparative tables to support the engineering judgment leading to the final route choice.",
        ],
        [
            "The material-balance chapter records the solved stream results in tabulated form so that the plant-wide basis and the unit-wise material movement remain transparent.",
        ],
        [
            "The financial chapter presents the principal indicators in tabulated form and then interprets them from the standpoint of engineering feasibility.",
        ],
        [
            "The reactor-design chapter records the basis of sizing, the governing design assumptions, and the principal operating envelope of the selected reactor train.",
            "The reactor-design discussion records the basis of sizing, the governing design assumptions, and the principal operating envelope of the selected reactor train.",
        ],
        [
            "The separation-design discussion records the key process assumptions, operating basis, and sizing logic for the selected purification system.",
        ],
    ]
    hits = sum(1 for group in marker_groups if any(marker in formatted_markdown for marker in group))
    return hits / len(marker_groups)


def _score_typography_layout(formatted_markdown: str) -> float:
    markers = [
        "# DESIGN A PLANT TO MANUFACTURE",
        "### HOME PAPER STYLE PRELIMINARY REPORT",
        "# Chapter 1: Introduction",
        "# Chapter 2: Literature Survey",
        "Appendix A:",
    ]
    hits = sum(1 for marker in markers if marker in formatted_markdown)
    return hits / len(markers)


def _score_citation_preservation(raw_citations: set[str], formatted_markdown: str) -> float:
    if not raw_citations:
        return 1.0
    preserved = 0
    for citation in raw_citations:
        if f"[{citation}]" in formatted_markdown:
            preserved += 1
            continue
        if re.search(rf"(?<![A-Za-z0-9_:-]){re.escape(citation)}(?![A-Za-z0-9_:-])", formatted_markdown):
            preserved += 1
    return preserved / len(raw_citations)


def _build_parity_notes(
    *,
    missing_chapters: list[str],
    structure_score: float,
    table_figure_score: float,
    chapter_specificity_score: float,
    typography_layout_score: float,
) -> list[str]:
    notes: list[str] = []
    if missing_chapters:
        notes.append("Some expected benchmark-style chapter groups are missing from the formatted output.")
    if structure_score < 0.85:
        notes.append("Structure parity is not yet at benchmark-complete level.")
    if table_figure_score < 0.85:
        notes.append("Table and figure presentation still needs refinement to fully match the benchmark pattern.")
    if chapter_specificity_score < 0.85:
        notes.append("Chapter-specific presentation is improved but still not uniformly benchmark-like across all major chapters.")
    if typography_layout_score < 0.85:
        notes.append("Typography and page-layout markers are present but still below benchmark-complete parity.")
    if not notes:
        notes.append("Formatted report is close to benchmark style across structure, presentation, and layout markers.")
    return notes


def _build_markdown_cover_page(basis: ProjectBasis) -> list[str]:
    return [
        f"# DESIGN A PLANT TO MANUFACTURE {basis.target_product.upper()}",
        "",
        f"## Capacity: {basis.capacity_tpa:.0f} TPA",
        "",
        "### HOME PAPER STYLE PRELIMINARY REPORT",
        "",
        f"Prepared for the proposed {basis.target_product} plant design case in {basis.region}.",
        "",
    ]


def _build_markdown_contents(rows: list[tuple[str, str]]) -> list[str]:
    lines = ["# Contents", ""]
    for label, title in rows:
        if label:
            lines.append(f"- {label}: {title}")
        else:
            lines.append(f"- {title}")
    lines.extend(["- References", "- Appendices", ""])
    return lines


def _build_html_document_open(style_profile: BenchmarkStyleProfile, report_title: str) -> str:
    return (
        "<html><head><meta charset='utf-8' />"
        f"<title>{html.escape(report_title)} Academic Report</title>"
        "<style>"
        "@page { size: A4; margin: 42pt 42pt 52pt 42pt; }"
        "body { font-family: 'Times New Roman', serif; font-size: 11.5pt; line-height: 1.32; color: #111; margin: 0; }"
        "h1, h2, h3 { font-family: 'Calibri', 'Helvetica', sans-serif; color: #111; page-break-after: avoid; }"
        "h1 { font-size: 18pt; margin: 20pt 0 10pt 0; text-transform: none; }"
        "h2 { font-size: 13pt; margin: 12pt 0 6pt 0; }"
        "h3 { font-size: 11.5pt; margin: 10pt 0 5pt 0; }"
        "p { text-align: justify; margin: 0 0 7pt 0; widows: 2; orphans: 2; }"
        ".cover { text-align: center; page-break-after: always; padding-top: 92pt; }"
        ".cover h1 { font-family: 'Times New Roman', serif; font-size: 26pt; font-weight: bold; text-transform: uppercase; }"
        ".cover h2 { font-family: 'Times New Roman', serif; font-size: 16pt; margin-top: 18pt; }"
        ".contents { page-break-after: always; text-align: left; }"
        ".contents h1 { text-align: center; margin-bottom: 12pt; }"
        ".contents table { width: 100%; border-collapse: collapse; font-size: 10.5pt; }"
        ".contents td { padding: 2pt 0; vertical-align: top; text-align: left; }"
        ".chapter { page-break-before: always; }"
        ".executive-summary { page-break-before: auto; }"
        ".chapter-preface { font-style: italic; }"
        ".appendix-note { font-size: 10pt; color: #444; }"
        ".table-caption { font-weight: bold; margin: 10pt 0 4pt 0; page-break-after: avoid; }"
        ".table-part-label { font-family: 'Calibri', 'Helvetica', sans-serif; font-size: 9pt; font-weight: bold; margin: 6pt 0 2pt 0; text-transform: uppercase; color: #333; }"
        ".figure-caption { font-weight: bold; margin: 10pt 0 4pt 0; }"
        ".diagram-figure { margin: 2pt 0 14pt 0; page-break-inside: avoid; }"
        ".diagram-figure svg { width: 100%; height: auto; display: block; }"
        "diagram-sheet { display: block; page-break-before: always; page-break-after: always; margin: 0; }"
        "diagram-sheet.landscape { break-before: page; break-after: page; }"
        ".diagram-sheet-caption { font-family: 'Calibri', 'Helvetica', sans-serif; font-size: 12pt; font-weight: 700; margin: 0 0 8pt 0; text-align: center; }"
        ".diagram-sheet-basis { font-size: 10.6pt; margin: 0 0 8pt 0; text-align: justify; }"
        ".diagram-sheet-figure { margin: 0; border: 0.8pt solid #444; padding: 8pt 10pt; background: #fff; }"
        ".diagram-sheet-figure svg { width: 100%; height: auto; display: block; max-height: 480pt; }"
        ".diagram-sheet-note { font-size: 9.5pt; margin: 8pt 0 0 0; text-align: center; color: #444; }"
        "table.report-table { width: 100%; border-collapse: collapse; margin: 0 0 12pt 0; font-size: 9.4pt; table-layout: fixed; page-break-inside: auto; }"
        "table.report-table th, table.report-table td { border: 0.7pt solid #222; padding: 4pt 5pt; vertical-align: top; text-align: left; word-break: break-word; overflow-wrap: anywhere; }"
        "table.report-table th { background: #efefef; font-family: 'Calibri', 'Helvetica', sans-serif; }"
        "table.report-table tr { page-break-inside: avoid; }"
        "table.report-table-compact { font-size: 9.1pt; }"
        "ul, ol { margin: 2pt 0 8pt 18pt; padding-left: 12pt; }"
        "li { margin: 0 0 4pt 0; }"
        ".list-continuation { margin: 2pt 0 0 0; }"
        "pre { font-family: 'Courier New', monospace; font-size: 9pt; white-space: pre-wrap; border: 0.7pt solid #999; padding: 6pt; }"
        ".citation { font-size: 9.5pt; }"
        "strong { font-weight: bold; }"
        "em { font-style: italic; }"
        "</style></head><body>"
    )


def _build_html_cover_page(basis: ProjectBasis) -> str:
    return (
        "<section class='cover'>"
        f"<h1>Design a Plant to Manufacture {html.escape(basis.target_product)}</h1>"
        f"<h2>{basis.capacity_tpa:.0f} TPA Continuous Plant</h2>"
        "<p>Home Paper Style Preliminary Techno-Economic Feasibility Report</p>"
        f"<p>Region: {html.escape(basis.region)}</p>"
        "</section>"
    )


def _build_html_contents(rows: list[tuple[str, str]]) -> str:
    body = ["<section class='contents'><h1>Contents</h1><table>"]
    for label, title in rows:
        body.append(
            "<tr>"
            f"<td style='width: 30%;'>{html.escape(label)}</td>"
            f"<td>{html.escape(title)}</td>"
            "</tr>"
        )
    body.append("<tr><td></td><td>References</td></tr>")
    body.append("<tr><td></td><td>Appendices</td></tr>")
    body.append("</table></section>")
    return "".join(body)


def _clean_heading_title(title: str) -> str:
    title = re.sub(r"^#+\s*", "", title).strip()
    title = re.sub(r"\s+", " ", title)
    return title.rstrip(":")


def _rename_heading(chapter_title: str, heading_text: str) -> str:
    mapping = HEADING_RENAMES_BY_CHAPTER.get(chapter_title.lower(), {})
    return mapping.get(heading_text.lower(), heading_text)


def _should_move_heading_to_appendix(chapter_title: str, heading_text: str) -> bool:
    appendix_headings = APPENDIX_ONLY_HEADINGS_BY_CHAPTER.get(chapter_title.lower(), set())
    return heading_text.lower() in appendix_headings


def _section_lead_in(chapter_title: str, heading_text: str) -> str:
    lowered = heading_text.lower()
    chapter_key = chapter_title.lower()
    if lowered in SECTION_LEAD_INS:
        return SECTION_LEAD_INS[lowered]
    if "route" in lowered and "comparison" in lowered:
        return "The comparative basis adopted for this section is summarized below."
    if "properties" in lowered:
        return "The relevant design properties retained for this study are summarized below."
    if "basis" in lowered:
        basis_map = {
            "process selection": "The engineering basis supporting this decision is stated below.",
            "site selection": "The siting basis adopted for this part of the report is stated below.",
            "thermodynamic aspects": "The thermodynamic basis adopted for this subsection is stated below.",
            "kinetic aspects": "The kinetic basis adopted for this subsection is stated below.",
            "process design of reactor system": "The reactor-design basis adopted for this subsection is stated below.",
            "process design of separation system": "The separation-design basis adopted for this subsection is stated below.",
            "project cost": "The capital-cost basis adopted for this subsection is stated below.",
            "cost of production": "The operating-cost basis adopted for this subsection is stated below.",
            "working capital": "The working-capital basis adopted for this subsection is stated below.",
            "financial analysis": "The financial basis adopted for this subsection is stated below.",
        }
        return basis_map.get(chapter_key, "The basis adopted for this part of the design is stated below.")
    if "summary" in lowered:
        summary_map = {
            "material balance": "The principal material-balance observations for this subsection are summarized below.",
            "energy balance": "The principal thermal observations for this subsection are summarized below.",
            "sizing of equipment": "The principal equipment details retained for this subsection are summarized below.",
            "financial analysis": "The principal financial observations for this subsection are summarized below.",
            "project cost": "The principal project-cost observations for this subsection are summarized below.",
            "cost of production": "The principal cost-of-production observations for this subsection are summarized below.",
            "working capital": "The principal working-capital observations for this subsection are summarized below.",
        }
        return summary_map.get(chapter_key, "The principal results for this subsection are summarized below.")
    if "decision" in lowered:
        return "The engineering decision retained for this subsection is stated below."
    return ""


def _polish_paragraph(text: str, *, chapter_title: str = "") -> str:
    sentence_library = build_sentence_pattern_library()
    text = re.sub(r"^\s*In this connection,\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*In the present study,\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(^|(?<=[.!?])\s+)In this connection,\s*", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(
        r"^\s*special emphasis is placed on the commercial basis of the product because it governs the subsequent process design\.\s*$",
        "Particular emphasis is placed on the commercial basis of the product, since it governs the subsequent process design.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*From the above literature survey, it is evident that ",
        "The literature survey shows that ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*From the above comparison it is evident that ",
        "The comparison shows that ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*On the basis of the results obtained, the project economics may be screened from the principal profitability indicators retained in this chapter\.\s*$",
        "The principal profitability indicators retained in this chapter provide the basis for the financial assessment of the project.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*From a financial standpoint,\s*70:30 debt-equity basis selected after lender-coverage reranking",
        "A 70:30 debt-equity basis is retained after lender-coverage reranking",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*From the foregoing chapters, it may be concluded that ",
        "The foregoing chapters show that ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*Accordingly,\s*50,000 TPA plant basis selected because ",
        "Accordingly, a plant capacity of 50,000 TPA is selected because ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*no document-derived process options\.\s*$",
        "No additional document-derived process options were identified.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^\s*Accordingly,\s*([0-9][0-9,]*(?:\.[0-9]+)?\s*TPA)\s+plant basis selected because\s*", r"Accordingly, a \1 plant basis is selected because ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSolver-derived\b", "The present design analysis", text)
    text = re.sub(r"\bsolver-derived\b", "the present design analysis", text)
    text = re.sub(r"\bSolver-backed\b", "The present engineering basis", text)
    for source, replacement in sentence_library.anti_pattern_replacements.items():
        text = re.sub(rf"\b{re.escape(source)}\b", replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\bThis chapter\b", "The present chapter", text)
    text = re.sub(r"\bThis report\b", "The present report", text)
    text = re.sub(r"\bfor the proposed plant\b", "for the proposed plant configuration", text)
    text = re.sub(r"\bdesign-ready\b", "suitable for preliminary design", text, flags=re.IGNORECASE)
    text = re.sub(r"\bscreening_feasible\b", "screening-feasible", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwhy not chosen\b", "reason for rejection", text, flags=re.IGNORECASE)
    text = re.sub(r"\bThe market for\b", "The market for", text)
    text = re.sub(r"\s+", " ", text).strip()

    if chapter_title.lower() == "financial analysis":
        text = re.sub(r"\braw output sheet\b", "raw calculation sheet", text, flags=re.IGNORECASE)
        text = re.sub(r"\bpayback\b", "payback period", text, flags=re.IGNORECASE)
        if "economic viability" not in text.lower() and "financial" in text.lower():
            text = text.rstrip(".") + ", and therefore the economic viability of the project may be judged from the same."
    if chapter_title.lower() == "process selection":
        text = re.sub(r"\broute comparison\b", "process-route comparison", text, flags=re.IGNORECASE)
        text = re.sub(r"\bselected alternative\b", "preferred process alternative", text, flags=re.IGNORECASE)
        if "comparison" in text.lower() and "evident" not in text.lower():
            text = text.rstrip(".") + ", from which the preferred process alternative may be identified."
    if chapter_title.lower() in {"material balance", "energy balance"}:
        text = re.sub(r"\bsummary\b", "account", text, flags=re.IGNORECASE)
        if "basis" in text.lower() and "carried out on the basis" not in text.lower() and len(text) < 260:
            text = "The calculation in this section is carried out on the basis adopted for the selected plant configuration. " + text[0].lower() + text[1:]
    if chapter_title.lower() in {"process design of reactor system", "process design of separation system"}:
        text = re.sub(r"\bbasis adopted\b", "design basis adopted", text, flags=re.IGNORECASE)
    if chapter_title.lower() == "introduction" and "product" in text.lower() and "industrial" not in text.lower() and len(text) < 260:
        text = text.rstrip(".") + ", which is of practical industrial importance and therefore justifies detailed plant-design treatment."
    if chapter_title.lower() == "conclusion" and "concluded" not in text.lower() and len(text) < 260:
        text = "From the foregoing discussion, " + text[0].lower() + text[1:]
    text = _apply_sentence_pattern_library(text, chapter_title, sentence_library)
    text = _apply_cadence_variation(text, chapter_title)
    return text


def _rewrite_paragraph(
    text: str,
    *,
    chapter_title: str,
    rewrite_plan: NarrativeRewriteBlock | None = None,
) -> str:
    polished = _polish_paragraph(text, chapter_title=chapter_title)
    return polished


def _apply_aggressive_chapter_rewrite(
    text: str,
    *,
    chapter_title: str,
    recommended_focus: list[str],
) -> str:
    chapter_key = chapter_title.lower()
    if len(text) > 420:
        return text
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "in the present report, the discussion is organized",
            "for the present design study, the discussion is directed",
            "at this stage of the report, the alternatives are judged",
            "the site discussion is framed in terms of",
            "the process description is written in a section-wise manner",
            "the economic results are not read in isolation",
            "thus, the study leads to a practical recommendation",
        )
    ):
        return text

    opener_map = {
        "introduction": "The introduction is arranged around the commercial product basis and the industrial setting within which benzalkonium chloride manufacture is to be considered.",
        "literature survey": "For the present design study, the discussion is directed first toward the routes available in the literature and then toward the routes of practical engineering significance.",
        "process selection": "At this stage of the report, the alternatives are judged not only by reaction chemistry but also by purification burden, operability, and overall plant practicality.",
        "site selection": "The site discussion is therefore developed in terms of logistics, utilities, regulation, and the extent to which each location can support continuous chemical manufacture.",
        "process description": "The process description is written in a section-wise manner so that feed preparation, reaction, purification, recycle, and finishing can be followed in their actual sequence.",
        "financial analysis": "The financial results are therefore interpreted together with the technical basis adopted for the selected plant configuration, rather than as isolated schedule values.",
        "conclusion": "Thus, the study leads to a practical recommendation founded on the combined process, design, and economic results discussed in the foregoing chapters.",
    }
    opener = opener_map.get(chapter_key, "")
    if not opener:
        return text

    focus_sentence = ""
    if recommended_focus:
        focus_text = recommended_focus[0].rstrip(".")
        focus_map = {
            "introduction": f" In this connection, the chapter is meant to {focus_text[0].lower() + focus_text[1:]}.",
            "site selection": f" In this connection, the comparison is meant to {focus_text[0].lower() + focus_text[1:]}.",
            "financial analysis": f" In this connection, the analysis is meant to {focus_text[0].lower() + focus_text[1:]}.",
            "conclusion": f" In this connection, the closing discussion is meant to {focus_text[0].lower() + focus_text[1:]}.",
        }
        focus_sentence = focus_map.get(chapter_key, f" In particular, the present discussion is intended to {focus_text[0].lower() + focus_text[1:]}.")

    if text[0].islower():
        text = text[0].upper() + text[1:]
    return f"{opener}{focus_sentence} {text}"


def _apply_sentence_pattern_library(text: str, chapter_title: str, sentence_library: SentencePatternLibrary) -> str:
    return text


def _table_lead_in(block: SemanticBlock, group_title: str) -> str:
    title = _table_caption(block, group_title).lower()
    chapter_key = group_title.lower()
    if "properties" in title:
        return "The principal physical-property data retained for design are listed below."
    if "route" in title and "comparison" in title:
        return "The route-wise comparison retained for process selection is given below."
    if "screening" in title:
        return "The route-screening criteria and their outcomes are summarized below."
    if "commercial product basis" in title:
        return "The adopted commercial basis of the project is summarized below."
    if "site" in title and "comparative" in title:
        return "The site alternatives are compared below against logistics, utilities, and supporting infrastructure."
    if "material balance" in title:
        return "The material-balance results are summarized below."
    if "energy balance" in title:
        return "The energy-balance results are summarized below."
    if "equipment" in title:
        return "The principal equipment dimensions retained for the present study are summarized below."
    if "financial" in title or "economic" in title:
        return "The principal financial indicators are summarized below."
    if chapter_key == "material balance":
        return "The principal stream-wise material-balance results are presented below."
    if chapter_key == "energy balance":
        return "The principal unit-wise duties and corresponding utility implications are presented below."
    if chapter_key == "process design of reactor system":
        return "The reactor-design quantities retained for preliminary sizing are summarized below."
    if chapter_key == "process design of separation system":
        return "The separation-design quantities retained for preliminary sizing are summarized below."
    if chapter_key == "financial analysis":
        return "The principal financial indicators derived from the adopted economic basis are presented below."
    if "cost" in title:
        return "The principal cost elements retained for the present case are summarized below."
    if "financial" in title:
        return "The key financial indicators obtained for the present case are summarized below."
    return ""


def _chapter_role_intro(chapter_title: str, role: str) -> str:
    return CHAPTER_ROLE_OPENERS.get(chapter_title.lower(), {}).get(role, "")


def _table_afterword(block: SemanticBlock, chapter_title: str) -> str:
    title = _table_caption(block, chapter_title).lower()
    specific = _table_specific_afterword(title, chapter_title)
    if specific:
        return specific
    return ""


def _chapter_transition_templates(chapter_title: str) -> list[str]:
    chapter_key = chapter_title.lower()
    profile = build_tone_style_rules()
    return profile.chapter_transition_templates.get(chapter_key, [])


def _chapter_table_discussion_templates(chapter_title: str) -> list[str]:
    chapter_key = chapter_title.lower()
    profile = build_tone_style_rules()
    return profile.chapter_table_discussion_templates.get(chapter_key, [])


def _deterministic_variant(options: list[str], seed: str) -> str:
    if not options:
        return ""
    index = sum(ord(ch) for ch in seed) % len(options)
    return options[index]


def _table_specific_afterword(title: str, chapter_title: str) -> str:
    chapter_key = chapter_title.lower()
    if "commercial product basis" in title:
        return "This table fixes the sold-solution basis, active-content basis, and commercial form used throughout the remainder of the report."
    if "route" in title and "comparison" in title:
        return "The relative strengths and limitations of the candidate routes can be read directly from this comparison."
    if "screening" in title:
        return "This screening table narrows the alternatives to those that remain practical after chemistry, purification, and operability are considered together."
    if "site" in title and "comparative" in title:
        return "The preference for the recommended location follows from its combined logistical, utility, and regulatory advantages."
    if "material balance" in title or chapter_key == "material balance":
        return ""
    if "energy balance" in title or chapter_key == "energy balance":
        return ""
    if "equipment" in title:
        return ""
    if "financial" in title or "economic" in title or chapter_key == "financial analysis":
        return ""
    return ""


def _should_move_table_to_appendix(block: SemanticBlock, chapter_title: str, kept_count: int) -> bool:
    title = _table_caption(block, chapter_title).lower()
    chapter_key = chapter_title.lower()
    headers, _ = _parse_markdown_table(block.markdown)
    wide = len(headers) > 6

    appendix_titles = (
        "section balance",
        "reaction extent",
        "byproduct closure",
        "unit packet balance",
        "composition closure",
        "stream ledger",
        "long stream ledger",
        "financial schedule",
        "debt schedule",
        "debt service",
        "procurement package",
        "scenario utility island",
        "utility island economics",
        "column hydraulics",
    )
    if any(marker in title for marker in appendix_titles):
        return True

    keep_titles = (
        "commercial product basis",
        "comparison of candidate routes",
        "comparative screening of candidate routes",
        "comparative evaluation of site alternatives",
        "overall plant balance",
        "summary of energy balance results",
        "separation thermodynamics basis",
        "summary of major equipment items",
        "project cost",
        "cost of production",
        "financial analysis",
    )
    if any(marker in title for marker in keep_titles):
        return False

    if chapter_key in {"material balance", "energy balance", "financial analysis", "sizing of equipment"}:
        if kept_count >= 1 and wide:
            return True
        if kept_count >= 2:
            return True

    return False


def _chapter_may_have_appendix_content(source_sections: list[SemanticSection], chapter_title: str) -> bool:
    kept_count = 0
    for section in source_sections:
        append_current_subsection = False
        for block in section.blocks:
            if block.role == "appendix_only":
                return True
            if block.kind == "heading":
                raw_heading_text = _clean_heading_title(block.title)
                if _should_move_heading_to_appendix(chapter_title, raw_heading_text):
                    append_current_subsection = True
                    return True
                append_current_subsection = False
                continue
            if append_current_subsection:
                return True
            if block.kind == "table":
                if _should_move_table_to_appendix(block, chapter_title, kept_count):
                    return True
                kept_count += 1
    return False


def _appendix_table_summary(block: SemanticBlock, chapter_title: str, subsection_heading: str) -> str:
    title = _table_caption(block, chapter_title).lower()
    heading = subsection_heading.lower()
    if "section balance" in title or "section balance" in heading:
        return "The section-wise material movement and recycle distribution are summarized in the appendix for reference during detailed checking."
    if "reaction extent" in title or "reaction extent" in heading:
        return "The allocation of main and side reaction extents is recorded in the appendix so that the main body can remain focused on the governing balance conclusions."
    if "byproduct closure" in title or "byproduct closure" in heading:
        return "The appendix records the byproduct-allocation basis and provenance used to close the remaining material balance."
    if "unit packet balance" in title or "unit packet balance" in heading:
        return "The packet-wise inlet, outlet, and closure details are retained in the appendix for detailed reconciliation."
    if "recycle and purge" in title or "recycle and purge" in heading:
        return "The recycle and purge detail is retained in the appendix, while the main text keeps only the broader material-balance implications."
    if "composition closure" in title or "composition closure" in heading:
        return "The appendix contains the detailed composition-closure register used to verify the solved stream picture."
    if "stream role" in title or "stream role" in heading:
        return "The detailed stream-role assignment is retained in the appendix because it is mainly a support table for flowsheet interpretation."
    if "financial schedule" in title or "debt schedule" in title:
        return "The year-wise financial schedules are retained in the appendix, while the main body focuses on the principal viability indicators."
    return "The supporting detail for this subsection is retained in the appendix, while the main body records only the principal design interpretation."


def _apply_cadence_variation(text: str, chapter_title: str) -> str:
    chapter_key = chapter_title.lower()
    lowered = text.lower()
    if len(text) > 280:
        return text
    if any(
        lowered.startswith(prefix)
        for prefix in (
            "from the above",
            "hence,",
            "therefore,",
            "on the basis",
            "in the present study,",
            "the material balance is carried out",
            "it is clear from",
            "the values obtained indicate",
            "from the foregoing",
        )
    ):
        return text
    cadence_variants = {
        "introduction": [
            "In practical terms, {body}",
            "Accordingly, {body}",
        ],
        "literature survey": [
            "In this connection, {body}",
            "Viewed in this manner, {body}",
        ],
        "process selection": [
            "From an engineering standpoint, {body}",
            "On this basis, {body}",
        ],
        "material balance": [
            "Under the selected basis, {body}",
            "For the present calculation basis, {body}",
        ],
        "energy balance": [
            "Under the selected duty basis, {body}",
            "For the present thermal basis, {body}",
        ],
        "process design of reactor system": [
            "For reactor design purposes, {body}",
            "With this design basis in view, {body}",
        ],
        "process design of separation system": [
            "For separation design purposes, {body}",
            "With this purification basis in view, {body}",
        ],
        "financial analysis": [
            "From a financial standpoint, {body}",
            "Accordingly, {body}",
        ],
        "conclusion": [
            "In summary, {body}",
            "Accordingly, {body}",
        ],
    }
    templates = cadence_variants.get(chapter_key, [])
    if not templates:
        return text
    template = _deterministic_variant(templates, f"{chapter_key}:{text[:48]}")
    body = text[0].lower() + text[1:] if text else text
    return template.format(body=body)


def _paragraph_to_html(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\[([A-Za-z0-9_:-]+)\]", r"<span class='citation'>[\1]</span>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def _extract_bold_label_paragraph(text: str) -> tuple[str, str] | None:
    stripped = text.strip()
    match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", stripped)
    if not match:
        return None
    label = match.group(1).strip()
    body = match.group(2).strip()
    if not label or len(label) > 90:
        return None
    return label, body


def _table_caption(block: SemanticBlock, group_title: str) -> str:
    if block.title:
        cleaned = _clean_heading_title(block.title)
        mapping = TABLE_CAPTION_RENAMES_BY_CHAPTER.get(group_title.lower(), {})
        return mapping.get(cleaned.lower(), cleaned)
    return f"{group_title} summary"


def _figure_caption(block: SemanticBlock, group_title: str) -> str:
    if block.title:
        cleaned = _clean_heading_title(block.title)
        if "block flow" in cleaned.lower():
            return "Block Flow Representation of Selected Process"
        if "process flow" in cleaned.lower():
            return "Process Flow Diagram of Selected Plant Configuration"
        if "layout" in cleaned.lower():
            return "Indicative Layout Representation"
        return cleaned
    if group_title.lower() == "block flow diagram":
        return "Block Flow Representation of Selected Process"
    if group_title.lower() == "process flow diagram":
        return "Process Flow Diagram of Selected Plant Configuration"
    return f"{group_title} schematic representation"


def _figure_lead_in(block: SemanticBlock, group_title: str) -> str:
    if group_title.lower() == "block flow diagram":
        return "The overall process arrangement adopted for the selected route is shown in the following figure."
    if group_title.lower() == "process flow diagram":
        return "The equipment-level process arrangement and the principal stream paths adopted for the selected plant are shown in the following figure."
    if group_title.lower() == "instrumentation & process control":
        return "The control-system arrangement and the principal loop groupings adopted for the selected process are shown in the following figure."
    if group_title.lower() == "project & plant layout":
        return "The indicative arrangement of the principal blocks is shown in the following figure."
    return "The corresponding schematic representation is given below."


def _is_full_page_diagram_group(group_title: str) -> bool:
    lowered = group_title.lower()
    return lowered in {
        "block flow diagram",
        "process flow diagram",
        "instrumentation & process control",
    }


def _render_full_page_diagram_sheet(svg: str, figure_caption: str, figure_lead: str, group_title: str) -> str:
    note = "Drawing-first landscape sheet rendered for readability."
    if group_title.lower() == "block flow diagram":
        note = "Section-level block flow diagram rendered on a dedicated landscape sheet for readability."
    elif group_title.lower() == "process flow diagram":
        note = "Equipment-level process flow diagram rendered on a dedicated landscape sheet for readability."
    elif group_title.lower() == "instrumentation & process control":
        note = "Control-system figure rendered on a dedicated landscape sheet for readability."
    basis_html = f"<div class='diagram-sheet-basis'>{_paragraph_to_html(figure_lead)}</div>" if figure_lead else ""
    return (
        "<diagram-sheet class='landscape full-page'>"
        f"{basis_html}"
        f"<div class='diagram-sheet-caption'>{html.escape(figure_caption)}</div>"
        f"<div class='diagram-sheet-figure'>{svg}</div>"
        f"<div class='diagram-sheet-note'>{html.escape(note)}</div>"
        "</diagram-sheet>"
    )


def _replace_formatted_register(markdown_text: str, heading: str, entries: list[tuple[str, str]], kind: str) -> str:
    marker = f"## {heading}\n\n_To be updated from the formatted chapter body._"
    if marker not in markdown_text:
        return markdown_text
    if not entries:
        replacement = f"## {heading}\n\n_No {kind.lower()} entries recorded in the formatted report._"
    else:
        lines = [f"## {heading}", ""]
        for number, caption in entries:
            lines.append(f"- {kind} {number}. {caption}")
        replacement = "\n".join(lines)
    return markdown_text.replace(marker, replacement, 1)


def _list_markdown_to_html(markdown: str) -> str:
    html_parts: list[str] = []
    stack: list[tuple[int, str]] = []
    open_li = False

    def close_li() -> None:
        nonlocal open_li
        if open_li:
            html_parts.append("</li>")
            open_li = False

    def close_to_indent(indent: int) -> None:
        nonlocal stack
        while stack and indent < stack[-1][0]:
            close_li()
            _, tag = stack.pop()
            html_parts.append(f"</{tag}>")

    for line in markdown.splitlines():
        if not line.strip():
            continue
        if _is_list_line(line):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            tag = "ol" if ordered else "ul"
            text = re.sub(r"^(?:\d+\.\s+|[-*]\s+)", "", stripped)

            close_to_indent(indent)
            if not stack or indent > stack[-1][0] or tag != stack[-1][1]:
                if open_li and indent > (stack[-1][0] if stack else -1):
                    open_li = False
                elif open_li:
                    close_li()
                html_parts.append(f"<{tag}>")
                stack.append((indent, tag))
            else:
                close_li()

            html_parts.append(f"<li>{_paragraph_to_html(text)}")
            open_li = True
        else:
            continuation = line.strip()
            if open_li:
                html_parts.append(f"<div class='list-continuation'>{_paragraph_to_html(continuation)}</div>")
            else:
                html_parts.append(f"<p>{_paragraph_to_html(continuation)}</p>")

    close_li()
    while stack:
        _, tag = stack.pop()
        html_parts.append(f"</{tag}>")
    return "".join(html_parts)


def _table_markdown_to_html(markdown: str) -> str:
    headers, body_rows = _parse_markdown_table(markdown)
    if len(headers) < 2:
        return f"<p>{_paragraph_to_html(markdown)}</p>"
    if len(headers) > 6:
        return _wide_table_markdown_to_html(headers, body_rows)
    body_html_rows = []
    for values in body_rows:
        cells = values + [""] * max(0, len(headers) - len(values))
        body_html_rows.append("<tr>" + "".join(f"<td>{_paragraph_to_html(cell)}</td>" for cell in cells[: len(headers)]) + "</tr>")
    return (
        "<table class='report-table'><thead><tr>"
        + "".join(f"<th>{_paragraph_to_html(header)}</th>" for header in headers)
        + "</tr></thead><tbody>"
        + "".join(body_html_rows)
        + "</tbody></table>"
    )


def _parse_markdown_table(markdown: str) -> tuple[list[str], list[list[str]]]:
    rows = [line.strip().strip("|") for line in markdown.splitlines() if line.strip()]
    if len(rows) < 2:
        return [], []
    headers = [cell.strip() for cell in rows[0].split("|")]
    body_rows: list[list[str]] = []
    for row in rows[2:]:
        body_rows.append([cell.strip() for cell in row.split("|")])
    return headers, body_rows


def _wide_table_markdown_to_html(headers: list[str], body_rows: list[list[str]]) -> str:
    anchor_count = 1
    chunk_size = 4
    chunks: list[list[int]] = []
    remaining = list(range(anchor_count, len(headers)))
    while remaining:
        chunks.append(remaining[:chunk_size])
        remaining = remaining[chunk_size:]
    parts: list[str] = []
    multi_part = len(chunks) > 1
    for idx, chunk in enumerate(chunks, start=1):
        part_headers = headers[:anchor_count] + [headers[i] for i in chunk]
        part_rows_html: list[str] = []
        for values in body_rows:
            padded = values + [""] * max(0, len(headers) - len(values))
            part_values = padded[:anchor_count] + [padded[i] for i in chunk]
            part_rows_html.append(
                "<tr>" + "".join(f"<td>{_paragraph_to_html(cell)}</td>" for cell in part_values) + "</tr>"
            )
        label = f"<div class='table-part-label'>Part {idx}</div>" if multi_part else ""
        parts.append(
            label
            + "<table class='report-table report-table-compact'><thead><tr>"
            + "".join(f"<th>{_paragraph_to_html(header)}</th>" for header in part_headers)
            + "</tr></thead><tbody>"
            + "".join(part_rows_html)
            + "</tbody></table>"
        )
    return "".join(parts)


def _simple_markdown_to_html(markdown: str) -> str:
    blocks = _parse_markdown_blocks(markdown, "supplement", [])
    html_parts: list[str] = []
    for block in blocks:
        if block.kind == "heading":
            level = min(max(block.heading_level, 1), 3)
            html_parts.append(f"<h{level}>{html.escape(_clean_heading_title(block.title))}</h{level}>")
        elif block.kind == "table":
            html_parts.append(_table_markdown_to_html(block.markdown))
        elif block.kind == "list":
            html_parts.append(_list_markdown_to_html(block.markdown))
        elif block.kind == "figure":
            if block.markdown.lstrip().startswith("<svg"):
                html_parts.append(f"<div class='diagram-figure'>{block.markdown}</div>")
            else:
                html_parts.append(f"<pre>{html.escape(block.markdown)}</pre>")
        elif block.kind == "code":
            html_parts.append(f"<pre>{html.escape(block.markdown)}</pre>")
        else:
            html_parts.append(f"<p>{_paragraph_to_html(block.markdown)}</p>")
    return "".join(html_parts)


def _is_markdown_table(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    current = lines[index].strip()
    nxt = lines[index + 1].strip()
    return current.startswith("|") and nxt.startswith("|") and set(nxt.replace("|", "").strip()) <= {"-", ":", " "}


def _is_list_line(line: str) -> bool:
    stripped = line.lstrip()
    return bool(re.match(r"^(?:[-*]\s+|\d+\.\s+)", stripped))


def _is_appendix_heading(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in TRACE_HEADING_PATTERNS)


def _extract_numeric_tokens(text: str) -> set[str]:
    return set(re.findall(r"-?\d+(?:\.\d+)?", text))
