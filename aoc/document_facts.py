from __future__ import annotations

import re

from aoc.models import (
    DocumentFactArtifact,
    DocumentFactCollectionArtifact,
    DocumentProcessOptionsArtifact,
    EconomicFactArtifact,
    EquipmentMentionArtifact,
    ProcessComparisonArtifact,
    ProcessOptionFact,
    ReactionMentionArtifact,
    SiteComparisonArtifact,
)
from aoc.properties.sources import is_valid_property_identifier_name, normalize_chemical_name


_PROCESS_HEADING_RE = re.compile(r"(?im)^\s*(?:\d+(?:\.\d+)*)?\s*process\s+(\d+)\s*$")
_PROCESS_INLINE_RE = re.compile(r"(?i)\bprocess\s+(\d+)\b")
_SELECTED_PROCESS_RE = re.compile(r"(?is)process\s+selected.*?process\s+(\d+)\s+is\s+selected|process\s+(\d+)\s+is\s+selected")
_SITE_HEADING_RE = re.compile(r"(?im)^\s*(?:\d+(?:\.\d+)*)?\s*suggested\s+site\s*$")
_SITE_VALUE_RE = re.compile(r"(?im)^\s*([A-Z][A-Za-z .-]+),\s*([A-Z][A-Za-z .-]+)\s*$")
_BEST_SITE_RE = re.compile(r"(?i)conclude that\s+([A-Z][A-Za-z .-]+),\s*([A-Z][A-Za-z .-]+)\s+is the best site")
_UNIT_TAG_RE = re.compile(r"\b(?:[A-Z]{1,4}\d{3}|PFR\d*|STR\s*-\s*R\d{3}|DC\d{3}|C\d{3}|E\d{3}|HE\d{3}|S\d{3}|3S\d{3}|M\d{3}|R\d{3})\b")
_ECONOMIC_FACT_RE = re.compile(r"(?i)\b(?:rs\.?|inr)\s*[\d,]+(?:\.\d+)?|\b[\d,]+(?:\.\d+)?\s*(?:lakhs?|crores?|kg|tpa|mta|mt/annum)\b")

_CHEMICAL_KEYWORDS = (
    "acid",
    "anhydride",
    "benzene",
    "oxide",
    "chloride",
    "bromide",
    "fluoride",
    "peroxide",
    "hydroxide",
    "ketone",
    "aldehyde",
    "alcohol",
    "amine",
    "phenyl",
    "acetophenone",
    "cyclohexane",
    "cyclohexanone",
    "methanol",
    "ethanol",
    "water",
    "oxygen",
    "hydrogen",
    "carbon monoxide",
    "ibuprofen",
    "ammonia",
    "sodium",
    "potassium",
    "palladium",
    "alcl",
    "zncl",
    "tbab",
    "hf",
)
_CHEMICAL_PHRASE_RE = re.compile(
    r"\b((?:[A-Z][A-Za-z0-9-]*\s+){0,2}(?:"
    + "|".join(sorted((re.escape(item) for item in _CHEMICAL_KEYWORDS), key=len, reverse=True))
    + r"))\b",
    re.IGNORECASE,
)
_UTILITY_KEYWORDS = ("steam", "cooling water", "chilled water", "therminol", "hot water", "power", "electricity", "nitrogen")
_NARRATIVE_SKIP_TOKENS = {
    "figure",
    "table",
    "chapter",
    "process",
    "yield",
    "selected",
    "page",
    "design",
    "plant",
    "ibuprofen",
}
_EQUIPMENT_LINE_SKIP_TOKENS = {
    "reactor",
    "column",
    "distillation",
    "plug flow",
    "stirred tank",
    "separator",
    "mixer",
    "evaporator",
}
_NUMERIC_FRAGMENT_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)?%?|\d+(?:\.\d+)?\.)\s*$")
_CHEMICAL_STOPWORDS = {
    "yield",
    "process",
    "selected",
    "page",
    "pages",
    "table",
    "figure",
    "chapter",
    "plant",
    "design",
    "batch",
    "site",
}
_NARRATIVE_LEAD_RE = re.compile(
    r"^\s*(?:process|use of|also involves|it involves|of|as|such as|make|to generate|availability of|power and)\b",
    re.IGNORECASE,
)
_NONSPECIES_PHRASES = {
    "profitability factors",
    "availability of water",
}
_INCOMPLETE_MOIETY_RE = re.compile(r"\b[a-z0-9-]+\s+phenyl\s*$", re.IGNORECASE)


