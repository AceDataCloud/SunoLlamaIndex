# Suno by Ace Data Cloud for LlamaIndex

[简体中文](readme/README_zh_Hans.md) · [API access and current pricing](https://platform.acedata.cloud/models?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_pricing)

Native LlamaIndex music tools, maintained by **Ace Data Cloud**. Install this
single-service package and pass `SunoToolSpec().to_tool_list()` to your agent.
You do not configure an MCP server or implement your own HTTP tools. This is an
Ace-provided Suno integration, not an official Suno or LlamaIndex product.

- `suno_generate_music`: submit once, returning a task ID.
- `suno_get_task`: retrieve the same task; final audio URLs appear after success.
- Synchronous and asynchronous native `FunctionTool` calls share the same schema.
- A model must be chosen explicitly. No fallback or automatic generation retries.

## 1. Install this integration

Python 3.10–3.12 are tested. The standard distribution name is
`llama-index-tools-suno-acedatacloud` (namespace `llama_index.tools.suno_acedatacloud`).
**Initial release status: source PR; not yet published to PyPI or listed by LlamaIndex.**
Do not expect `pip install llama-index-tools-suno-acedatacloud` to work until a
release is published. Use the exact commit/PR or download its wheel for review:

```bash
python -m pip install "llama-index-tools-suno-acedatacloud @ git+https://github.com/AceDataCloud/SunoLlamaIndex.git@codex/native-suno-tools"
```

This installs the native tool package, not the older SDK search/extraction example.
The package uses the published Ace SDK; it does not copy shared SDK or MCP code.
[Official LlamaIndex tool concepts](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools/).

## 2. Register and get an application API Token

1. [Register or sign in to Ace Data Cloud](https://platform.acedata.cloud?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_register).
2. Open [Applications](https://platform.acedata.cloud/console/applications?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_api_key). Find **General application**;
   if absent, select **Initialize General Application**. Its key can use services
   your account is entitled to. A service-specific application's key is limited
   to that service.
3. Copy an existing API Key, or choose **Manage Keys → Create** for a dedicated
   `LlamaIndex Suno` key. Check Suno access, current model availability, usage
   limits and [balance/pricing](https://platform.acedata.cloud/models?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_balance) first.

![Real Ace application key page; key values redacted](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/get-api-key-en.png)

4. When creating a key, review **Expiration Time**, **Set Usage Limitation**,
   and **Allowed APIs**. If API restrictions are enabled, allow **both**
   `/suno/audios` and `/suno/tasks`. Create the key, return to the key list,
   then copy the token value.

![Real Ace key creation page; dedicated key and optional restrictions](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/create-api-key-en.png)

These are real Ace console screenshots reused from the Suno Dify guide at the
linked fixed source commit, retrieved 2026-10-18 (the create-key image retains the
old example name `Dify tutorial`; enter `LlamaIndex Suno` instead); they show account setup, not
LlamaIndex execution. Visible key values are redacted. Layout can change.

Use the raw application token, without `Bearer `, quote characters or spaces.
A `platform-...` account-management token cannot replace it. Never paste a key
into an agent prompt, notebook output, committed code or screenshot.

## 3. Put the token in the native tool constructor

Set `ACEDATACLOUD_API_TOKEN` in your environment; `SunoToolSpec()` reads it.
Alternatively pass `api_token=your_secret_from_a_credential_store` in application
code. The token is never an argument in the agent-visible tool schema.

```python
from llama_index.tools.suno_acedatacloud import SunoToolSpec

spec = SunoToolSpec()
tools = spec.to_tool_list()
print([tool.metadata.name for tool in tools])
# ['suno_generate_music', 'suno_get_task']

# With your existing function-calling LlamaIndex LLM:
# from llama_index.core.agent.workflow import FunctionAgent
# agent = FunctionAgent(llm=llm, tools=tools)
```

Constructing the tools and inspecting metadata sends no generation request.
This is a code framework: there is no claimed new settings page, provider
selector or music GUI. [Official debugging screenshots](docs/visual-sources.md)
are historical references only; the free consumer test below runs native tools.

## 4. Submit once, then query the same task

The following creates a **billable** music task if run with a valid token.
Use only after you have authorized its cost and chosen an available Suno model
from your current account. The integration deliberately has no default model.

```python
import asyncio
from llama_index.tools.suno_acedatacloud import SunoToolSpec


async def main():
    spec = SunoToolSpec()
    try:
        generate, retrieve = spec.to_tool_list()
        submission = (
            await generate.acall(
                prompt="A gentle instrumental piano melody for a sunrise.",
                model="YOUR_AVAILABLE_SUNO_MODEL",
                instrumental=True,
            )
        ).raw_output
        print(submission["task_id"])
        # Store this ID. Wait at least 15 seconds before each pending query.
        await asyncio.sleep(15)
        result = (await retrieve.acall(task_id=submission["task_id"])).raw_output
        print(result)
    finally:
        await spec.aclose()


asyncio.run(main())
```

This makes one submission and one query; it does not wait indefinitely. If the
result is `pending`, save its task ID and call **only** `suno_get_task` again after
15 seconds. Do not rerun generation to check progress. You can also query a
previous ID using `python examples/query_existing.py YOUR_EXISTING_TASK_ID`.
Query access does not authorize a new paid task. See [task API](https://platform.acedata.cloud/documents/suno-tasks?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_task_guide).

Only `status="succeeded"`, `success=true` and non-empty `media_urls` represent
completed audio. `processing` and streaming preview URLs remain pending and are
hidden from `media_urls`. A task failure stays `failed`. An HTTP 401/403/429/500
keeps the SDK error type. On an ambiguous timeout or missing task ID, inspect
your account history instead of automatically generating again.

A completed tool result has this shape (illustrative values, not a live receipt):

```json
{"task_id":"your-task-id","status":"succeeded","success":true,
 "media_urls":["https://.../final.mp3"],"trace_id":"your-trace-id",
 "polling_interval_seconds":null}
```

## 5. Verify without a real key or paid request

```bash
python -m pip install -e ".[dev]"
python examples/offline.py
pytest
ruff check .
ruff format --check .
python -m build
```

The offline consumer uses synthetic HTTP responses, a dummy token and
`example.invalid` media URLs. It calls real LlamaIndex native tools and the
published SDK; it does not generate real music. CI also installs the built wheel
in a separate environment before running that consumer. Passing tests do not
prove a paid generation, final media, a unique bill, official listing or revenue.

## Troubleshooting

| Symptom | Action |
|---|---|
| Package not found on PyPI | Initial release is not published yet; use the source PR/commit for review. |
| Missing key or 401 | Copy the full raw application token; check expiry, permissions and service access. |
| 403 or insufficient balance | Inspect the upstream SDK error and account limits; do not generate repeatedly. |
| 429 or network timeout | Automatic retries are off; inspect submission/task history before another generation. |
| Still pending / preview audio | Wait, then query the same ID; do not resubmit. |
| Query denied | Allow `/suno/tasks` for the same application/key; another account's ID is not access. |
| No final media after a success flag | Inspect the same task; do not fabricate a final URL or resubmit. |

## Distribution and official discovery

This package follows LlamaIndex's independent integration naming and namespace.
[Upstream policy](https://github.com/run-llama/llama_index/blob/main/CONTRIBUTING.md)
no longer accepts new packages in the monorepo. A release workflow using PyPI
Trusted Publishing is prepared; its project/publisher setup and human review
must be completed before publication. The old LlamaHub site has moved to the
[current official integration docs](https://developers.llamaindex.ai/python/framework/community/integrations/).
Official discoverability and default inclusion are not claimed.

MIT. Suno names identify the supported service; Ace Data Cloud maintains this integration.
