import pytest
from passlib.context import CryptContext

from app.services.auth.auth_service import AuthService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def test_hash_password_returns_different_hashes_for_same_input() -> None:
    password = "mysecretpassword"  # noqa: S105

    hashed1 = AuthService.hash_password(password)
    hashed2 = AuthService.hash_password(password)

    # Hashed passwords should not be equal due to salting
    assert hashed1 != hashed2
    assert hashed1.startswith("$2b$")  # bcrypt hash starts like this


def test_verify_password_with_correct_password() -> None:
    password = "testpass123"  # noqa: S105
    hashed = AuthService.hash_password(password)

    assert AuthService.verify_password(password, hashed) is True


def test_verify_password_with_incorrect_password() -> None:
    password = "correctpass"  # noqa: S105
    hashed = AuthService.hash_password(password)

    assert AuthService.verify_password("wrongpass", hashed) is False


@pytest.mark.parametrize("password", ["123456", "P@ssw0rd!", "æøåÆØÅ"])
def test_hash_and_verify_with_various_passwords(password: str) -> None:
    hashed = AuthService.hash_password(password)
    assert AuthService.verify_password(password, hashed) is True
