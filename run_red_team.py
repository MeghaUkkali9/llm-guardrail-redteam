import asyncio
import logging
from pathlib import Path

from red_team.config import get_settings
from red_team.report import print_console_summary, write_markdown_report
from red_team.runner import run_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

REPORT_PATH = Path(__file__).parent / "report.md"


async def main():
    settings = get_settings()
    results = await run_all(settings)
    print_console_summary(results)
    write_markdown_report(results, REPORT_PATH)
    print(f"Full report written to {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