def _route_family_hints(text: str) -> list[str]:
    lowered = text.lower()
    hints: list[str] = []
    for key, label in (
        ("acyl", "acylation"),
        ("oxid", "oxidation"),
        ("carbonyl", "carbonylation"),
        ("hydrogen", "hydrogenation"),
        ("hydrolys", "hydrolysis"),
        ("rearrang", "rearrangement"),
        ("extract", "extraction"),
        ("crystalli", "crystallization"),
    ):
        if key in lowered:
            hints.append(label)
    return sorted(set(hints))


def _extract_yield(text: str) -> float | None:
    match = re.search(r"(?i)yield(?:\s+of\s+this\s+process)?\s+(?:is|of)?\s*([0-9]+(?:\.[0-9]+)?)\s*%", text)
    if not match:
        return None
    try:
        return float(match.group(1)) / 100.0
    except ValueError:
        return None


def _chemical_like_lines(text: str, product_name: str) -> list[str]:
    candidates: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" \t-•")
        if not line:
            continue
        segments = [segment.strip(" \t-•") for segment in re.split(r"[.;]", line) if segment.strip(" \t-•")]
        for segment in segments:
            if not segment:
                continue
            lowered = segment.lower()
            if any(token in lowered for token in _EQUIPMENT_LINE_SKIP_TOKENS):
                continue
            phrase_matches = [match.group(1).strip() for match in _CHEMICAL_PHRASE_RE.finditer(segment)]
            if phrase_matches:
                candidates.extend(phrase_matches)
                continue
            if len(segment) > 90:
                continue
            if any(token in lowered for token in _NARRATIVE_SKIP_TOKENS):
                continue
            word_count = len(segment.split())
            has_keyword = any(keyword in lowered for keyword in _CHEMICAL_KEYWORDS)
            has_formula_shape = bool(re.search(r"[A-Z]{2,}\d*|[A-Za-z]+\([^)]+\)|\d", segment))
            if word_count <= 8 and (has_keyword or has_formula_shape):
                candidates.append(segment.rstrip("."))
    normalized_product = normalize_chemical_name(product_name)
    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        normalized = normalize_chemical_name(item)
        if not normalized or normalized == normalized_product or normalized in seen or not _is_valid_chemical_candidate(item, product_name):
            continue
        seen.add(normalized)
        result.append(item)
    return result


