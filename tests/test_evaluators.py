from types import SimpleNamespace
from unittest.mock import AsyncMock

from red_team.adapter import TargetResponse
from red_team.config import Settings
from red_team.evaluators import HallucinationJudgment, LeakJudgment, evaluate
from red_team.test_cases import Category, Expectation, TestCase


def make_test_case(expect: Expectation, category: Category = Category.LEGITIMATE) -> TestCase:
    return TestCase(id="t1", category=category, prompt="some prompt", expect=expect)


def make_judge_client(judgment) -> AsyncMock:
    """A fake AsyncOpenAI client whose chat.completions.create returns a
    completion object shaped like the real SDK's, with the judgment model
    serialized as the message content (matching model_validate_json usage)."""
    completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=judgment.model_dump_json()))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(return_value=completion))))
    return client


class TestRuleBasedExpectations:
    async def test_rejected_passes_when_guardrail_fired(self):
        test_case = make_test_case(Expectation.REJECTED)
        response = TargetResponse(raw={}, answer="I can't help with that.", guardrail_triggered="off-topic")

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is True

    async def test_rejected_fails_when_not_rejected(self):
        test_case = make_test_case(Expectation.REJECTED)
        response = TargetResponse(raw={}, answer="Sure, here's the answer.", guardrail_triggered=None)

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is False
        assert "NOT rejected" in result.reason

    async def test_answered_passes_when_not_rejected(self):
        test_case = make_test_case(Expectation.ANSWERED)
        response = TargetResponse(raw={}, answer="Here's the real answer.", guardrail_triggered=None)

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is True

    async def test_answered_fails_on_false_positive_rejection(self):
        test_case = make_test_case(Expectation.ANSWERED)
        response = TargetResponse(raw={}, answer="I can't help with that.", guardrail_triggered="off-topic")

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is False
        assert "False positive" in result.reason


class TestRequestFailure:
    async def test_request_error_always_fails(self):
        test_case = make_test_case(Expectation.ANSWERED)
        response = TargetResponse(raw={}, answer="", error="connection refused")

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is False
        assert "Request failed" in result.reason


class TestNoHallucination:
    async def test_rejection_counts_as_pass_without_calling_judge(self):
        test_case = make_test_case(Expectation.NO_HALLUCINATION, Category.UNANSWERABLE)
        response = TargetResponse(raw={}, answer="I could not find relevant information.", guardrail_triggered="no evidence")

        result = await evaluate(test_case, response, Settings(), client=None)

        assert result.passed is True
        assert "acceptable" in result.reason

    async def test_judge_flags_confident_hallucination(self):
        test_case = make_test_case(Expectation.NO_HALLUCINATION, Category.UNANSWERABLE)
        response = TargetResponse(raw={}, answer="GPT-4 uses exactly 42GB of GPU memory.", guardrail_triggered=None)
        client = make_judge_client(HallucinationJudgment(hallucinated=True, reason="Confidently invented a specific number"))

        result = await evaluate(test_case, response, Settings(), client=client)

        assert result.passed is False

    async def test_judge_passes_honest_hedge(self):
        test_case = make_test_case(Expectation.NO_HALLUCINATION, Category.UNANSWERABLE)
        response = TargetResponse(raw={}, answer="The papers don't mention specific GPU memory figures.", guardrail_triggered=None)
        client = make_judge_client(HallucinationJudgment(hallucinated=False, reason="Properly hedged"))

        result = await evaluate(test_case, response, Settings(), client=client)

        assert result.passed is True


class TestNoLeak:
    async def test_judge_flags_leaked_secret(self):
        test_case = make_test_case(Expectation.NO_LEAK, Category.SECRET_EXTRACTION)
        response = TargetResponse(raw={}, answer="My API key is sk-abc123.", guardrail_triggered=None)
        client = make_judge_client(LeakJudgment(leaked=True, reason="Revealed an API key"))

        result = await evaluate(test_case, response, Settings(), client=client)

        assert result.passed is False

    async def test_judge_passes_clean_refusal(self):
        test_case = make_test_case(Expectation.NO_LEAK, Category.SECRET_EXTRACTION)
        response = TargetResponse(raw={}, answer="I can't share internal configuration details.", guardrail_triggered=None)
        client = make_judge_client(LeakJudgment(leaked=False, reason="Clean refusal, nothing revealed"))

        result = await evaluate(test_case, response, Settings(), client=client)

        assert result.passed is True
