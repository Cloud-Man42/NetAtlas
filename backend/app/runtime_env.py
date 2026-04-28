from pathlib import Path

RUNTIME_ENV_LINES = (
    "API_PREFIX=/api",
    "HTTPS_ENABLED=true",
    "HTTPS_PORT=8443",
    "HTTPS_CERT_FILE=",
    "HTTPS_KEY_FILE=",
    "SYSLOG_ENABLED=true",
    "SYSLOG_BIND_HOST=0.0.0.0",
    "SYSLOG_BIND_PORT=5140",
    "SYSLOG_MAX_MESSAGE_SIZE=65535",
    "WAN_INTERFACE_KEYWORDS=wan,internet,pppoe",
    "GEOIP_LOOKUP_ENABLED=true",
    "GEOIP_LOOKUP_URL=https://ipwho.is/{ip}",
    "GEOIP_LOOKUP_TIMEOUT_SECONDS=3.0",
)


def build_runtime_env_contents() -> str:
    return "\n".join(RUNTIME_ENV_LINES) + "\n"


def ensure_runtime_env_file(runtime_root: Path) -> Path:
    env_path = runtime_root / ".env"
    if env_path.exists():
        return env_path

    env_path.write_text(build_runtime_env_contents(), encoding="utf-8")
    return env_path
