from app.core.config import Settings


def test_app_bind_host_defaults_to_localhost_only() -> None:
    settings = Settings()

    assert settings.app_bind_host == "127.0.0.1"


def test_app_bind_host_can_be_configured_for_network_access() -> None:
    settings = Settings(APP_BIND_HOST="0.0.0.0")

    assert settings.app_bind_host == "0.0.0.0"
