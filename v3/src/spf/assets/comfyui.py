"""The ComfyUI-backed Image Service: one stdlib client for local and cloud.

Turns a composed prompt into `count` PNG blobs by submitting an authored
ComfyUI **Workflow** (an API-format graph) to a configured **Environment**
(local ComfyUI or Comfy Cloud). Only the positive prompt and a per-job seed are
patched into the graph; the model, steps, cfg, LoRAs, and negative prompt stay
exactly as authored (see ADR 0009 and its amendment).

All network I/O funnels through the single `_request` seam, so tests
monkeypatch exactly that one function. Stdlib only — the prototype proved a
dependency is unnecessary.
"""

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

SAMPLER_CLASSES = ("KSampler", "KSamplerAdvanced")
_MAX_ATTEMPTS = 4  # one initial try plus three retries (from PollinationsService)
_BACKOFF_BASE = 1.0  # seconds, doubled each retry: 1s, 2s, 4s
_SERVER_ERROR = 500
_POLL_INTERVAL = 2.0
_SEED_BOUND = 2**31
_POLL_ROUTES = ("/api/jobs/{id}", "/history/{id}")  # try-both order

# Upstream primitive keys a scalar link might carry its value under.
_PRIMITIVE_KEYS = ("value", "seed", "int", "number")


class ComfyUIError(Exception):
    """A ComfyUI failure to surface as a clean CLI message, not a traceback.

    Raised for an execution `failed` status (carrying ComfyUI's
    `node_errors`), a timeout, a completed job with no images, and an
    unpatchable Workflow. Transient network failures are `urllib` errors
    and are handled by retry inside `_request`, not raised as this.
    """


def _request(  # noqa: PLR0913  the single HTTP seam's shape is fixed (see the plan)
    base: str,
    path: str,
    *,
    api_key: str | None = None,
    body: dict[str, Any] | None = None,
    raw: bool = False,
    timeout: float = 120,
) -> Any:  # noqa: ANN401  parsed JSON (dict/list) or raw bytes, by design
    """Perform one ComfyUI HTTP call — the sole network seam.

    JSON-encodes `body` (setting `Content-Type`) when present and adds an
    `X-API-Key` header when `api_key` is given. Retries transient failures
    (5xx and connection errors) with exponential backoff up to
    `_MAX_ATTEMPTS`; 4xx client errors fail fast. Returns parsed JSON, or
    raw `bytes` when `raw` is set (for `/api/view`).
    """
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(_MAX_ATTEMPTS):
        request = urllib.request.Request(url, data=data)  # noqa: S310  configured host
        if body is not None:
            request.add_header("Content-Type", "application/json")
        if api_key:
            request.add_header("X-API-Key", api_key)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                payload = response.read()
                return payload if raw else json.loads(payload)
        except urllib.error.HTTPError as err:
            if err.code < _SERVER_ERROR:  # 4xx: bad key/request, not transient
                detail = err.read().decode("utf-8", "replace")[:2000]
                msg = f"HTTP {err.code} on {path}: {detail}"
                raise ComfyUIError(msg) from None
            if attempt == _MAX_ATTEMPTS - 1:
                raise  # out of retries on a 5xx
        except urllib.error.URLError:
            if attempt == _MAX_ATTEMPTS - 1:
                raise  # out of retries on a connection error
        time.sleep(_BACKOFF_BASE * 2**attempt)

    msg = "unreachable: the retry loop always returns or raises"
    raise RuntimeError(msg)  # pragma: no cover


# --- Workflow graph helpers (title- and id-independent, ported from probe) ---


def _load_workflow(path: Path) -> dict[str, Any]:
    """Read and parse `path` as an API-format Workflow graph.

    An API-format graph is a dict of nodes, each carrying `class_type`. A
    plain (UI-format) export is not runnable; raise `ComfyUIError`
    telling the user to "Save (API Format)".
    """
    graph = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or not all(
        isinstance(node, dict) and "class_type" in node for node in graph.values()
    ):
        msg = (
            f"{path} is not an API-format Workflow. In ComfyUI use "
            "'Save (API Format)', not the plain 'Save' (that exports UI format)."
        )
        raise ComfyUIError(msg)
    return graph


