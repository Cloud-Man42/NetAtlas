from app.launcher import HTTPS_PORT, _browser_host_for_bind_host, _settings_with_launcher_defaults, _tls_hosts


def test_browser_host_uses_localhost_for_wildcard_bind() -> None:
    assert _browser_host_for_bind_host("0.0.0.0") == "localhost"


def test_browser_host_uses_specific_bind_host() -> None:
    assert _browser_host_for_bind_host("192.168.1.10") == "192.168.1.10"


def test_tls_hosts_include_specific_bind_host() -> None:
    assert _tls_hosts("192.168.1.10") == ["127.0.0.1", "localhost", "192.168.1.10"]


def test_tls_hosts_skip_wildcard_bind_host() -> None:
    assert _tls_hosts("0.0.0.0") == ["127.0.0.1", "localhost"]


def test_launcher_defaults_do_not_override_env_bind_host(monkeypatch) -> None:
    monkeypatch.setenv("APP_BIND_HOST", "0.0.0.0")
    monkeypatch.delenv("HTTPS_ENABLED", raising=False)
    monkeypatch.delenv("HTTPS_PORT", raising=False)

    settings = _settings_with_launcher_defaults()

    assert settings.app_bind_host == "0.0.0.0"
    assert settings.https_enabled is True
    assert settings.https_port == HTTPS_PORT
