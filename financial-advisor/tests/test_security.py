from app.core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert not verify_password("wrong-password", hashed)

    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"


class TestJWT:
    def test_create_and_decode_roundtrip(self) -> None:
        token = create_access_token("user-123")
        user_id = decode_access_token(token)
        assert user_id == "user-123"

    def test_invalid_token_raises(self) -> None:
        import pytest

        with pytest.raises(TokenError):
            decode_access_token("not.a.valid.token")

    def test_tampered_token_raises(self) -> None:
        import pytest

        token = create_access_token("user-123")
        tampered = token[:-5] + "xxxxx"
        with pytest.raises(TokenError):
            decode_access_token(tampered)