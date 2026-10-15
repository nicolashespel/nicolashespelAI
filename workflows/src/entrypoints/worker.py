"""Point d entrée du worker — démarre le worker et enregistre les workflows."""

import asyncio

try:
    from mistralai_workflows import discover_workflows, run_worker
except ImportError:  # selon la version du SDK
    from mistralai.workflows import discover_workflows, run_worker


async def main() -> None:
    discovered = discover_workflows()
    await run_worker(discovered)


if __name__ == "__main__":
    asyncio.run(main())