def _nodes_of_class(graph: dict[str, Any], *classes: str) -> list[str]:
    return [nid for nid, node in graph.items() if node.get("class_type") in classes]


def _sole_node_of_class(
    graph: dict[str, Any], classes: Sequence[str], what: str
) -> str:
    """Return the id of the one node of `classes`; raise unless exactly one."""
    hits = _nodes_of_class(graph, *classes)
    if len(hits) != 1:
        msg = f"expected exactly 1 {what} node, found {len(hits)}: {hits}"
        raise ComfyUIError(msg)
    return hits[0]


def _set_scalar_or_upstream(
    graph: dict[str, Any], node_id: str, key: str, value: object
) -> bool:
    """Set `inputs[key]` to `value`, following a link to its primitive.

    A link is `["<node_id>", slot]`; a literal is anything else. When the
    input is a link, patch the upstream primitive's value instead. Returns
    whether a value was set (`False` if the input is absent).
    """
    inputs = graph[node_id]["inputs"]
    if key not in inputs:
        return False
    current = inputs[key]
    if isinstance(current, list):  # a link -> patch the upstream primitive
        upstream = graph[current[0]]["inputs"]
        for candidate in (*_PRIMITIVE_KEYS, key):
            if candidate in upstream:
                upstream[candidate] = value
                return True
        return False
    inputs[key] = value
    return True


def _patch_prompt_and_seed(graph: dict[str, Any], *, prompt: str, seed: int) -> None:
    """Patch only the positive prompt and the seed, by graph-follow.

    Locates the sole sampler, patches its seed (following a linked primitive),
    then follows its `positive` link to the text node and sets `text`.
    Everything else — model, steps, cfg, LoRAs, negative — is left untouched.
    Raises `ComfyUIError` on an unpatchable graph.
    """
    sid = _sole_node_of_class(graph, SAMPLER_CLASSES, "sampler")
    inputs = graph[sid]["inputs"]

    seed_key = "seed" if "seed" in inputs else "noise_seed"
    if not _set_scalar_or_upstream(graph, sid, seed_key, seed):
        msg = f"could not find a seed input on sampler {sid}"
        raise ComfyUIError(msg)

    positive = inputs.get("positive")
    if not isinstance(positive, list):
        msg = "sampler's 'positive' input is not a link to a text node"
        raise ComfyUIError(msg)
    text_node = graph[positive[0]]["inputs"]
    if "text" not in text_node:
        klass = graph[positive[0]]["class_type"]
        msg = f"positive node {klass} has no 'text' input to patch"
        raise ComfyUIError(msg)
    text_node["text"] = prompt


# --- Submit / poll / fetch ---------------------------------------------------


def _submit(base: str, api_key: str | None, graph: dict[str, Any]) -> str:
    """Queue `graph` via `/api/prompt` and return its `prompt_id`."""
    response = _request(
        base,
        "/api/prompt",
        api_key=api_key,
        body={"prompt": graph, "client_id": str(uuid.uuid4())},
    )
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        msg = f"no prompt_id in submit response: {response}"
        raise ComfyUIError(msg)
    return prompt_id


def _record_state(record: dict[str, Any]) -> str | None:
    status = record.get("status")
    return status.get("status_str") if isinstance(status, dict) else status


