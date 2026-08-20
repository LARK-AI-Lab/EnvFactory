from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from src.mini import doctor
from src.mini.config import load_config
from src.mini.doctor import ModelHealthError, check_model_health


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


class _ModelHandler(BaseHTTPRequestHandler):
    api_key = "doctor-test-key"
    model = "Qwen/Qwen3-14B"
    requests: list[tuple[str, dict | None]] = []

    def _send(self, value: dict) -> None:
        encoded = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        assert self.headers["Authorization"] == f"Bearer {self.api_key}"
        self.requests.append((self.path, None))
        self._send(
            {
                "object": "list",
                "data": [{"id": self.model, "max_model_len": 16384}],
            }
        )

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        assert self.headers["Authorization"] == f"Bearer {self.api_key}"
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        self.requests.append((self.path, payload))
        self._send(
            {
                "model": self.model,
                "choices": [{"message": {"role": "assistant", "content": "OK"}}],
            }
        )

    def log_message(self, _format: str, *_args) -> None:
        return


@pytest.fixture
def model_server(monkeypatch):
    _ModelHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("VLLM_API_KEY", _ModelHandler.api_key)
    monkeypatch.setenv(
        "ENVFACTORY_MINI_TEACHER_BASE_URL",
        f"http://127.0.0.1:{server.server_address[1]}/v1",
    )
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_model_health_checks_identity_context_and_short_completion(model_server) -> None:
    config = load_config(CONFIG_PATH)

    result = check_model_health(config, timeout=2)

    assert result["healthy"] is True
    assert result["returned_model"] == _ModelHandler.model
    assert result["reported_max_model_len"] == 16384
    assert [request[0] for request in _ModelHandler.requests] == [
        "/v1/models",
        "/v1/chat/completions",
    ]
    payload = _ModelHandler.requests[1][1]
    assert payload is not None
    assert payload["max_tokens"] == 8
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert _ModelHandler.api_key not in json.dumps(result)


def test_model_health_requires_secret_without_exposing_it(monkeypatch) -> None:
    config = load_config(CONFIG_PATH)
    monkeypatch.delenv("VLLM_API_KEY", raising=False)
    with pytest.raises(ModelHealthError, match="VLLM_API_KEY.*not present"):
        check_model_health(config, timeout=0.1)


def test_collect_report_records_presence_only_and_can_pass_compatible_host(
    monkeypatch,
) -> None:
    config = load_config(CONFIG_PATH)
    secret = "never-write-this-value"
    monkeypatch.setenv("VLLM_API_KEY", secret)
    monkeypatch.setattr(doctor.sys, "version_info", (3, 12, 1))
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.os, "cpu_count", lambda: 4)
    monkeypatch.setattr(doctor, "_host_ram_bytes", lambda: 32 * doctor.GIB)
    monkeypatch.setattr(
        doctor,
        "_torch_report",
        lambda: (
            {
                "version": "2.test",
                "importable": True,
                "error": None,
                "compiled_cuda_version": "12.8",
                "cuda_available": True,
            },
            object(),
        ),
    )
    monkeypatch.setattr(
        doctor,
        "_gpu_report",
        lambda _torch: {
            "name": "NVIDIA RTX PRO 6000 Blackwell",
            "driver_version": "test",
            "total_vram_bytes": 96 * doctor.GIB,
            "free_vram_bytes": 95 * doctor.GIB,
            "compute_capability": "12.0",
            "source": "test",
        },
    )
    monkeypatch.setattr(
        doctor,
        "_package_status",
        lambda *_args, **_kwargs: {"version": "test", "importable": True, "error": None},
    )
    monkeypatch.setattr(
        doctor,
        "_disk_report",
        lambda label, path: {
            "label": label,
            "path": str(path),
            "available": True,
            "free_bytes": 25 * doctor.GIB,
        },
    )
    monkeypatch.setattr(doctor, "_installed_packages", lambda: {"example": "1.0"})

    report = doctor.collect_report(config, require_model=False)

    assert report["compatible"] is True
    assert report["required_secrets"] == [{"name": "VLLM_API_KEY", "present": True}]
    assert secret not in json.dumps(report)
    assert report["installed_packages"] == {"example": "1.0"}


def test_molab_dependency_profiles_and_launcher_are_isolated_and_safe() -> None:
    runtime = (REPOSITORY_ROOT / "requirements-molab.txt").read_text(encoding="utf-8")
    training = (REPOSITORY_ROOT / "requirements-molab-train.txt").read_text(encoding="utf-8")
    launcher = (REPOSITORY_ROOT / "src" / "serve" / "vllm_molab.sh").read_text(
        encoding="utf-8"
    )

    assert "vllm==0.8.5" not in runtime.lower()
    assert "vllm" in runtime.lower()
    assert "vllm" not in "\n".join(
        line for line in training.lower().splitlines() if not line.startswith("#")
    )
    assert "llamafactory==" in training.lower()
    assert "set -euo pipefail" in launcher
    assert "--host 127.0.0.1" in launcher
    assert "--tensor-parallel-size 1" in launcher
    assert "--api-key" not in launcher
    assert "CUDA_VISIBLE_DEVICES=0" in launcher
    assert "model_server.log" in launcher
    assert "kill -TERM" in launcher
    assert "memory returned" in launcher
    # vLLM reserves VLLM_PORT for internal networking; the API launcher uses
    # its own namespace and passes the value explicitly.
    assert not any(line.startswith("VLLM_PORT=") for line in launcher.splitlines())
    assert "MOLAB_VLLM_PORT" in launcher
    assert 'MOLAB_VLLM_EXECUTABLE="${MOLAB_VLLM_EXECUTABLE:-.venv-mini-runtime/bin/vllm}"' in launcher
