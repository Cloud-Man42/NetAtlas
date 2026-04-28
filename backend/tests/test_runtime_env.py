from app.runtime_env import build_runtime_env_contents, ensure_runtime_env_file


def test_build_runtime_env_contents_uses_install_safe_defaults() -> None:
    contents = build_runtime_env_contents()

    assert "GEOIP_LOOKUP_ENABLED=true\n" in contents
    assert "GEOIP_LOOKUP_URL=https://ipwho.is/{ip}\n" in contents
    assert "WAN_INTERFACE_KEYWORDS=wan,internet,pppoe\n" in contents
    assert "DATABASE_URL=" not in contents
    assert contents.endswith("\n")


def test_ensure_runtime_env_file_creates_missing_file(tmp_path) -> None:
    env_path = ensure_runtime_env_file(tmp_path)

    assert env_path == tmp_path / ".env"
    assert env_path.read_text(encoding="utf-8") == build_runtime_env_contents()


def test_ensure_runtime_env_file_keeps_existing_file(tmp_path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("GEOIP_LOOKUP_ENABLED=false\n", encoding="utf-8")

    result = ensure_runtime_env_file(tmp_path)

    assert result == env_path
    assert env_path.read_text(encoding="utf-8") == "GEOIP_LOOKUP_ENABLED=false\n"
