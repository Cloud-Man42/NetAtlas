import multiprocessing
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

import uvicorn

from app.core.config import Settings
from app.runtime_env import ensure_runtime_env_file
from app.tls import ensure_local_tls_certificates

DEFAULT_APP_BIND_HOST = "127.0.0.1"
HTTP_PORT = 8000
HTTPS_PORT = 8443


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _frontend_dir(root: Path) -> Path:
    if getattr(sys, "frozen", False):
        candidate_dirs = [
            root / "frontend",
            root / "_internal" / "frontend",
        ]
        for candidate in candidate_dirs:
            if candidate.exists():
                return candidate
        return candidate_dirs[0]
    return root.parent / "frontend" / "dist"


def _data_dir(root: Path) -> Path:
    return root / "Data" if getattr(sys, "frozen", False) else root / "storage"


def _wait_for_server(host: str, port: int, attempts: int = 40, delay_seconds: float = 0.25) -> None:
    for _ in range(attempts):
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(delay_seconds)


def _browser_host_for_bind_host(bind_host: str) -> str:
    return "localhost" if bind_host in {"0.0.0.0", "::"} else bind_host


def _tls_hosts(bind_host: str) -> list[str]:
    hosts = [DEFAULT_APP_BIND_HOST, "localhost"]
    if bind_host not in {"0.0.0.0", "::"} and bind_host not in hosts:
        hosts.append(bind_host)
    return hosts


def _settings_with_launcher_defaults() -> Settings:
    settings = Settings()
    if "HTTPS_ENABLED" not in os.environ:
        settings.https_enabled = True
    if "HTTPS_PORT" not in os.environ:
        settings.https_port = HTTPS_PORT
    return settings


def _open_browser_when_ready(url: str, host: str, port: int) -> None:
    def _open() -> None:
        _wait_for_server(host, port)
        webbrowser.open(url)

    threading.Thread(target=_open, name="netatlas-browser-launcher", daemon=True).start()


def _resolve_tls_files(settings: Settings, data_dir: Path) -> tuple[Path, Path]:
    if settings.https_cert_file and settings.https_key_file:
        cert_path = Path(settings.https_cert_file).expanduser().resolve()
        key_path = Path(settings.https_key_file).expanduser().resolve()
        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError("Configured HTTPS certificate or key file was not found.")
        return cert_path, key_path

    return ensure_local_tls_certificates(data_dir, hosts=_tls_hosts(settings.app_bind_host))


def _uvicorn_log_config(log_path: Path) -> dict[str, object]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": str(log_path),
                "formatter": "default",
                "encoding": "utf-8",
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["file"], "level": "INFO", "propagate": False},
        },
    }


def main() -> None:
    multiprocessing.freeze_support()

    runtime_root = _runtime_root()
    frontend_dir = _frontend_dir(runtime_root)
    data_dir = _data_dir(runtime_root)
    data_dir.mkdir(parents=True, exist_ok=True)
    ensure_runtime_env_file(runtime_root)
    log_path = data_dir / "netatlas.log"

    os.environ.setdefault("NETATLAS_STATIC_DIR", str(frontend_dir))
    os.environ.setdefault("NETATLAS_DATA_DIR", str(data_dir))

    settings = _settings_with_launcher_defaults()
    app_scheme = "https" if settings.https_enabled else "http"
    app_port = settings.https_port if settings.https_enabled else HTTP_PORT
    browser_host = _browser_host_for_bind_host(settings.app_bind_host)
    os.environ.setdefault(
        "CORS_ORIGINS",
        f"{app_scheme}://{DEFAULT_APP_BIND_HOST}:{app_port},{app_scheme}://localhost:{app_port}",
    )

    ssl_options: dict[str, str] = {}
    if settings.https_enabled:
        cert_path, key_path = _resolve_tls_files(settings, data_dir)
        ssl_options = {
            "ssl_certfile": str(cert_path),
            "ssl_keyfile": str(key_path),
        }

    _open_browser_when_ready(f"{app_scheme}://{browser_host}:{app_port}", browser_host, app_port)
    uvicorn.run(
        "app.main:app",
        host=settings.app_bind_host,
        port=app_port,
        reload=False,
        workers=1,
        log_config=_uvicorn_log_config(log_path),
        **ssl_options,
    )


def _write_failure_log(error: BaseException) -> None:
    log_root = _runtime_root()
    log_path = log_root / "netatlas-launcher-error.log"
    log_path.write_text("".join(traceback.format_exception(error)), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        _write_failure_log(error)
        raise
