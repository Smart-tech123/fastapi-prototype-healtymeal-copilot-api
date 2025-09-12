import base64
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.utils.uuid import UuidUtil


class KeyUtil:
    @classmethod
    def b64url_uint(cls, n: int) -> str:
        """Base64url encode an int (no padding)."""
        b = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    @classmethod
    def new_rsa_keypair(
        cls,
    ) -> tuple[str, dict[str, Any], str]:
        """Return (kid, public_jwk, private_pem)."""
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        pub = key.public_key().public_numbers()
        kid = str(UuidUtil.make_uuid())
        jwk = {
            "kty": "RSA",
            "kid": kid,
            "use": "sig",
            "alg": "RS256",
            "n": cls.b64url_uint(pub.n),
            "e": cls.b64url_uint(pub.e),
        }
        return kid, jwk, priv_pem

    @classmethod
    def pem_to_pubkey(cls, priv_pem: str):  # type: ignore  # noqa: ANN206, PGH003
        return serialization.load_pem_private_key(priv_pem.encode(), password=None).public_key()
