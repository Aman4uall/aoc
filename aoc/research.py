from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz

from aoc.models import (
    GeographicScope,
    ProjectConfig,
    ResearchBundle,
    SourceDomain,
    SourceKind,
    SourceRecord,
    UserDocument,
)


def _read_document(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return file_path.read_text(encoding="utf-8")
    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        with file_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = [" | ".join(row) for row in reader]
        return "\n".join(rows)
    if suffix == ".json":
        return json.dumps(json.loads(file_path.read_text(encoding="utf-8")), indent=2)
    if suffix == ".pdf":
        document = fitz.open(file_path)
        try:
            return "\n".join(page.get_text("text") for page in document)
        finally:
            document.close()
    raise ValueError(f"Unsupported document type for research ingestion: {file_path.suffix}")


def _is_india_source(source: SourceRecord) -> bool:
    if source.country and source.country.lower() == "india":
        return True
    if source.geographic_scope in {GeographicScope.INDIA, GeographicScope.STATE, GeographicScope.CITY}:
        return True
    label = (source.geographic_label or "").lower()
    return "india" in label


def _is_technical_source(source: SourceRecord) -> bool:
    return source.source_domain in {SourceDomain.TECHNICAL, SourceDomain.SAFETY}


class ResearchManager:
    def __init__(self, reasoning_service):
        self.reasoning_service = reasoning_service

    def _ingest_document(
        self,
        source_id: str,
        label: str,
        path: str,
        *,
        source_kind: SourceKind,
        source_domain: SourceDomain,
        geographic_scope: GeographicScope,
        country: str | None = None,
        citation_text: str | None = None,
    ) -> tuple[SourceRecord, str]:
        text = _read_document(path)
        record = SourceRecord(
            source_id=source_id,
            source_kind=source_kind,
            source_domain=source_domain,
            title=label,
            citation_text=citation_text or f"{label} (user supplied document)",
            extraction_snippet=text[:1200],
            local_path=path,
            geographic_scope=geographic_scope,
            geographic_label=country or geographic_scope.value,
            country=country,
        )
        return record, text

    def _append_source(
        self,
        sources: list[SourceRecord],
        corpus_sections: list[str],
        seen_ids: set[str],
        source: SourceRecord,
        excerpt: str,
    ) -> None:
        if source.source_id in seen_ids:
            return
        seen_ids.add(source.source_id)
        sources.append(source)
        corpus_sections.append(f"[{source.source_id}] {source.title}\n{excerpt[:8000]}")

    def build_bundle(self, config: ProjectConfig) -> ResearchBundle:
        sources: list[SourceRecord] = []
        corpus_sections: list[str] = []
        user_ids: list[str] = []
        seen_ids: set[str] = set()

        for index, document in enumerate(config.user_documents, start=1):
            record, text = self._ingest_document(
                f"user_doc_{index}",
                document.label,
                document.path,
                source_kind=document.source_kind or SourceKind.USER_DOCUMENT,
                source_domain=document.source_domain or SourceDomain.TECHNICAL,
                geographic_scope=document.geographic_scope or GeographicScope.UNKNOWN,
                country="India" if document.geographic_scope in {GeographicScope.INDIA, GeographicScope.STATE, GeographicScope.CITY} else None,
            )
            self._append_source(sources, corpus_sections, seen_ids, record, text)
            user_ids.append(record.source_id)

        for index, sheet in enumerate(config.india_market_sheets, start=1):
            label = Path(sheet).stem.replace("_", " ").replace("-", " ").title()
            record, text = self._ingest_document(
                f"india_sheet_{index}",
                label,
                sheet,
                source_kind=SourceKind.MARKET,
                source_domain=SourceDomain.ECONOMICS,
                geographic_scope=GeographicScope.INDIA,
                country="India",
                citation_text=f"{label} (India market sheet)",
            )
            self._append_source(sources, corpus_sections, seen_ids, record, text)

        should_discover = config.model.backend != "mock" or config.require_india_only_data or not sources
        if should_discover:
            discovery = self.reasoning_service.discover_sources(config.basis)
            for source in discovery.sources:
                excerpt = source.extraction_snippet or source.citation_text
                self._append_source(sources, corpus_sections, seen_ids, source, excerpt)
            if discovery.summary:
                corpus_sections.append(discovery.summary[:8000])

        technical_source_ids = [source.source_id for source in sources if _is_technical_source(source)]
        india_source_ids = [source.source_id for source in sources if _is_india_source(source)]
        return ResearchBundle(
            sources=sources,
            technical_source_ids=technical_source_ids,
            india_source_ids=india_source_ids,
            corpus_excerpt="\n\n".join(corpus_sections)[:32000],
            user_document_ids=user_ids,
        )
