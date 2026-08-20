"""Read-only compatibility and model-health checks for EnvFactory Mini."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

from .config import MiniConfig, MiniConfigError, load_config


GIB = 1024**3
MINIMUM_FREE_DISK_BYTES = 10 * GIB
LOW_FREE_DISK_BYTES = 20 * GIB
MINIMUM_HOST_RAM_BYTES = 30 * GIB
MINIMUM_GPU_VRAM_BYTES = 90 * GIB
MINIMUM_CUDA_VERSION = (12, 8)
MINIMUM_COMPUTE_CAPABILITY = (12, 0)


class DoctorError(RuntimeError):
    """Raised when a doctor probe cannot be completed safely."""


class ModelHealthError(DoctorError):
    """Raised when the configured OpenAI-compatible endpoint is unhealthy."""


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    parts: list[int] = []
    for component in value.split("."):
        digits = "".join(character for character in component if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def _nearest_existing(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _host_ram_bytes() -> int | None:
    try:
        import psutil  # type: ignore[import-not-found]

        return int(psutil.virtual_memory().total)
    except (ImportError, OSError, ValueError):
        pass
    if hasattr(os, "sysconf"):
        try:
            return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
        except (OSError, ValueError):
            pass
    return None


def _disk_report(label: str, path: Path) -> dict[str, Any]:
    probe = _nearest_existing(path)
    try:
        usage = shutil.disk_usage(probe)
        return {
            "label": label,
            "path": str(path),
            "probe_path": str(probe),
            "total_bytes": usage.total,
            "free_bytes": usage.free,
            "available": True,
        }
    except OSError as exc:
        return {
            "label": label,
            "path": str(path),
            "probe_path": str(probe),
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _path_report(label: str, path: Path, *, output: bool) -> dict[str, Any]:
    probe = _nearest_existing(path if output else path.parent)
    exists = path.exists()
    writable = os.access(probe, os.W_OK)
    return {
        "label": label,
        "path": str(path),
        "kind": "output" if output else "input",
        "exists": exists,
        "writable": writable,
        "ok": writable if output else exists,
    }


def _package_status(distribution: str, module: str, *, import_module: bool) -> dict[str, Any]:
    try:
        version = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        version = None
    error = None
    importable = False
    try:
        if import_module:
            importlib.import_module(module)
        elif importlib.util.find_spec(module) is None:
            raise ImportError(f"module {module!r} was not found")
        importable = True
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"version": version, "importable": importable, "error": error}


def _installed_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            packages[name] = distribution.version
    return dict(sorted(packages.items(), key=lambda item: item[0].lower()))


def _torch_report() -> tuple[dict[str, Any], Any | None]:
    report = _package_status("torch", "torch", import_module=True)
    if not report["importable"]:
        report.update({"compiled_cuda_version": None, "cuda_available": False})
        return report, None
    torch = sys.modules["torch"]
    report.update(
        {
            "version": str(torch.__version__),
            "compiled_cuda_version": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
        }
    )
    return report, torch


def _nvidia_smi_gpu() -> dict[str, Any] | None:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    command = [
        executable,
        "--query-gpu=name,driver_version,memory.total,memory.free,compute_cap",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    first_line = next((line for line in completed.stdout.splitlines() if line.strip()), "")
    fields = [field.strip() for field in first_line.split(",")]
    if len(fields) != 5:
        return None
    try:
        total_bytes = int(float(fields[2]) * 1024**2)
        free_bytes = int(float(fields[3]) * 1024**2)
    except ValueError:
        return None
    return {
        "name": fields[0],
        "driver_version": fields[1],
        "total_vram_bytes": total_bytes,
        "free_vram_bytes": free_bytes,
        "compute_capability": fields[4],
        "source": "nvidia-smi",
    }


def _gpu_report(torch: Any | None) -> dict[str, Any]:
    report = _nvidia_smi_gpu()
    if report is not None:
        return report
    if torch is None or not torch.cuda.is_available():
        return {
            "name": None,
            "driver_version": None,
            "total_vram_bytes": None,
            "free_vram_bytes": None,
            "compute_capability": None,
            "source": None,
        }
    try:
        free_bytes, total_bytes = torch.cuda.mem_get_info(0)
        capability = torch.cuda.get_device_capability(0)
        return {
            "name": torch.cuda.get_device_name(0),
            "driver_version": None,
            "total_vram_bytes": int(total_bytes),
            "free_vram_bytes": int(free_bytes),
            "compute_capability": f"{capability[0]}.{capability[1]}",
            "source": "torch",
        }
    except (RuntimeError, ValueError) as exc:
        return {
            "name": None,
            "driver_version": None,
            "total_vram_bytes": None,
            "free_vram_bytes": None,
            "compute_capability": None,
            "source": "torch",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _request_json(
    url: str,
    *,
    api_key: str,
    timeout: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ModelHealthError(f"model request failed: {type(exc).__name__}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ModelHealthError("model endpoint returned a non-object JSON response")
    return parsed


def check_model_health(
    config: MiniConfig,
    *,
    expected_model: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Validate model discovery and one short chat completion without retaining text."""
    environment_name = config.teacher.api_key_env
    api_key = os.environ.get(environment_name)
    if not api_key:
        raise ModelHealthError(f"required environment variable {environment_name} is not present")
    model = expected_model or config.teacher.model
    base_url = config.teacher.base_url.rstrip("/")
    models_response = _request_json(f"{base_url}/models", api_key=api_key, timeout=timeout)
    model_records = models_response.get("data")
    if not isinstance(model_records, list):
        raise ModelHealthError("/v1/models response does not contain a data list")
    identifiers = [record.get("id") for record in model_records if isinstance(record, dict)]
    identifiers = [identifier for identifier in identifiers if isinstance(identifier, str)]
    if model not in identifiers:
        raise ModelHealthError(
            f"configured model {model!r} is not served; returned identifiers: {identifiers}"
        )
    selected = next(
        record
        for record in model_records
        if isinstance(record, dict) and record.get("id") == model
    )
    reported_context = selected.get("max_model_len", selected.get("max_context_length"))
    if reported_context is not None:
        try:
            reported_context = int(reported_context)
        except (TypeError, ValueError) as exc:
            raise ModelHealthError("model context length is not an integer") from exc
        if reported_context < config.teacher.max_model_len:
            raise ModelHealthError(
                f"model reports context {reported_context}, below configured "
                f"{config.teacher.max_model_len}"
            )
    completion = _request_json(
        f"{base_url}/chat/completions",
        api_key=api_key,
        timeout=timeout,
        payload={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "temperature": 0,
            "max_tokens": 8,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )
    choices = completion.get("choices")
    valid_completion = bool(
        isinstance(choices, list)
        and choices
        and isinstance(choices[0], dict)
        and isinstance(choices[0].get("message"), dict)
        and isinstance(choices[0]["message"].get("content"), str)
        and choices[0]["message"]["content"].strip()
    )
    if not valid_completion:
        raise ModelHealthError("chat completion response does not contain a message")
    returned_model = completion.get("model")
    if returned_model is not None and returned_model != model:
        raise ModelHealthError(
            f"chat completion returned model {returned_model!r}, expected {model!r}"
        )
    return {
        "checked": True,
        "healthy": True,
        "base_url": base_url,
        "expected_model": model,
        "returned_model": returned_model or model,
        "configured_max_model_len": config.teacher.max_model_len,
        "reported_max_model_len": reported_context,
        "chat_completion_valid": True,
    }


def _configured_paths(config: MiniConfig) -> list[dict[str, Any]]:
    paths = [
        _path_report("repository", config.repo_root, output=False),
        _path_report("configuration", config.config_path, output=False),
        _path_report("MCP configuration", config.catalog.mcp_config, output=False),
        _path_report("metadata directory", config.catalog.metadata_dir, output=False),
    ]
    for server in config.catalog.servers:
        paths.append(
            _path_report(
                f"{server} tool", config.repo_root / "envs" / "tools" / f"{server}.py", output=False
            )
        )
    for label, path in (
        ("artifact root", config.artifact_root),
        ("graph output", config.graph.path),
        ("graph manifest", config.graph.manifest_path),
        ("embedding cache", config.graph.embedding_cache),
        ("classification cache", config.graph.user_provided_cache),
    ):
        paths.append(_path_report(label, path, output=True))
    return paths


def collect_report(
    config: MiniConfig,
    *,
    require_model: bool,
    environment_profile: Literal["runtime", "train"] = "runtime",
    expected_model: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Collect a secret-free compatibility report and calculate pass/fail status."""
    torch_report, torch = _torch_report()
    package_status = {
        "torch": torch_report,
        "vllm": _package_status("vllm", "vllm", import_module=True),
        "sentence_transformers": _package_status(
            "sentence-transformers", "sentence_transformers", import_module=False
        ),
        "llamafactory": _package_status(
            "llamafactory", "llamafactory", import_module=False
        ),
    }
    gpu = _gpu_report(torch)
    model_cache = Path(
        os.environ.get("HF_HOME")
        or os.environ.get("HUGGINGFACE_HUB_CACHE")
        or Path.home() / ".cache" / "huggingface"
    ).expanduser().resolve()
    paths = _configured_paths(config)
    disks = [
        _disk_report("repository", config.repo_root),
        _disk_report("model_cache", model_cache),
        _disk_report("artifacts", config.artifact_root),
    ]
    secret = {
        "name": config.teacher.api_key_env,
        "present": bool(os.environ.get(config.teacher.api_key_env)),
    }
    endpoint: dict[str, Any] = {"checked": False, "healthy": None}
    endpoint_error = None
    if require_model:
        try:
            endpoint = check_model_health(
                config, expected_model=expected_model, timeout=timeout
            )
        except ModelHealthError as exc:
            endpoint = {"checked": True, "healthy": False, "error": str(exc)}
            endpoint_error = str(exc)

    errors: list[str] = []
    warnings: list[str] = []
    if sys.version_info < (3, 12):
        errors.append("Python 3.12 or newer is required")
    if platform.system() != "Linux":
        errors.append("MoLab runtime must be Linux")
    cpu_count = os.cpu_count()
    if cpu_count is None or cpu_count < 4:
        errors.append("at least four CPUs are required")
    host_ram = _host_ram_bytes()
    if host_ram is None or host_ram < MINIMUM_HOST_RAM_BYTES:
        errors.append("at least 30 GiB of host RAM must be detectable")
    if not all(record["ok"] for record in paths):
        errors.append("one or more required paths are missing or not writable")
    for disk in disks:
        free = disk.get("free_bytes")
        if free is None or free < MINIMUM_FREE_DISK_BYTES:
            errors.append(f"{disk['label']} has less than 10 GiB free or could not be checked")
        elif free < LOW_FREE_DISK_BYTES:
            warnings.append(f"{disk['label']} has less than 20 GiB free")
    if not torch_report["importable"] or not torch_report["cuda_available"]:
        errors.append("PyTorch with an available CUDA device is required")
    if _version_tuple(torch_report.get("compiled_cuda_version")) < MINIMUM_CUDA_VERSION:
        errors.append("PyTorch must be compiled for CUDA 12.8 or newer")
    if environment_profile == "runtime":
        if not package_status["vllm"]["importable"]:
            errors.append("vLLM must import successfully in the runtime environment")
        if not package_status["sentence_transformers"]["importable"]:
            errors.append("sentence-transformers is required in the runtime environment")
        if not secret["present"]:
            errors.append(f"required secret variable {secret['name']} is not present")
    elif not package_status["llamafactory"]["importable"]:
        errors.append("LlamaFactory is required in the training environment")
    if gpu.get("total_vram_bytes") is None or gpu["total_vram_bytes"] < MINIMUM_GPU_VRAM_BYTES:
        errors.append("a GPU with at least 90 GiB VRAM is required")
    if _version_tuple(gpu.get("compute_capability")) < MINIMUM_COMPUTE_CAPABILITY:
        errors.append("a Blackwell-class GPU with compute capability 12.0 or newer is required")
    if endpoint_error:
        errors.append(f"model endpoint is unhealthy: {endpoint_error}")
    if require_model and endpoint.get("reported_max_model_len") is None:
        warnings.append("the model endpoint did not report its maximum context length")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment_profile": environment_profile,
        "compatible": not errors,
        "errors": errors,
        "warnings": warnings,
        "python": {
            "executable": sys.executable,
            "prefix": sys.prefix,
            "version": platform.python_version(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
        },
        "resources": {"cpu_count": cpu_count, "host_ram_bytes": host_ram},
        "gpu": gpu,
        "packages": package_status,
        "installed_packages": _installed_packages(),
        "paths": paths,
        "disks": disks,
        "model_cache": str(model_cache),
        "artifact_root": str(config.artifact_root),
        "required_secrets": [secret],
        "model_endpoint": endpoint,
    }


def _atomic_write_json(destination: Path, value: object) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _print_human(report: dict[str, Any]) -> None:
    state = "compatible" if report["compatible"] else "incompatible"
    print(f"MoLab {report['environment_profile']} doctor: {state}")
    print(f"Python: {report['python']['version']} ({report['python']['executable']})")
    print(
        f"Platform: {report['platform']['system']} {report['platform']['machine']}; "
        f"CPU: {report['resources']['cpu_count']}; RAM: {report['resources']['host_ram_bytes']} bytes"
    )
    gpu = report["gpu"]
    print(
        f"GPU: {gpu.get('name') or 'unavailable'}; driver: "
        f"{gpu.get('driver_version') or 'unavailable'}; VRAM: {gpu.get('total_vram_bytes')} bytes; "
        f"compute capability: {gpu.get('compute_capability') or 'unavailable'}"
    )
    torch = report["packages"]["torch"]
    print(
        f"PyTorch: {torch.get('version') or 'unavailable'}; compiled CUDA: "
        f"{torch.get('compiled_cuda_version') or 'unavailable'}; CUDA available: "
        f"{torch.get('cuda_available')}"
    )
    vllm = report["packages"]["vllm"]
    print(f"vLLM: {vllm.get('version') or 'unavailable'}; importable: {vllm['importable']}")
    for secret in report["required_secrets"]:
        print(f"Secret {secret['name']}: {'present' if secret['present'] else 'missing'}")
    endpoint = report["model_endpoint"]
    if endpoint["checked"]:
        print(
            f"Model endpoint: {'healthy' if endpoint['healthy'] else 'unhealthy'}; "
            f"model: {endpoint.get('returned_model') or 'unavailable'}"
        )
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MoLab Mini runtime compatibility")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--repo-root", help="Explicit EnvFactory repository root")
    model = parser.add_mutually_exclusive_group(required=True)
    model.add_argument("--without-model", action="store_true", help="Skip endpoint requests")
    model.add_argument("--require-model", action="store_true", help="Require model health")
    parser.add_argument(
        "--environment-profile", choices=("runtime", "train"), default="runtime"
    )
    parser.add_argument("--expected-model", help="Expected served model identifier")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    parser.add_argument("--output", type=Path, help="Atomically write the JSON report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        config = load_config(args.config, repo_root=args.repo_root)
        report = collect_report(
            config,
            require_model=args.require_model,
            environment_profile=args.environment_profile,
            expected_model=args.expected_model,
            timeout=args.timeout,
        )
        if args.output:
            destination = args.output.expanduser()
            if not destination.is_absolute():
                destination = config.repo_root / destination
            _atomic_write_json(destination.resolve(), report)
    except (DoctorError, MiniConfigError, OSError, ValueError) as exc:
        print(f"doctor failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["compatible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DoctorError",
    "ModelHealthError",
    "check_model_health",
    "collect_report",
    "main",
]
