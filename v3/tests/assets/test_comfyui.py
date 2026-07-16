"""The ComfyUI-backed Image Service: patching, submit/poll/fetch, errors.

Everything is driven through a monkeypatched :func:`comfyui._request` — the one
low-level HTTP seam — so no real sockets are opened. A committed fixture graph
(``fixtures/mini_workflow.json``) stands in for a real API-format workflow.
"""

import json
import random
import urllib.error
from collections.abc import Callable
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from spf.assets import comfyui

_FIXTURES = Path(__file__).parent / "fixtures"
_MINI = _FIXTURES / "mini_workflow.json"
_PNG = b"\x89PNG\r\n\x1a\n"

# The fixture's KSampler and positive text node (see mini_workflow.json).
_SAMPLER = "5"
_POSITIVE = "2"


def _one_image_outputs(name: str = "spf_00001_.png") -> dict[str, Any]:
    return {"7": {"images": [{"filename": name, "subfolder": "", "type": "output"}]}}


class _ScriptedComfy:
    """A stand-in for :func:`comfyui._request` recording submissions.

    Serves a ``prompt_id`` on ``/api/prompt`` (recording the submitted graph),
    a ``completed`` record on any poll route, and PNG bytes on ``/api/view``.
    ``poll_ok`` decides which poll routes answer; a route it rejects raises a
    404 :class:`~urllib.error.HTTPError`, exactly as a real server would.
    """

    def __init__(
        self,
        *,
        outputs: dict[str, Any] | None = None,
        poll_ok: Callable[[str], bool] = lambda _route: True,
    ) -> None:
        self.submissions: list[tuple[str, dict[str, Any]]] = []
        self.calls: list[tuple[str, str | None]] = []
        self._outputs = _one_image_outputs() if outputs is None else outputs
        self._poll_ok = poll_ok
        self._counter = 0

    def reset(self) -> None:
        self.submissions.clear()
        self.calls.clear()
        self._counter = 0

    def __call__(  # noqa: PLR0913  mirrors the _request seam's fixed shape
        self,
        base: str,  # noqa: ARG002  positional to match _request; unused here
        path: str,
        *,
        api_key: str | None = None,
        body: dict[str, Any] | None = None,
        raw: bool = False,
        timeout: float = 120,  # noqa: ARG002  part of the seam signature; unused
    ) -> Any:  # noqa: ANN401  mirrors _request's dynamic return
        self.calls.append((path, api_key))
        if path == "/api/prompt":
            self._counter += 1
            pid = f"pid-{self._counter}"
            assert body is not None
            self.submissions.append((pid, body["prompt"]))
            return {"prompt_id": pid}
        if raw:  # /api/view
            return _PNG + b"fake-image-bytes"
        return self._poll(path)

    def _poll(self, path: str) -> dict[str, Any]:
        route = "/history/{id}" if path.startswith("/history/") else "/api/jobs/{id}"
        if not self._poll_ok(route):
            raise _http_error(404)
        pid = path.rsplit("/", 1)[-1]
        record = {"status": "completed", "outputs": self._outputs}
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
    scripted: _ScriptedComfy,
    monkeypatch: pytest.MonkeyPatch,
) -> comfyui.ComfyUIService:
    """Build a service whose Workflow is ``graph`` written to a temp file."""
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
    service = _service_for(graph, tmp_path, scripted, monkeypatch)

    service.generate("prompt", 1, seed=7)

    _, submitted = scripted.submissions[0]
    expected = random.Random(7).randrange(2**31)  # noqa: S311  independent truth
    assert submitted["p"]["inputs"]["value"] == expected  # upstream primitive set
    assert submitted["s"]["inputs"]["seed"] == ["p", 0]  # the link itself untouched


def test_rejects_a_workflow_with_no_sampler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = {"t": {"class_type": "CLIPTextEncode", "inputs": {"text": "x"}}}
    service = _service_for(graph, tmp_path, _ScriptedComfy(), monkeypatch)

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
    service = _service_for(graph, tmp_path, _ScriptedComfy(), monkeypatch)

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
    service = _service_for(graph, tmp_path, _ScriptedComfy(), monkeypatch)

    with pytest.raises(comfyui.ComfyUIError, match="no 'text' input"):
        service.generate("prompt", 1, seed=7)