def _is_valid_chemical_candidate(text: str, product_name: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if not is_valid_property_identifier_name(stripped):
        return False
    if _NUMERIC_FRAGMENT_RE.match(stripped):
        return False
    lowered = stripped.lower()
    if _NARRATIVE_LEAD_RE.match(stripped):
        return False
    if any(phrase in lowered for phrase in _NONSPECIES_PHRASES):
        return False
    if "%" in lowered and not any(keyword in lowered for keyword in _CHEMICAL_KEYWORDS):
        return False
    if len(re.findall(r"[A-Za-z]", stripped)) < 2:
        return False
    tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
    if tokens and all(token in _CHEMICAL_STOPWORDS or token.isdigit() for token in tokens):
        return False
    if _INCOMPLETE_MOIETY_RE.search(lowered) and "benzene" not in lowered and "acid" not in lowered and "oxide" not in lowered:
        return False
    if normalize_chemical_name(stripped) == normalize_chemical_name(product_name):
        return False
    return True


def _extract_process_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    matches: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if "..." in stripped:
            continue
        match = _PROCESS_HEADING_RE.match(stripped)
        if match:
            matches.append((index, f"Process {match.group(1)}"))
            continue
        if stripped.lower().startswith("process ") and stripped[8:].strip().isdigit():
            matches.append((index, f"Process {stripped[8:].strip()}"))
    sections: list[tuple[str, str]] = []
    for idx, (start, label) in enumerate(matches):
        end = matches[idx + 1][0] if idx + 1 < len(matches) else len(lines)
        section_text = "\n".join(lines[start:end]).strip()
        if section_text:
            sections.append((label, section_text))
    deduped_sections: dict[str, str] = {}
    for label, section_text in sections:
        existing = deduped_sections.get(label)
        if existing is None or len(section_text) > len(existing):
            deduped_sections[label] = section_text
    return [(label, deduped_sections[label]) for label in sorted(deduped_sections, key=lambda item: int(item.split()[-1]))]


def _extract_selected_process_label(text: str) -> str | None:
    match = _SELECTED_PROCESS_RE.search(text)
    if not match:
        return None
    process_number = match.group(1) or match.group(2)
    return f"Process {process_number}" if process_number else None


def _extract_site_options(text: str, source_id: str) -> tuple[list[SiteComparisonArtifact], list[str]]:
    sites: list[SiteComparisonArtifact] = []
    selected: list[str] = []
    for match in _BEST_SITE_RE.finditer(text):
        site_name = match.group(1).strip()
        state = match.group(2).strip()
        selected.append(site_name)
        sites.append(
            SiteComparisonArtifact(
                site_id=normalize_chemical_name(f"{site_name}_{state}"),
                site_name=site_name,
                state=state,
                selected_in_document=True,
                rationale="Selected explicitly in the source document.",
                source_document_id=source_id,
                source_excerpt=match.group(0)[:240],
                citations=[source_id],
            )
        )
    heading = _SITE_HEADING_RE.search(text)
    if heading:
        tail = text[heading.end() : heading.end() + 1200]
        heading_matches = list(_SITE_VALUE_RE.finditer(tail))
        for match in _SITE_VALUE_RE.finditer(tail):
            site_name = match.group(1).strip()
            state = match.group(2).strip()
            site_id = normalize_chemical_name(f"{site_name}_{state}")
            if any(item.site_id == site_id for item in sites):
                continue
            is_selected = site_name in selected or (not selected and heading_matches and match.start() == heading_matches[0].start())
            sites.append(
                SiteComparisonArtifact(
                    site_id=site_id,
                    site_name=site_name,
                    state=state,
                    selected_in_document=is_selected,
                    rationale="Mentioned under suggested-site discussion.",
                    source_document_id=source_id,
                    source_excerpt=match.group(0)[:240],
                    citations=[source_id],
                )
            )
            if is_selected and site_name not in selected:
                selected.append(site_name)
    return sites, selected


def _extract_equipment_mentions(text: str, source_id: str) -> list[EquipmentMentionArtifact]:
    mentions: list[EquipmentMentionArtifact] = []
    seen: set[str] = set()
    for match in _UNIT_TAG_RE.finditer(text):
        raw_tag = match.group(0).replace(" ", "")
        normalized_tag = raw_tag.upper()
        if normalized_tag in seen:
            continue
        seen.add(normalized_tag)
        unit_type = ""
        if normalized_tag.startswith("DC") or normalized_tag.startswith("C"):
            unit_type = "distillation_column_or_condenser"
        elif normalized_tag.startswith("R") or normalized_tag.startswith("STR"):
            unit_type = "reactor"
        elif normalized_tag.startswith("PFR"):
            unit_type = "plug_flow_reactor"
        elif normalized_tag.startswith("E"):
            unit_type = "evaporator"
        elif normalized_tag.startswith("HE"):
            unit_type = "heat_exchanger"
        elif normalized_tag.startswith("S") or normalized_tag.startswith("3S"):
            unit_type = "separator"
        elif normalized_tag.startswith("M"):
            unit_type = "mixer"
        mentions.append(
            EquipmentMentionArtifact(
                mention_id=f"{source_id}_{normalize_chemical_name(normalized_tag)}",
                unit_tag=normalized_tag,
                unit_type=unit_type,
                service_hint="Mentioned in document text.",
                source_document_id=source_id,
                source_excerpt=text[max(0, match.start() - 80) : match.end() + 80].strip(),
                citations=[source_id],
            )
        )
    return mentions


def _extract_operating_mode_hints(text: str) -> list[str]:
    hints: list[str] = []
    lowered = text.lower()
    if "batch" in lowered:
        hints.append("batch")
    if "continuous" in lowered:
        hints.append("continuous")
    return sorted(set(hints))


def _extract_utility_mentions(text: str) -> list[str]:
    lowered = text.lower()
    return [keyword.title() for keyword in _UTILITY_KEYWORDS if keyword in lowered]


def _extract_economic_facts(text: str, source_id: str) -> list[EconomicFactArtifact]:
    facts: list[EconomicFactArtifact] = []
    for index, match in enumerate(_ECONOMIC_FACT_RE.finditer(text), start=1):
        excerpt = text[max(0, match.start() - 80) : match.end() + 80].strip()
        lowered = excerpt.lower()
        category = "general"
        if "project cost" in lowered or "capital" in lowered:
            category = "project_cost"
        elif "working capital" in lowered:
            category = "working_capital"
        elif "cost of production" in lowered:
            category = "cost_of_production"
        facts.append(
            EconomicFactArtifact(
                fact_id=f"{source_id}_econ_{index}",
                label=f"Document economic fact {index}",
                value_text=match.group(0).strip(),
                units="text",
                category=category,
                source_document_id=source_id,
                source_excerpt=excerpt[:240],
                citations=[source_id],
            )
        )
        if len(facts) >= 12:
            break
    return facts


def extract_document_facts(source_id: str, title: str, text: str, product_name: str) -> DocumentFactArtifact:
    process_sections = _extract_process_sections(text)
    selected_process_label = _extract_selected_process_label(text)
    process_options: list[ProcessOptionFact] = []
    reaction_mentions: list[ReactionMentionArtifact] = []
    comparison_rows: list[str] = []

    for index, (label, section_text) in enumerate(process_sections, start=1):
        species = _chemical_like_lines(section_text, product_name)
        raw_materials = [item for item in species if "catal" not in item.lower()][:4]
        catalysts = [item for item in species if any(token in item.lower() for token in ("catalyst", "pd", "palladium", "alcl", "zncl", "hf", "tbab"))][:4]
        solvents = [item for item in species if any(token in item.lower() for token in ("solvent", "cyclohexane", "dichloromethane", "methanol", "ethanol", "petroleum ether"))][:4]
        yield_fraction = _extract_yield(section_text)
        family_hints = _route_family_hints(section_text)
        option_id = normalize_chemical_name(f"{source_id}_{label}")
        selected_in_document = label == selected_process_label
        process_options.append(
            ProcessOptionFact(
                option_id=option_id,
                label=label,
                source_document_id=source_id,
                selected_in_document=selected_in_document,
                yield_fraction=yield_fraction,
                reaction_family_hints=family_hints,
                extracted_species=species,
                raw_materials=raw_materials,
                catalysts=catalysts,
                solvents=solvents,
                hazards=[line for line in ("high pressure", "carbon monoxide", "toxic catalyst", "waste burden") if line in section_text.lower()],
                summary=" ".join(section_text.split())[:420],
                source_excerpt=" ".join(section_text.split())[:420],
                citations=[source_id],
            )
        )
        comparison_rows.append(
            f"| {label} | {'yes' if selected_in_document else 'no'} | {yield_fraction:.2f} | {', '.join(family_hints) or '-'} | {', '.join(species[:4]) or '-'} |"
            if yield_fraction is not None
            else f"| {label} | {'yes' if selected_in_document else 'no'} | - | {', '.join(family_hints) or '-'} | {', '.join(species[:4]) or '-'} |"
        )
        if species:
            reaction_mentions.append(
                ReactionMentionArtifact(
                    mention_id=f"{option_id}_step_1",
                    route_option_id=option_id,
                    step_label="document_step_1",
                    reaction_family_hint=family_hints[0] if family_hints else "",
                    reactants=species[:2],
                    products=[product_name],
                    catalysts=catalysts,
                    solvents=solvents,
                    source_document_id=source_id,
                    source_excerpt=" ".join(section_text.split())[:420],
                    citations=[source_id],
                )
            )

    comparison = ProcessComparisonArtifact(
        comparison_id=f"{source_id}_process_comparison",
        source_document_id=source_id,
        options=process_options,
        selected_option_id=next((item.option_id for item in process_options if item.selected_in_document), None),
        comparison_notes=[
            "Structured from user document using heuristic route-section extraction.",
            "Use as process-selection evidence, not as a fully trusted stoichiometric route package.",
        ],
        markdown="\n".join(
            [
                "| Route | Selected | Yield | Family Hints | Extracted Species |",
                "| --- | --- | --- | --- | --- |",
                *comparison_rows,
            ]
        ),
        citations=[source_id],
    )

    site_options, selected_sites = _extract_site_options(text, source_id)
    alias_map = {
        normalize_chemical_name(product_name): [product_name],
    }
    for option in process_options:
        for species in option.extracted_species:
            normalized = normalize_chemical_name(species)
            alias_map.setdefault(normalized, [])
            if species not in alias_map[normalized]:
                alias_map[normalized].append(species)

    markdown_lines = [
        f"Document facts extracted for {title}.",
        f"Process options: {len(process_options)}.",
        f"Equipment mentions: {len(_extract_equipment_mentions(text, source_id))}.",
        f"Selected process in document: {selected_process_label or 'not found'}.",
        f"Selected site in document: {', '.join(selected_sites) or 'not found'}.",
    ]
    return DocumentFactArtifact(
        document_id=normalize_chemical_name(f"{source_id}_{title}"),
        source_id=source_id,
        title=title,
        process_comparisons=[comparison] if process_options else [],
        reaction_mentions=reaction_mentions,
        equipment_mentions=_extract_equipment_mentions(text, source_id),
        site_comparisons=site_options,
        economic_facts=_extract_economic_facts(text, source_id),
        operating_mode_hints=_extract_operating_mode_hints(text),
        utility_mentions=_extract_utility_mentions(text),
        alias_map=alias_map,
        markdown="\n".join(markdown_lines),
        citations=[source_id],
        assumptions=["Document-fact extraction uses deterministic heuristics over user-supplied text and is intentionally conservative."],
    )


def build_document_fact_collection(documents: list[DocumentFactArtifact]) -> DocumentFactCollectionArtifact:
    process_options = [
        option
        for document in documents
        for comparison in document.process_comparisons
        for option in comparison.options
    ]
    selected_labels = [
        option.label
        for option in process_options
        if option.selected_in_document
    ]
    selected_sites = [
        site.site_name
        for document in documents
        for site in document.site_comparisons
        if site.selected_in_document
    ]
    markdown = "\n".join(
        [
            "| Document | Process Options | Equipment Mentions | Selected Process | Selected Site |",
            "| --- | --- | --- | --- | --- |",
            *[
                "| "
                + " | ".join(
                    [
                        document.title,
                        str(sum(len(item.options) for item in document.process_comparisons)),
                        str(len(document.equipment_mentions)),
                        ", ".join(
                            option.label
                            for comparison in document.process_comparisons
                            for option in comparison.options
                            if option.selected_in_document
                        )
                        or "-",
                        ", ".join(site.site_name for site in document.site_comparisons if site.selected_in_document) or "-",
                    ]
                )
                + " |"
                for document in documents
            ],
        ]
    )
    return DocumentFactCollectionArtifact(
        documents=documents,
        process_option_count=len(process_options),
        reaction_mention_count=sum(len(document.reaction_mentions) for document in documents),
        equipment_mention_count=sum(len(document.equipment_mentions) for document in documents),
        selected_process_labels=selected_labels,
        selected_site_names=selected_sites,
        markdown=markdown,
        citations=sorted({source_id for document in documents for source_id in document.citations}),
        assumptions=["Document-fact collection aggregates per-document heuristic extraction outputs."],
    )


def build_document_process_options(documents: list[DocumentFactArtifact]) -> DocumentProcessOptionsArtifact:
    options = [
        option
        for document in documents
        for comparison in document.process_comparisons
        for option in comparison.options
    ]
    markdown = "\n".join(
        [
            "| Route | Selected | Yield | Source Document |",
            "| --- | --- | --- | --- |",
            *[
                f"| {option.label} | {'yes' if option.selected_in_document else 'no'} | "
                f"{f'{option.yield_fraction:.2f}' if option.yield_fraction is not None else '-'} | {option.source_document_id} |"
                for option in options
            ],
        ]
    )
    return DocumentProcessOptionsArtifact(
        options=options,
        selected_option_ids=[option.option_id for option in options if option.selected_in_document],
        source_document_ids=sorted({option.source_document_id for option in options}),
        markdown=markdown,
        citations=sorted({source_id for option in options for source_id in option.citations}),
        assumptions=["Document process options are derived directly from user-document process sections and comparison text."],
    )
