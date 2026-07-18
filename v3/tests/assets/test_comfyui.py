"""The ComfyUI-backed Image Service: patching, submit/poll/fetch, errors.

Everything is driven through a monkeypatched `comfyui._request` — the one
low-level HTTP seam — so no real sockets are opened. A committed fixture graph
(`fixtures/mini_workflow.json`) stands in for a real API-format workflow.
"""

import itertools
import json
import random
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from email.message import Message
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from typing import Any, Self

import pytest

from spf.assets import comfyui

_FIXTURES = Path(__file__).parent / "fixtures"
_MINI = _FIXTURES / "mini_workflow.json"
_MINI_REFINE = _FIXTURES / "mini_refine_workflow.json"
_PNG = b"\x89PNG\r\n\x1a\n"

# The fixture's KSampler and positive text node (see mini_workflow.json).
_SAMPLER = "5"
_POSITIVE = "2"


def _one_image_outputs(name: str = "spf_00001_.png") -> dict[str, Any]:
    return {"7": {"images": [{"filename": name, "subfolder": "", "type": "output"}]}}


class _ScriptedComfy:
    """A stand-in for `comfyui._request` recording submissions.

    Serves a `prompt_id` on `/api/prompt` (recording the submitted graph),
    a `completed` record on any poll route, and PNG bytes on `/api/view`.
    `poll_ok` decides which poll routes answer; a route it rejects raises
    `ComfyUIError`, exactly as `_request` does on a
    4xx from a server that does not serve that route.
    """

    def __init__(
        self,
        *,
        outputs: dict[str, Any] | None = None,
        poll_ok: Callable[[str], bool] = lambda _route: True,
        subfolder: str = "",
    ) -> None:
        self.submissions: list[tuple[str, dict[str, Any]]] = []
        self.calls: list[tuple[str, str | None]] = []
        self.uploads: list[tuple[tuple[str, bytes], dict[str, Any]]] = []
        self._outputs = outputs  # None ⇒ one per-job image named after the prompt_id
        self._poll_ok = poll_ok
        self._subfolder = subfolder  # what /api/upload/image echoes back
        self._counter = 0

    def reset(self) -> None:
        self.submissions.clear()
        self.calls.clear()
        self.uploads.clear()
        self._counter = 0

    def __call__(  # noqa: PLR0913  mirrors the _request seam's fixed shape
        self,
        base: str,  # noqa: ARG002  positional to match _request; unused here
        path: str,
        *,
        api_key: str | None = None,
        body: dict[str, Any] | None = None,
        upload: tuple[str, bytes] | None = None,
        raw: bool = False,
        timeout: float = 120,  # noqa: ARG002  part of the seam signature; unused
    ) -> Any:  # noqa: ANN401  mirrors _request's dynamic return
        self.calls.append((path, api_key))
        if path == "/api/upload/image":
            assert upload is not None
            self.uploads.append((upload, body or {}))
            # ComfyUI renames on collision and answers with what it stored.
            name, _blob = upload
            return {"name": name, "subfolder": self._subfolder, "type": "input"}
        if path == "/api/prompt":
            self._counter += 1
            pid = f"pid-{self._counter}"
            assert body is not None
            self.submissions.append((pid, body["prompt"]))
            return {"prompt_id": pid}
        if raw:  # /api/view — echo the requested filename so blobs are per-job
            query = urllib.parse.parse_qs(path.split("?", 1)[1])
            return _PNG + query["filename"][0].encode()
        return self._poll(path)

    def _poll(self, path: str) -> dict[str, Any]:
        route = "/history/{id}" if path.startswith("/history/") else "/api/jobs/{id}"
        if not self._poll_ok(route):
            # _request already turns a 4xx into ComfyUIError; mirror that here.
            msg = f"HTTP 404 on {path}"
            raise comfyui.ComfyUIError(msg)
        pid = path.rsplit("/", 1)[-1]
        outputs = (
            self._outputs
            if self._outputs is not None
            else _one_image_outputs(f"{pid}.png")
        )
        record = {"status": "completed", "outputs": outputs}
        return {pid: record} if path.startswith("/history/") else record


