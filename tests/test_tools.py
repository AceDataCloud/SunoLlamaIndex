import json

import pytest
import respx
from acedatacloud import APIError, AuthenticationError, ModerationError, RateLimitError
from llama_index.core.tools import FunctionTool

from llama_index.tools.suno_acedatacloud import SunoToolSpec

BASE = "https://api.acedata.cloud"


@pytest.fixture
async def spec():
    tool_spec = SunoToolSpec(api_token="synthetic-key")
    yield tool_spec
    await tool_spec.aclose()


def test_native_metadata_and_no_secret_schema(spec):
    tools = spec.to_tool_list()
    assert all(isinstance(t, FunctionTool) for t in tools)
    assert [t.metadata.name for t in tools] == ["suno_generate_music", "suno_get_task"]
    schema = tools[0].metadata.get_parameters_dict()
    assert set(schema["required"]) == {"prompt", "model"}
    assert "api_token" not in json.dumps(schema)
    assert "synthetic-key" not in str(spec)
    assert "Suno" in tools[0].metadata.description


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_native_submit_once_and_query_same_id(spec, asynchronous):
    with respx.mock(assert_all_mocked=True) as router:
        generation = router.post(BASE + "/suno/audios").respond(200, json={"task_id": "task-123"})
        query = router.post(BASE + "/suno/tasks").respond(
            200,
            json={
                "id": "task-123",
                "trace_id": "trace-123",
                "response": {"success": True, "data": [{"audio_url": "https://example.com/final.mp3"}]},
            },
        )
        generate, retrieve = spec.to_tool_list()
        kwargs = {"prompt": "piano", "model": "explicit-model", "instrumental": True}
        result = (await generate.acall(**kwargs) if asynchronous else generate.call(**kwargs)).raw_output
        assert result["status"] == "pending" and result["media_urls"] == []
        assert generation.call_count == 1
        assert json.loads(generation.calls[0].request.content) == {
            "action": "generate",
            "prompt": "piano",
            "model": "explicit-model",
            "instrumental": True,
            "async": True,
        }
        assert generation.calls[0].request.headers["Authorization"] == "Bearer synthetic-key"
        final = (
            await retrieve.acall(task_id=result["task_id"])
            if asynchronous
            else retrieve.call(task_id=result["task_id"])
        ).raw_output
        assert final == {
            "task_id": "task-123",
            "status": "succeeded",
            "success": True,
            "media_urls": ["https://example.com/final.mp3"],
            "trace_id": "trace-123",
            "polling_interval_seconds": None,
        }
        assert json.loads(query.calls[0].request.content) == {"id": "task-123", "action": "retrieve"}
        assert len(router.calls) == 2


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"state": "processing", "response": {"data": [{"audio_url": "https://example.com/preview.mp3"}]}}, "pending"),
        (
            {
                "state": "processing",
                "response": {"success": True, "data": [{"audio_url": "https://example.com/preview.mp3"}]},
            },
            "pending",
        ),
        ({"response": {}}, "pending"),
        (
            {
                "state": "failed",
                "response": {"success": True, "data": [{"audio_url": "https://example.com/preview.mp3"}]},
            },
            "failed",
        ),
        ({"response": {"success": False, "error": {"code": "moderated"}}}, "failed"),
    ],
)
async def test_pending_previews_and_failed_tasks_are_not_final(spec, payload, expected):
    with respx.mock(assert_all_mocked=True) as router:
        router.post(BASE + "/suno/tasks").respond(200, json=payload)
        result = spec.suno_get_task("existing-task")
        assert result["status"] == expected
        assert result["media_urls"] == []
        assert len(router.calls) == 1
        if expected == "failed":
            assert result["success"] is False and result["error"]


@pytest.mark.parametrize(
    "status,exception", [(401, AuthenticationError), (403, ModerationError), (429, RateLimitError), (500, APIError)]
)
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_generation_errors_preserve_meaning_and_never_retry(spec, status, exception, asynchronous):
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(BASE + "/suno/audios").respond(status, json={"error": {"message": "rejected"}})
        with pytest.raises(exception):
            if asynchronous:
                await spec.asuno_generate_music("piano", "explicit-model")
            else:
                spec.suno_generate_music("piano", "explicit-model")
        assert route.call_count == 1


@pytest.mark.parametrize("kwargs", [{"prompt": "", "model": "model"}, {"prompt": "piano", "model": ""}])
async def test_missing_input_never_sends_request(spec, kwargs):
    with respx.mock(assert_all_mocked=True) as router:
        with pytest.raises(ValueError):
            spec.suno_generate_music(**kwargs)
        assert not router.calls


@pytest.mark.parametrize("token", ["", " ", "Bearer key", "platform-account-token"])
def test_credential_preflight(monkeypatch, token):
    monkeypatch.delenv("ACEDATACLOUD_API_TOKEN", raising=False)
    with pytest.raises(ValueError):
        SunoToolSpec(api_token=token)


async def test_environment_credential(monkeypatch):
    monkeypatch.setenv("ACEDATACLOUD_API_TOKEN", "environment-key")
    spec = SunoToolSpec()
    spec.close()
    await spec.aclose()


async def test_missing_task_id_never_retries(spec):
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(BASE + "/suno/audios").respond(200, json={"success": True})
        with pytest.raises(RuntimeError, match="do not automatically resubmit"):
            spec.suno_generate_music("piano", "explicit-model")
        assert route.call_count == 1


@pytest.mark.parametrize(
    "response",
    [None, {"success": True, "data": []}, {"success": True, "data": [{"audio_url": "file:///tmp/fake.mp3"}]}],
)
async def test_incomplete_response_is_not_final(spec, response):
    with respx.mock(assert_all_mocked=True) as router:
        router.post(BASE + "/suno/tasks").respond(200, json={"response": response})
        with pytest.raises(ValueError):
            spec.suno_get_task("existing-task")
        assert len(router.calls) == 1


async def test_query_auth_failure_preserved(spec):
    with respx.mock(assert_all_mocked=True) as router:
        router.post(BASE + "/suno/tasks").respond(401, json={"error": {"message": "bad key"}})
        with pytest.raises(AuthenticationError):
            await spec.asuno_get_task("existing-task")
        assert len(router.calls) == 1


async def test_empty_query_id_never_sends(spec):
    with respx.mock(assert_all_mocked=True) as router:
        with pytest.raises(ValueError):
            spec.suno_get_task(" ")
        assert not router.calls


async def test_function_agent_accepts_native_tools_without_model_request(spec):
    from llama_index.core.agent.workflow import FunctionAgent
    from llama_index.core.llms import MockLLM

    with respx.mock(assert_all_mocked=True) as router:
        agent = FunctionAgent(llm=MockLLM(), tools=spec.to_tool_list())
        assert [tool.metadata.name for tool in agent.tools] == ["suno_generate_music", "suno_get_task"]
        assert not router.calls
