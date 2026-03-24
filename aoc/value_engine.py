from __future__ import annotations

from aoc.models import ProvenanceTag, SensitivityLevel, ValueRecord


def _format_value(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    formatted = f"{value:.6f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"


def make_value_record(
    value_id: str,
    name: str,
    value: float | int | str,
    units: str,
    *,
    provenance_method: ProvenanceTag = ProvenanceTag.CALCULATED,
    source_ids: list[str] | None = None,
    citations: list[str] | None = None,
    assumptions: list[str] | None = None,
    uncertainty_band: str = "derived",
    sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM,
    blocking: bool = False,
) -> ValueRecord:
    return ValueRecord(
        value_id=value_id,
        name=name,
        value=_format_value(value),
        units=units,
        provenance_method=provenance_method,
        source_ids=list(source_ids or citations or []),
        uncertainty_band=uncertainty_band,
        sensitivity=sensitivity,
        blocking=blocking,
        citations=list(citations or []),
        assumptions=list(assumptions or []),
    )
