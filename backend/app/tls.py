from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Iterable

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def ensure_local_tls_certificates(data_dir: Path, hosts: Iterable[str]) -> tuple[Path, Path]:
    tls_dir = data_dir / "tls"
    tls_dir.mkdir(parents=True, exist_ok=True)

    cert_path = tls_dir / "netatlas-local.crt"
    key_path = tls_dir / "netatlas-local.key"

    if cert_path.exists() and key_path.exists():
        return cert_path, key_path

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NetAtlas"),
            x509.NameAttribute(NameOID.COMMON_NAME, "NetAtlas Local HTTPS"),
        ]
    )

    subject_alternative_names: list[x509.GeneralName] = []
    for host in hosts:
        try:
            subject_alternative_names.append(x509.IPAddress(ip_address(host)))
        except ValueError:
            subject_alternative_names.append(x509.DNSName(host))

    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(subject_alternative_names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )

    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    return cert_path, key_path