def _http_error(code: int, body: bytes = b"boom") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "err", Message(), BytesIO(body))


def _service(
    scripted: _ScriptedComfy, monkeypatch: pytest.MonkeyPatch, **kw: object
) -> comfyui.ComfyUIService:
    monkeypatch.setattr(comfyui, "_request", scripted)
    opts: dict[str, Any] = {
        "base_url": "http://server",
        "workflow_path": _MINI,
        "api_key_env": "",
        "timeout_s": 5,
    }
    return comfyui.ComfyUIService(**{**opts, **kw})


def _patched_seeds(scripted: _ScriptedComfy) -> list[int]:
    return [graph[_SAMPLER]["inputs"]["seed"] for _, graph in scripted.submissions]


def _service_for(
    graph: dict[str, Any],
    tmp_path: Path,
    *,
    scripted: _ScriptedComfy,
    monkeypatch: pytest.MonkeyPatch,
) -> comfyui.ComfyUIService:
    """Build a service whose Workflow is `graph` written to a temp file."""
    workflow = tmp_path / "wf.json"
    workflow.write_text(json.dumps(graph), encoding="utf-8")
    return _service(scripted, monkeypatch, workflow_path=workflow)


# --- Cycle 1: sub-seed derivation (ported from PollinationsService) ---------


def test_generate_derives_deterministic_distinct_seeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _service(scripted, monkeypatch)

    first = service.generate("a prompt", 3, seed=42)
    seeds_a = _patched_seeds(scripted)
    scripted.reset()
    again = service.generate("a prompt", 3, seed=42)
    seeds_b = _patched_seeds(scripted)

    rng = random.Random(42)  # noqa: S311  independent source of truth for sub-seeds
    expected = [rng.randrange(2**31) for _ in range(3)]

    assert len(first) == len(again) == 3
    assert seeds_a == seeds_b == expected  # deterministic given the base seed
    assert len(set(seeds_a)) == 3  # three distinct sub-seeds from one base


# --- Cycle 2: graph-follow patching -----------------------------------------


def test_patches_prompt_onto_positive_leaving_the_rest_authored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _service(scripted, monkeypatch)

    service.generate("a brass rat soldier", 1, seed=7)

    _, graph = scripted.submissions[0]
    expected = random.Random(7).randrange(2**31)  # noqa: S311  independent truth
    assert graph[_SAMPLER]["inputs"]["seed"] == expected  # seed on the sampler
    assert graph[_POSITIVE]["inputs"]["text"] == "a brass rat soldier"
    # Everything else stays exactly as authored (Decision 4).
    assert graph["3"]["inputs"]["text"] == "a placeholder negative prompt"
    assert graph[_SAMPLER]["inputs"]["steps"] == 20
    assert graph[_SAMPLER]["inputs"]["cfg"] == 7.0
    assert graph["1"]["inputs"]["ckpt_name"] == "model.safetensors"


def test_follows_a_linked_seed_primitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = {
        "s": {
            "class_type": "KSampler",
            "inputs": {"seed": ["p", 0], "positive": ["t", 0]},
        },
        "t": {"class_type": "CLIPTextEncode", "inputs": {"text": "placeholder"}},
        "p": {"class_type": "PrimitiveInt", "inputs": {"value": 0}},
    }
    scripted = _ScriptedComfy()
    service = _service_for(graph, tmp_path, scripted=scripted, monkeypatch=monkeypatch)

    service.generate("prompt", 1, seed=7)

    _, submitted = scripted.submissions[0]
    expected = random.Random(7).randrange(2**31)  # noqa: S311  independent truth
    assert submitted["p"]["inputs"]["value"] == expected  # upstream primitive set
    assert submitted["s"]["inputs"]["seed"] == ["p", 0]  # the link itself untouched


