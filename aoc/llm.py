from __future__ import annotations

import os

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
        load_dotenv()
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMError("GEMINI_API_KEY environment variable is not set.")

    def _generate_modern(self, prompt: str, *, config: dict):
        from google import genai

        client = genai.Client(api_key=self.api_key)
        return client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

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
            config = {
                "temperature": temperature,
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_json_schema": schema.model_json_schema(),
            }
            if use_search:
                config["tools"] = [{"google_search": {}}, {"url_context": {}}]
            response = self._generate_modern(prompt, config=config)
            if not getattr(response, "text", None):
                raise LLMError("Gemini returned an empty structured response.")
            return schema.model_validate_json(response.text)
        except ImportError:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise LLMError("Neither google-genai nor google-generativeai is installed.") from exc
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(model_name=self.model_name, system_instruction=system_instruction)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                ),
            )
            if not getattr(response, "text", None):
                raise LLMError("Legacy Gemini SDK returned an empty structured response.")
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
                config["tools"] = [{"google_search": {}}, {"url_context": {}}]
            response = self._generate_modern(prompt, config=config)
            if not getattr(response, "text", None):
                raise LLMError("Gemini returned an empty text response.")
            return response.text.strip()
        except ImportError:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(model_name=self.model_name, system_instruction=system_instruction)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                ),
            )
            if not getattr(response, "text", None):
                raise LLMError("Legacy Gemini SDK returned an empty text response.")
            return response.text.strip()
