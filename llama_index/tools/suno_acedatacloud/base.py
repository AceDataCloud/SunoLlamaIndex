"""Native Suno tools with single submission and explicit same-task retrieval."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

from acedatacloud import AceDataCloud, AsyncAceDataCloud
from llama_index.core.tools.tool_spec.base import BaseToolSpec

API_BASE = "https://api.acedata.cloud"
_PENDING = {"pending", "processing", "running", "queued", "submitted", "streaming", "in_progress"}
_FAILED = {"failed", "failure", "error", "cancelled", "canceled", "rejected"}


def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must contain text")
    return value.strip()


def _submitted(task_id: str) -> dict[str, Any]:
    if not task_id:
        raise RuntimeError("No task ID returned. Submission outcome is unknown; do not automatically resubmit.")
    return {
        "task_id": task_id,
        "status": "pending",
        "success": None,
        "media_urls": [],
        "next_tool": "suno_get_task",
        "polling_interval_seconds": 15,
        "message": "Submission accepted. Query this same task ID; do not generate again to check progress.",
    }


def _result(task_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    response = raw.get("response", raw)
    if not isinstance(response, dict):
        raise ValueError("Task response must be an object; query the same task ID, do not resubmit.")
    words = {str(node.get(key, "")).lower() for node in (raw, response) for key in ("state", "status")}
    if words & _FAILED or response.get("success") is False:
        status, success = "failed", False
    elif words & _PENDING:
        status, success = "pending", None
    elif response.get("success") is True:
        status, success = "succeeded", True
    else:
        status, success = "pending", None

    urls: list[str] = []
    if status == "succeeded":
        data = response.get("data", [])
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("audio_url"), str):
                url = item["audio_url"]
                parsed = urlsplit(url)
                if (
                    parsed.scheme in ("https", "http")
                    and parsed.hostname
                    and not parsed.username
                    and not parsed.password
                ):
                    if url not in urls:
                        urls.append(url)
        if not urls:
            raise ValueError("Task claims success without final audio URLs; inspect the same task, do not resubmit.")
    output = {
        "task_id": task_id,
        "status": status,
        "success": success,
        "media_urls": urls,
        "trace_id": raw.get("trace_id") or response.get("trace_id"),
        "polling_interval_seconds": 15 if status == "pending" else None,
    }
    if status == "failed":
        output["error"] = response.get("error") or raw.get("error") or "Task failed"
    return output


class SunoToolSpec(BaseToolSpec):
    """Suno music tools provided by Ace Data Cloud. Models are explicit; generation may consume credits.

    Constructor only configures clients. `to_tool_list()` exposes native FunctionTool objects without MCP setup.
    """

    spec_functions = [("suno_generate_music", "asuno_generate_music"), ("suno_get_task", "asuno_get_task")]

    def __init__(self, api_token: str | None = None) -> None:
        token = api_token if api_token is not None else os.environ.get("ACEDATACLOUD_API_TOKEN", "")
        token = _required(token, "ACEDATACLOUD_API_TOKEN")
        if token.lower().startswith("bearer ") or token.startswith("platform-"):
            raise ValueError(
                "Use a raw application API token, without Bearer; account-management tokens are not supported."
            )
        self._client = AceDataCloud(api_token=token, base_url=API_BASE, max_retries=0)
        self._async_client = AsyncAceDataCloud(api_token=token, base_url=API_BASE, max_retries=0)

    def suno_generate_music(self, prompt: str, model: str, instrumental: bool = False) -> dict[str, Any]:
        """Submit Suno music generation once through Ace Data Cloud; consumes account credits.

        `prompt` describes the music; `model` must be an available Suno model selected by the user.
        Returns a pending task ID, not final audio. Use suno_get_task with that ID at least 15 seconds apart.
        Do not call generation again to poll, and do not automatically retry an ambiguous submission error.
        """
        handle = self._client.suno.generate(
            prompt=_required(prompt, "prompt"),
            model=_required(model, "model"),
            action="generate",
            instrumental=instrumental,
            async_=True,
        )
        return _submitted(handle.id)

    async def asuno_generate_music(self, prompt: str, model: str, instrumental: bool = False) -> dict[str, Any]:
        """Asynchronously submit once. Poll the same task ID with suno_get_task; no automatic retries."""
        handle = await self._async_client.suno.generate(
            prompt=_required(prompt, "prompt"),
            model=_required(model, "model"),
            action="generate",
            instrumental=instrumental,
            async_=True,
        )
        return _submitted(handle.id)

    def suno_get_task(self, task_id: str) -> dict[str, Any]:
        """Read an existing Suno task through Ace Data Cloud; never submits a generation.

        Pass the exact task_id from suno_generate_music. Pending media are hidden because they are previews.
        Wait at least 15 seconds between pending queries. Final media_urls appear only after success.
        """
        task_id = _required(task_id, "task_id")
        return _result(task_id, self._client.tasks.get(task_id, service="suno"))

    async def asuno_get_task(self, task_id: str) -> dict[str, Any]:
        """Asynchronously read the same task; no resubmission and no internal polling loop."""
        task_id = _required(task_id, "task_id")
        return _result(task_id, await self._async_client.tasks.get(task_id, service="suno"))

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        self._client.close()

    async def aclose(self) -> None:
        """Close both HTTP clients after synchronous or asynchronous use."""
        self._client.close()
        await self._async_client.close()