def test_rejects_a_workflow_with_no_sampler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = {"t": {"class_type": "CLIPTextEncode", "inputs": {"text": "x"}}}
    service = _service_for(
        graph, tmp_path, scripted=_ScriptedComfy(), monkeypatch=monkeypatch
    )

    with pytest.raises(comfyui.ComfyUIError, match="found 0"):
        service.generate("prompt", 1, seed=7)


def test_rejects_a_workflow_with_two_samplers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sampler = {"class_type": "KSampler", "inputs": {"seed": 0, "positive": ["t", 0]}}
    graph = {
        "s1": dict(sampler),
        "s2": dict(sampler),
        "t": {"class_type": "CLIPTextEncode", "inputs": {"text": "x"}},
    }
    service = _service_for(
        graph, tmp_path, scripted=_ScriptedComfy(), monkeypatch=monkeypatch
    )

    with pytest.raises(comfyui.ComfyUIError, match="found 2"):
        service.generate("prompt", 1, seed=7)


def test_rejects_a_non_text_positive_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = {
        "s": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "positive": ["c", 0]},
        },
        "c": {"class_type": "ConditioningCombine", "inputs": {"strength": 1.0}},
    }
    service = _service_for(
        graph, tmp_path, scripted=_ScriptedComfy(), monkeypatch=monkeypatch
    )

    with pytest.raises(comfyui.ComfyUIError, match="no 'text' or 'prompt' input"):
        service.generate("prompt", 1, seed=7)


def test_patches_an_encoder_that_names_its_input_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Qwen's edit encoder declares `prompt` where CLIPTextEncode declares
    # `text` (see the plan, §6). Both keys must patch.
    graph = {
        "s": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "positive": ["t", 0]},
        },
        "t": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {"prompt": "placeholder", "clip": ["c", 0]},
        },
    }
    scripted = _ScriptedComfy()
    service = _service_for(graph, tmp_path, scripted=scripted, monkeypatch=monkeypatch)

    service.generate("make the hat brass instead of leather", 1, seed=7)

    _, submitted = scripted.submissions[0]
    assert submitted["t"]["inputs"]["prompt"] == "make the hat brass instead of leather"


# --- Cycle 3: happy-path flow (N blobs, in order) ---------------------------


def test_generate_returns_one_blob_per_job_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _service(scripted, monkeypatch)

    blobs = service.generate("a prompt", 3, seed=1)

    pids = [pid for pid, _ in scripted.submissions]
    assert len(pids) == 3  # three sequential submissions
    # Each job's blob is fetched and returned in submission order.
    assert list(blobs) == [_PNG + f"{pid}.png".encode() for pid in pids]
    assert len(set(_patched_seeds(scripted))) == 3  # a distinct seed per job
    # batch_size stays as authored (one image per job); it is never patched.
    assert all(g["4"]["inputs"]["batch_size"] == 1 for _, g in scripted.submissions)


# --- Cycle 4: poll try-both-and-cache ---------------------------------------


def test_poll_tries_both_routes_then_caches_the_winner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # This server answers only /history/{id} (like a local ComfyUI).
    scripted = _ScriptedComfy(poll_ok=lambda route: route == "/history/{id}")
    service = _service(scripted, monkeypatch)

    service.generate("a prompt", 2, seed=1)

    polls = [p for p, _ in scripted.calls if "/jobs/" in p or "/history/" in p]
    # Job 1 tries /api/jobs (rejected) then /history (wins); job 2 reuses the
    # cached /history route without re-trying /api/jobs.
    assert polls == ["/api/jobs/pid-1", "/history/pid-1", "/history/pid-2"]


# --- Cycle 5: retry vs fail-fast --------------------------------------------


