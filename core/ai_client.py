import json
from typing import List

import requests

SYSTEM_PROMPT = """You are a data cleaning expert. Analyze the provided dataset schema and suggest cleaning operations.
Return ONLY a JSON array of cleaning operations. Each operation must be one of:
- {"operation": "drop_nulls", "column": "col_name"} or {"operation": "drop_nulls"} to drop any row with nulls
- {"operation": "fill_nulls", "column": "col_name", "params": {"value": "replacement"}}
- {"operation": "drop_duplicates", "column": "col_name"} or {"operation": "drop_duplicates"} for all columns
- {"operation": "coerce_type", "column": "col_name", "params": {"dtype": "int|float|numeric|datetime"}}
- {"operation": "normalize_text", "column": "col_name"}
- {"operation": "parse_dates", "column": "col_name"}
- {"operation": "drop_column", "column": "col_name"}
- {"operation": "rename_column", "column": "col_name", "params": {"new_name": "new_col_name"}}

IMPORTANT: Preserve the original language of all column names. Do NOT translate any column names to another language. Keep Vietnamese column names in Vietnamese, English column names in English, etc.

Respond with ONLY the JSON array, no explanation."""


class AIClient:
    def __init__(self):
        self._provider = ""
        self._model = ""
        self._api_key = ""
        self._url = ""

    def configure(self, provider: str, model: str, api_key: str, url: str):
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._url = url.rstrip("/")

    @property
    def is_configured(self) -> bool:
        return all([self._provider, self._model, self._url])

    def get_config(self) -> dict:
        return {
            "provider": self._provider,
            "model": self._model,
            "api_key": self._api_key,
            "url": self._url,
        }

    def analyze(self, df_info: dict, language: str = "EN") -> List[dict]:
        prompt = SYSTEM_PROMPT
        if language == "VI":
            prompt += "\nIMPORTANT: Respond in Vietnamese language."
        user_message = json.dumps(df_info, ensure_ascii=False, default=str)
        content = self._call_api(prompt, user_message)
        if content.startswith("```"):
            lines = content.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(
                "AI returned malformed JSON that could not be parsed. "
                "Please try again."
            )

    def chat(self, system_prompt: str, user_message: str) -> str:
        return self._call_api(system_prompt, user_message)

    def _call_api(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.1,
        }

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        url = f"{self._url}/v1/chat/completions"
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"].strip()
