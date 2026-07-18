from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from red_team.config import Settings


class TargetResponse(BaseModel):
    """Normalized shape the evaluators work against, regardless of which
    system-under-test's raw response format looked like."""

    raw: Dict[str, Any]
    answer: str
    guardrail_triggered: Optional[str] = None
    grounded: Optional[bool] = None
    sources: list[str] = []
    error: Optional[str] = None


class AgenticAskAdapter:
    """Adapter for this project's own /agentic-ask endpoint.

    Kept as a small, separate class specifically so a different system under
    test (a different RAG API, a different response schema) only needs a new
    adapter implementing `ask()` — the test cases, evaluators, and runner
    don't change.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    async def ask(self, prompt: str) -> TargetResponse:
        payload = {"query": prompt, "top_k": 3, "use_hybrid": True, "model": "gpt-4o-mini"}

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(self._settings.target_url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            return TargetResponse(raw={}, answer="", error=str(e))

        return TargetResponse(
            raw=data,
            answer=data.get("answer", ""),
            guardrail_triggered=data.get("guardrail_triggered"),
            grounded=data.get("grounded"),
            sources=data.get("sources", []),
        )
