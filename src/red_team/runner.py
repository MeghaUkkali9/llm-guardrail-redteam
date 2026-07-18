import logging

from openai import AsyncOpenAI

from red_team.adapter import AgenticAskAdapter
from red_team.config import Settings
from red_team.evaluators import EvalResult, evaluate
from red_team.test_cases import TEST_CASES, TestCase

logger = logging.getLogger(__name__)


async def run_test_case(
    test_case: TestCase, adapter: AgenticAskAdapter, settings: Settings, judge_client: AsyncOpenAI
) -> EvalResult:
    logger.info(f"Running {test_case.id} ({test_case.category.value}): {test_case.prompt[:60]}...")
    response = await adapter.ask(test_case.prompt)
    result = await evaluate(test_case, response, settings, judge_client)
    logger.info(f"{test_case.id}: {'PASS' if result.passed else 'FAIL'} — {result.reason}")
    return result


async def run_all(settings: Settings | None = None, test_cases: list[TestCase] | None = None) -> list[EvalResult]:
    settings = settings or Settings()
    test_cases = test_cases if test_cases is not None else TEST_CASES
    adapter = AgenticAskAdapter(settings)
    judge_client = AsyncOpenAI(api_key=settings.openai_api_key)

    results = []
    for test_case in test_cases:
        results.append(await run_test_case(test_case, adapter, settings, judge_client))
    return results