class _FakeResponse:
    """A minimal `urlopen` context manager returning canned bytes."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def read(self) -> bytes:
        return self._data


def test_request_retries_server_error_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes: list[object] = [_http_error(500), _FakeResponse(b'{"prompt_id": "p"}')]
    calls: list[object] = []

    def fake_urlopen(request: object, timeout: float = 120) -> _FakeResponse:  # noqa: ARG001
        result = outcomes[len(calls)]
        calls.append(request)
        if isinstance(result, Exception):
            raise result
        assert isinstance(result, _FakeResponse)
        return result

    sleeps: list[float] = []
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(comfyui.time, "sleep", sleeps.append)

    result = comfyui._request("http://x", "/api/prompt", body={})

    assert result == {"prompt_id": "p"}
    assert len(calls) == 2  # one failure, then success
    assert len(sleeps) == 1  # backed off once before the retry


def test_request_fails_fast_on_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_urlopen(request: object, timeout: float = 120) -> _FakeResponse:  # noqa: ARG001
        calls.append(request)
        raise _http_error(400, b"bad request body")

    sleeps: list[float] = []
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(comfyui.time, "sleep", sleeps.append)

    with pytest.raises(comfyui.ComfyUIError, match="bad request body"):
        comfyui._request("http://x", "/api/prompt", body={})
    assert len(calls) == 1  # failed fast, no retry
    assert sleeps == []


# --- Cycle 3: multipart upload of a Refinement's init image ------------------


def _captured_multipart(
    monkeypatch: pytest.MonkeyPatch, response: bytes
) -> list[urllib.request.Request]:
    """Capture the `Request` objects `_request` hands to `urlopen`."""
    calls: list[urllib.request.Request] = []

    def fake_urlopen(
        request: urllib.request.Request,
        timeout: float = 120,  # noqa: ARG001  part of the urlopen signature
    ) -> _FakeResponse:
        calls.append(request)
        return _FakeResponse(response)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


def _parse_multipart(request: urllib.request.Request) -> dict[str, Message]:
    """Re-parse a captured request as MIME, the way a server would.

    Returns the form parts by field name, so the encoder is checked against
    the stdlib's parser rather than against itself.
    """
    assert isinstance(request.data, bytes)
    headers = f"Content-Type: {request.get_header('Content-type')}\r\n\r\n".encode()
    payload = BytesParser().parsebytes(headers + request.data).get_payload()
    assert isinstance(payload, list)
    parts: dict[str, Message] = {}
    for part in payload:
        assert isinstance(part, Message)
        name = part.get_param("name", header="content-disposition")
        assert isinstance(name, str)
        parts[name] = part
    return parts


def test_request_posts_an_upload_as_multipart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The init image is uploaded as a real multipart/form-data body built on
    # the stdlib — no HTTP dependency.
    calls = _captured_multipart(monkeypatch, b'{"name": "init.png"}')

    result = comfyui._request(
        "http://x",
        "/api/upload/image",
        upload=("init.png", _PNG),
        body={"overwrite": "true"},
    )

    assert result == {"name": "init.png"}
    (request,) = calls
    assert request.get_header("Content-type", "").startswith("multipart/form-data;")

    parts = _parse_multipart(request)
    assert set(parts) == {"image", "overwrite"}
    assert parts["image"].get_filename() == "init.png"
    assert parts["image"].get_payload(decode=True) == _PNG
    assert parts["overwrite"].get_payload(decode=True) == b"true"


def test_upload_adds_no_http_dependency() -> None:
    # ADR 0009: the ComfyUI client is stdlib-only. Multipart encoding is not a
    # reason to take on an HTTP library.
    pyproject = (Path(__file__).parents[2] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    declared = pyproject.split("dependencies = [", 1)[1].split("]", 1)[0]
    assert not {"requests", "httpx", "aiohttp", "urllib3"} & set(
        declared.replace('"', " ").replace(",", " ").split()
    )


def test_generate_raises_on_failed_status_carrying_node_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(base: str, path: str, **_: object) -> Any:  # noqa: ANN401, ARG001
        if path == "/api/prompt":
            return {"prompt_id": "pid"}
        return {"status": "failed", "node_errors": {"5": "OOM loading KSampler"}}

    monkeypatch.setattr(comfyui, "_request", fake)
    service = comfyui.ComfyUIService(
        base_url="http://x", workflow_path=_MINI, api_key_env="", timeout_s=5
    )

    with pytest.raises(comfyui.ComfyUIError, match="OOM loading KSampler"):
        service.generate("a prompt", 1, seed=1)


def test_generate_raises_when_completed_with_no_images(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy(outputs={})  # completed, but no images
    service = _service(scripted, monkeypatch)

    with pytest.raises(comfyui.ComfyUIError, match="no images"):
        service.generate("a prompt", 1, seed=1)


def test_generate_raises_on_poll_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(base: str, path: str, **_: object) -> Any:  # noqa: ANN401, ARG001
        if path == "/api/prompt":
            return {"prompt_id": "pid"}
        return {"status": "running"}  # never completes

    # Cross the deadline after one poll pass; make the backoff sleep a no-op.
    clock = itertools.chain([0.0, 0.0], itertools.repeat(100.0))
    monkeypatch.setattr(comfyui, "_request", fake)
    monkeypatch.setattr(comfyui.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(comfyui.time, "sleep", lambda _: None)
    service = comfyui.ComfyUIService(
        base_url="http://x", workflow_path=_MINI, api_key_env="", timeout_s=1
    )

    with pytest.raises(comfyui.ComfyUIError, match="timed out"):
        service.generate("a prompt", 1, seed=1)


# --- Cycle 6: lazy API key --------------------------------------------------


def test_sends_api_key_header_when_env_var_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPF_TEST_KEY", "secret-123")
    scripted = _ScriptedComfy()
    service = _service(scripted, monkeypatch, api_key_env="SPF_TEST_KEY")

    service.generate("a prompt", 1, seed=1)

    assert {key for _, key in scripted.calls} == {"secret-123"}


def test_omits_api_key_when_env_name_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _service(scripted, monkeypatch, api_key_env="")

    service.generate("a prompt", 1, seed=1)

    assert all(key is None for _, key in scripted.calls)


def test_api_key_is_read_lazily_at_generate_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SPF_TEST_KEY", raising=False)
    scripted = _ScriptedComfy()
    # The env var is unset when the service is constructed...
    service = _service(scripted, monkeypatch, api_key_env="SPF_TEST_KEY")
    # ...and exported only afterwards, as a user would after importing the CLI.
    monkeypatch.setenv("SPF_TEST_KEY", "exported-later")

    service.generate("a prompt", 1, seed=1)

    assert {key for _, key in scripted.calls} == {"exported-later"}


# --- Cycle 5: refine (upload -> patch init image -> submit/poll/fetch) ------

_INIT = _PNG + b"the candidate being refined"

# The refine fixture's LoadImage and positive encoder (mini_refine_workflow).
_LOAD_IMAGE = "4"
_REFINE_POSITIVE = "6"


def _refine_service(
    scripted: _ScriptedComfy,
    monkeypatch: pytest.MonkeyPatch,
    **kw: object,
) -> comfyui.ComfyUIService:
    return _service(
        scripted, monkeypatch, **{"refine_workflow_path": _MINI_REFINE, **kw}
    )


def test_refine_uploads_the_init_image_and_points_load_image_at_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _refine_service(scripted, monkeypatch)

    service.refine("make the hat brass", _INIT, 1, seed=7)

    (filename, blob), fields = scripted.uploads[0]
    assert blob == _INIT  # the candidate's own bytes are what get uploaded
    assert fields["overwrite"] == "true"  # refining twice must not pile up "foo (1)"
    _, graph = scripted.submissions[0]
    # The sole LoadImage now names the file the server said it stored.
    assert graph[_LOAD_IMAGE]["inputs"]["image"] == filename


def test_refine_qualifies_the_init_filename_with_a_subfolder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ComfyUI may store the upload under a subfolder; LoadImage then needs the
    # qualified "sub/name.png" form, not the bare name.
    scripted = _ScriptedComfy(subfolder="spf")
    service = _refine_service(scripted, monkeypatch)

    service.refine("make the hat brass", _INIT, 1, seed=7)

    (name, _blob), _fields = scripted.uploads[0]
    _, graph = scripted.submissions[0]
    assert graph[_LOAD_IMAGE]["inputs"]["image"] == f"spf/{name}"


def test_refine_patches_the_correction_verbatim_as_the_positive_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _refine_service(scripted, monkeypatch)

    service.refine("make the hat brass instead of leather", _INIT, 1, seed=7)

    _, graph = scripted.submissions[0]
    # Verbatim: no scene description, no wrapper (the plan, §5).
    correction = "make the hat brass instead of leather"
    assert graph[_REFINE_POSITIVE]["inputs"]["prompt"] == correction
    expected = random.Random(7).randrange(2**31)  # noqa: S311  independent truth
    assert graph["9"]["inputs"]["seed"] == expected
    # The standing guardrail and the authored stack are left alone.
    assert graph["7"]["inputs"]["prompt"] == "a placeholder negative prompt"
    assert graph["1"]["inputs"]["unet_name"] == "edit-model.safetensors"
    assert graph["9"]["inputs"]["steps"] == 4


def test_refine_returns_one_blob_per_sub_seed_uploading_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _refine_service(scripted, monkeypatch)

    blobs = service.refine("make the hat brass", _INIT, 3, seed=1)

    pids = [pid for pid, _ in scripted.submissions]
    assert len(pids) == 3  # three variants of the one Correction
    assert list(blobs) == [_PNG + f"{pid}.png".encode() for pid in pids]
    assert len(scripted.uploads) == 1  # the init image is uploaded once per batch
    seeds = [g["9"]["inputs"]["seed"] for _, g in scripted.submissions]
    assert len(set(seeds)) == 3


def test_refine_streams_each_blob_to_on_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted = _ScriptedComfy()
    service = _refine_service(scripted, monkeypatch)
    seen: list[bytes | str] = []

    blobs = service.refine(
        "make the hat brass", _INIT, 2, seed=1, on_result=seen.append
    )

    assert seen == list(blobs)  # saved as they arrive, not at the end of the batch


def test_refine_rejects_a_workflow_with_no_load_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = json.loads(_MINI_REFINE.read_text(encoding="utf-8"))
    del graph[_LOAD_IMAGE]
    workflow = tmp_path / "no-load-image.json"
    workflow.write_text(json.dumps(graph), encoding="utf-8")
    service = _refine_service(
        _ScriptedComfy(), monkeypatch, refine_workflow_path=workflow
    )

    with pytest.raises(comfyui.ComfyUIError, match="found 0"):
        service.refine("make the hat brass", _INIT, 1, seed=7)


def test_refine_rejects_a_workflow_with_two_load_images(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Qwen-Image-Edit's stock template ships two or three LoadImage nodes; a
    # refine Workflow must be reduced to exactly one (the plan, §6).
    graph = json.loads(_MINI_REFINE.read_text(encoding="utf-8"))
    graph["4b"] = dict(graph[_LOAD_IMAGE])
    workflow = tmp_path / "two-load-images.json"
    workflow.write_text(json.dumps(graph), encoding="utf-8")
    service = _refine_service(
        _ScriptedComfy(), monkeypatch, refine_workflow_path=workflow
    )

    with pytest.raises(comfyui.ComfyUIError, match="found 2"):
        service.refine("make the hat brass", _INIT, 1, seed=7)
