from shared.fitlife_common import sign_token, verify_token


def test_token_roundtrip() -> None:
    token = sign_token({"sub": "USR-DEMO", "role": "user"}, "jwt-secret", exp_minutes=5)
    payload = verify_token(token, "jwt-secret")
    assert payload is not None
    assert payload["sub"] == "USR-DEMO"
