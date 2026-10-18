"""Query an existing task once; does not submit generation. May require service access."""

import argparse
import asyncio
import json

from llama_index.tools.suno_acedatacloud import SunoToolSpec


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    args = parser.parse_args()
    spec = SunoToolSpec()
    try:
        print(json.dumps(await spec.asuno_get_task(args.task_id), indent=2))
    finally:
        await spec.aclose()


if __name__ == "__main__":
    asyncio.run(main())
