"""Point d'entrée du worker : découvre les workflows et démarre le worker Mistral."""

import asyncio

try:
    from mistralai_workflows import discover_workflows, run_worker
except ImportError:  # selon la version du SDK
    from mistralai.workflows import discover_workflows, run_worker  # type: ignore


async def main() -> None:
    decouverts = discover_workflows()
    await run_worker(decouverts)


if __name__ == "__main__":
    asyncio.run(main())
