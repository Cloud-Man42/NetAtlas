from app.tls import ensure_local_tls_certificates


def test_local_tls_certificates_are_created_and_reused(tmp_path) -> None:
    cert_path, key_path = ensure_local_tls_certificates(tmp_path, hosts=["localhost", "127.0.0.1"])

    assert cert_path.exists()
    assert key_path.exists()
    assert b"BEGIN CERTIFICATE" in cert_path.read_bytes()
    assert b"BEGIN PRIVATE KEY" in key_path.read_bytes()

    second_cert_path, second_key_path = ensure_local_tls_certificates(tmp_path, hosts=["localhost", "127.0.0.1"])

    assert second_cert_path == cert_path
    assert second_key_path == key_path
