from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from aoc.models import ChapterArtifact, ProjectConfig, ProjectRunState, utc_now

T = TypeVar("T", bound=BaseModel)


class ArtifactStore:
    def __init__(self, output_root: str = "outputs"):
        self.output_root = Path(output_root).resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        return self.output_root / project_id

    def ensure_project_layout(self, project_id: str) -> Path:
        base = self.project_dir(project_id)
        for relative in ("artifacts", "chapter_artifacts", "chapters", "annexures"):
            (base / relative).mkdir(parents=True, exist_ok=True)
        return base

    def save_model(self, project_id: str, relative_path: str, model: BaseModel) -> Path:
        base = self.ensure_project_layout(project_id)
        path = base / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_model(self, project_id: str, relative_path: str, model_type: type[T]) -> T:
        path = self.project_dir(project_id) / relative_path
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def maybe_load_model(self, project_id: str, relative_path: str, model_type: type[T]) -> T | None:
        path = self.project_dir(project_id) / relative_path
        if not path.exists():
            return None
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def save_text(self, project_id: str, relative_path: str, content: str) -> Path:
        base = self.ensure_project_layout(project_id)
        path = base / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def save_chapter(self, project_id: str, chapter: ChapterArtifact) -> tuple[Path, Path]:
        json_path = self.save_model(project_id, f"chapter_artifacts/{chapter.chapter_id}.json", chapter)
        md_path = self.save_text(project_id, f"chapters/{chapter.chapter_id}.md", chapter.rendered_markdown)
        return json_path, md_path

    def load_chapter(self, project_id: str, chapter_id: str) -> ChapterArtifact:
        return self.load_model(project_id, f"chapter_artifacts/{chapter_id}.json", ChapterArtifact)

    def save_run_state(self, state: ProjectRunState) -> Path:
        state.last_updated = utc_now()
        return self.save_model(state.project_id, "run_state.json", state)

    def load_run_state(self, project_id: str) -> ProjectRunState | None:
        return self.maybe_load_model(project_id, "run_state.json", ProjectRunState)

    def save_config(self, config: ProjectConfig) -> Path:
        return self.save_model(config.project_id, "project_config.json", config)

    def save_json_blob(self, project_id: str, relative_path: str, data: dict) -> Path:
        base = self.ensure_project_layout(project_id)
        path = base / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def delete_path(self, project_id: str, relative_path: str) -> None:
        path = self.project_dir(project_id) / relative_path
        if path.exists():
            path.unlink()
