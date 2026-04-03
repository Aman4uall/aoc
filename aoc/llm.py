from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv


class LLMError(RuntimeError):
    """Raised when a model request cannot be completed."""


class BaseLLMClient:
    def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system_instruction: str,
        use_search: bool = False,
        temperature: float = 0.2,
    ) -> BaseModel:
        raise NotImplementedError

    def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str,
        use_search: bool = False,
        temperature: float = 0.2,
    ) -> str:
        raise NotImplementedError


class GoogleGeminiClient(BaseLLMClient):
    def __init__(self, model_name: str, api_key: str | None = None):
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(dotenv_path=project_root / ".env")
        self.model_name = model_name
        self.use_vertex = self._read_bool_env("GOOGLE_GENAI_USE_VERTEXAI")
        self.vertex_project = (
            os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("VERTEX_PROJECT")
            or "aocproject-492204"
        )
        self.vertex_location = (
            os.getenv("GOOGLE_CLOUD_LOCATION")
            or os.getenv("VERTEX_LOCATION")
            or "us-central1"
        )

        # Resolve service-account key to an absolute path
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        if creds_path and not Path(creds_path).is_absolute():
            abs_creds = str(project_root / creds_path)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_creds

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.use_vertex and not self.api_key:
            raise LLMError("GEMINI_API_KEY environment variable is not set.")

    @staticmethod
    def _read_bool_env(name: str) -> bool:
        value = os.getenv(name, "").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _generate_modern(self, prompt: str, *, config: dict):
        from google import genai

        if self.use_vertex:
            client = genai.Client(
                vertexai=True,
                project=self.vertex_project,
                location=self.vertex_location,
            )
        else:
            os.environ["GEMINI_API_KEY"] = self.api_key
            client = genai.Client(api_key=self.api_key)
        return client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

    def _search_tools(self) -> list[dict]:
        # Vertex rejects structured generation when URL Context is combined with
        # controlled JSON output. Keep Vertex on the simpler search tool path.
        if self.use_vertex:
            return [{"google_search": {}}]
        return [{"google_search": {}}, {"url_context": {}}]

    @staticmethod
    def _clean_json_text(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return cleaned

    def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system_instruction: str,
        use_search: bool = False,
        temperature: float = 0.2,
    ) -> BaseModel:
        try:
            if use_search and self.use_vertex:
                schema_prompt = (
                    f"{prompt}\n\n"
                    "Return only valid JSON matching this schema exactly:\n"
                    f"{schema.model_json_schema()}"
                )
                config = {
                    "temperature": temperature,
                    "system_instruction": system_instruction,
                    "tools": self._search_tools(),
                }
                response = self._generate_modern(schema_prompt, config=config)
                if not getattr(response, "text", None):
                    raise LLMError("Vertex returned an empty structured response.")
                return schema.model_validate_json(self._clean_json_text(response.text))

            config = {
                "temperature": temperature,
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_json_schema": schema.model_json_schema(),
            }
            if use_search:
                config["tools"] = self._search_tools()
            response = self._generate_modern(prompt, config=config)
            if not getattr(response, "text", None):
                raise LLMError("Gemini returned an empty structured response.")
            return schema.model_validate_json(self._clean_json_text(response.text))
        except ImportError:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel, GenerationConfig
            except ImportError as exc:
                raise LLMError("Neither google-genai nor vertexai is installed.") from exc

            vertexai.init(project=self.vertex_project, location=self.vertex_location)
            model = GenerativeModel(model_name=self.model_name, system_instruction=system_instruction)
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            if not getattr(response, "text", None):
                raise LLMError("Legacy Vertex SDK returned an empty structured response.")
            return schema.model_validate_json(response.text)

    def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str,
        use_search: bool = False,
        temperature: float = 0.2,
    ) -> str:
        try:
            config = {
                "temperature": temperature,
                "system_instruction": system_instruction,
            }
            if use_search:
                config["tools"] = self._search_tools()
            response = self._generate_modern(prompt, config=config)
            if not getattr(response, "text", None):
                raise LLMError("Gemini returned an empty text response.")
            return response.text.strip()
        except ImportError:
            import vertexai
            from vertexai.generative_models import GenerativeModel, GenerationConfig

            vertexai.init(project=self.vertex_project, location=self.vertex_location)
            model = GenerativeModel(model_name=self.model_name, system_instruction=system_instruction)
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                ),
            )
            if not getattr(response, "text", None):
                raise LLMError("Legacy Vertex SDK returned an empty text response.")
            return response.text.strip()
