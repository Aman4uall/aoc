from __future__ import annotations

from pathlib import Path
import re

import yaml

from aoc.models import ProjectConfig


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "project"


def load_project_config(path: str) -> ProjectConfig:
    config_path = Path(path).expanduser().resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = ProjectConfig.model_validate(raw)
    if not config.project_id:
        config.project_id = f"{slugify(config.basis.target_product)}-v1"
    for document in config.user_documents:
        document_path = Path(document.path).expanduser()
        if not document_path.is_absolute():
            document.path = str((config_path.parent / document_path).resolve())
        else:
            document.path = str(document_path.resolve())
    resolved_sheets: list[str] = []
    for sheet in config.india_market_sheets:
        sheet_path = Path(sheet).expanduser()
        if not sheet_path.is_absolute():
            resolved_sheets.append(str((config_path.parent / sheet_path).resolve()))
        else:
            resolved_sheets.append(str(sheet_path.resolve()))
    config.india_market_sheets = resolved_sheets
    if config.basis.process_template.value.endswith("_india"):
        config.require_india_only_data = True
        config.basis.india_only = True
        config.basis.region = "India"
        config.basis.currency = "INR"
    return config