def _poll(
    base: str,
    api_key: str | None,
    prompt_id: str,
    *,
    timeout_s: float,
    cached_route: str | None,
) -> tuple[dict[str, Any], str]:
    """Poll until the job completes, returning `(record, route)`.

    Tries `cached_route` if known, else each of `_POLL_ROUTES` in order
    until one answers 200 — that becomes the cached route for the batch. The two
    shapes are normalized: `/history/{id}` nests under the prompt_id,
    `/api/jobs/{id}` does not. Raises `ComfyUIError` on a `failed`
    status or on timeout.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        routes = (cached_route,) if cached_route else _POLL_ROUTES
        for route in routes:
            path = route.replace("{id}", prompt_id)
            try:
                data = _request(base, path, api_key=api_key, timeout=30)
            except ComfyUIError:
                continue  # this route not served here; try the next
            cached_route = route
            record = data.get(prompt_id, data) if isinstance(data, dict) else data
            state = _record_state(record)
            if state in ("failed", "error"):
                msg = f"ComfyUI job failed: {json.dumps(record)[:1500]}"
                raise ComfyUIError(msg)
            if record.get("outputs") or state == "completed":
                return record, route
        time.sleep(_POLL_INTERVAL)

    msg = f"timed out after {timeout_s}s waiting for {prompt_id}"
    raise ComfyUIError(msg)


def _fetch_images(
    base: str, api_key: str | None, record: dict[str, Any]
) -> list[bytes]:
    """Fetch every non-`temp` output image of `record` via `/api/view`."""
    images = [
        image
        for node in record.get("outputs", {}).values()
        for image in node.get("images", [])
        if image.get("type") != "temp"
    ]
    if not images:
        msg = f"job completed but produced no images: {record.get('outputs')}"
        raise ComfyUIError(msg)
    blobs = []
    for image in images:
        query = urllib.parse.urlencode(
            {
                "filename": image["filename"],
                "subfolder": image.get("subfolder", ""),
                "type": image.get("type", "output"),
            }
        )
        blobs.append(_request(base, f"/api/view?{query}", api_key=api_key, raw=True))
    return blobs


class ComfyUIService:
    """A `Service` that renders images via ComfyUI.

    Constructed from one Environment's config; touches neither the network nor
    the Workflow file until `generate`. The API key is read lazily, per
    call, from the environment variable named by `api_key_env` (empty ⇒ no
    auth header), so it can be exported after import.
    """

    def __init__(
        self,
        *,
        base_url: str,
        workflow_path: Path,
        api_key_env: str,
        timeout_s: int,
    ) -> None:
        """Store one Environment's config; read nothing until `generate`."""
        self._base_url = base_url
        self._workflow_path = workflow_path
        self._api_key_env = api_key_env
        self._timeout_s = timeout_s

    def generate(
        self,
        source: str,
        count: int,
        *,
        seed: int | None = None,
        on_result: Callable[[bytes | str], None] | None = None,
    ) -> Sequence[bytes]:
        """Render `count` images for the `source` prompt, one per sub-seed.

        Each job's image is fetched as it completes; `on_result` (when given)
        is called with that blob right away, so the caller can save it before the
        next job is submitted, rather than at the end of the batch.
        """
        graph = _load_workflow(self._workflow_path)
        api_key = os.environ.get(self._api_key_env) if self._api_key_env else None
        api_key = api_key or None
        rng = random.Random(seed)  # noqa: S311  image seeds, not cryptographic
        sub_seeds = [rng.randrange(_SEED_BOUND) for _ in range(count)]

        cached_route: str | None = None
        blobs: list[bytes] = []
        for sub_seed in sub_seeds:
            job_graph = json.loads(json.dumps(graph))  # per-job copy
            _patch_prompt_and_seed(job_graph, prompt=source, seed=sub_seed)
            prompt_id = _submit(self._base_url, api_key, job_graph)
            record, cached_route = _poll(
                self._base_url,
                api_key,
                prompt_id,
                timeout_s=self._timeout_s,
                cached_route=cached_route,
            )
            for blob in _fetch_images(self._base_url, api_key, record):
                if on_result is not None:
                    on_result(blob)
                blobs.append(blob)
        return blobs
