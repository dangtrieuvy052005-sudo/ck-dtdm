from flask import Flask, jsonify, request
import time
import requests
from jose import jwt
import os

# ---- OIDC config lấy từ biến môi trường (đặt trong docker-compose) ----
ISSUER   = os.getenv("OIDC_ISSUER",   "http://keycloak:8080/realms/master")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "myapp")  # client_id
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# ---- JWKS cache đơn giản ----
_JWKS = None
_JWKS_TS = 0
def get_jwks():
    global _JWKS, _JWKS_TS
    if (not _JWKS) or (time.time() - _JWKS_TS > 300):
        resp = requests.get(JWKS_URL, timeout=5)
        resp.raise_for_status()
        _JWKS = resp.json()
        _JWKS_TS = time.time()
    return _JWKS

def verify_token(auth_header: str):
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise ValueError("Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1].strip()

    # Lấy header để tìm kid
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")

    jwks = get_jwks()
    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise ValueError("JWKS key not found for kid")

    # Giải mã + kiểm tra iss, aud
    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"verify_at_hash": False},  # đơn giản hóa cho demo
    )
    return payload

app = Flask(__name__)

@app.get("/hello")
def hello():
    return jsonify(message="Hello from App Server! (public)")

@app.get("/secure")
def secure():
    try:
        payload = verify_token(request.headers.get("Authorization"))
        return jsonify(
            message="Secure resource OK",
            sub=payload.get("sub"),
            preferred_username=payload.get("preferred_username"),
            realm_access=payload.get("realm_access", {}),
            aud=payload.get("aud"),
            iss=payload.get("iss"),
        )
    except Exception as e:
        return jsonify(error=str(e)), 401

if __name__ == "__main__":
    # Quan trọng: lắng nghe trên 0.0.0.0:8081 để Docker publish ra được
    app.run(host="0.0.0.0", port=8081)
