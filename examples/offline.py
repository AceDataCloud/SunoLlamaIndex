"""Native FunctionTool consumer smoke test using synthetic HTTP responses only."""

import asyncio
import json

import respx

from llama_index.tools.suno_acedatacloud import SunoToolSpec


async def main():
    with respx.mock(assert_all_mocked=True) as router:
        router.post("https://api.acedata.cloud/suno/audios").respond(200, json={"task_id": "synthetic-task"})
        router.post("https://api.acedata.cloud/suno/tasks").respond(
            200,
            json={
                "id": "synthetic-task",
                "response": {"success": True, "data": [{"audio_url": "https://example.invalid/synthetic.mp3"}]},
            },
        )
        spec = SunoToolSpec(api_token="offline-not-a-key")
        try:
            generate, retrieve = spec.to_tool_list()
            submitted = generate.call(
                prompt="Instrumental piano", model="user-selected-model", instrumental=True
            ).raw_output
            result = (await retrieve.acall(task_id=submitted["task_id"])).raw_output
            assert result["status"] == "succeeded"
            assert result["media_urls"] == ["https://example.invalid/synthetic.mp3"]
            assert len(router.calls) == 2
            print(
                json.dumps(
                    {
                        "mode": "synthetic-offline",
                        "tools": [t.metadata.name for t in spec.to_tool_list()],
                        "submitted": submitted,
                        "result": result,
                    },
                    indent=2,
                )
            )
        finally:
            await spec.aclose()


if __name__ == "__main__":
    asyncio.run(main())
