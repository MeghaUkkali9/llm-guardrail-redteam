from unittest.mock import AsyncMock

import httpx

from red_team.adapter import AgenticAskAdapter
from red_team.config import Settings


def make_response(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=json_body, request=httpx.Request("POST", "http://test/agentic-ask"))


class TestAgenticAskAdapter:
    async def test_successful_response_is_normalized(self, mocker):
        mocker.patch(
            "httpx.AsyncClient.post",
            AsyncMock(
                return_value=make_response(
                    200,
                    {
                        "answer": "Transformers use self-attention.",
                        "guardrail_triggered": None,
                        "grounded": True,
                        "sources": ["https://arxiv.org/pdf/1706.03762.pdf"],
                    },
                )
            ),
        )
        adapter = AgenticAskAdapter(Settings())

        result = await adapter.ask("What is a transformer?")

        assert result.answer == "Transformers use self-attention."
        assert result.grounded is True
        assert result.guardrail_triggered is None
        assert result.error is None

    async def test_rejected_response_carries_guardrail_reason(self, mocker):
        mocker.patch(
            "httpx.AsyncClient.post",
            AsyncMock(
                return_value=make_response(
                    200,
                    {"answer": "I can't help with that.", "guardrail_triggered": "off-topic", "grounded": False, "sources": []},
                )
            ),
        )
        adapter = AgenticAskAdapter(Settings())

        result = await adapter.ask("What's the weather?")

        assert result.guardrail_triggered == "off-topic"

    async def test_http_error_is_captured_not_raised(self, mocker):
        mocker.patch("httpx.AsyncClient.post", AsyncMock(side_effect=httpx.ConnectError("connection refused")))
        adapter = AgenticAskAdapter(Settings())

        result = await adapter.ask("anything")

        assert result.error is not None
        assert result.answer == ""
