"""Flask backend service for the mini cloud demo.

The application exposes:
- ``/hello``   : public health/info endpoint.
- ``/student`` : returns student information from a JSON document.
- ``/secure``  : protected endpoint that validates a Keycloak JWT.
- ``/metrics`` : basic Prometheus metrics for monitoring.

The implementation emphasises clean code so the accompanying report is
straightforward to write và bảo vệ.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from flask import Flask, Response, jsonify, request
import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidTokenError,
    PyJWKClientError,
)


@dataclass(frozen=True)
class OIDCConfig:
    """Runtime configuration for decoding Keycloak tokens."""

    issuer: str
    audience: str
    algorithms: tuple[str, ...] = ("RS256",)

    @property
    def jwks_url(self) -> str:
        issuer = self.issuer.rstrip("/")
        return f"{issuer}/protocol/openid-connect/certs"


def _build_oidc_config() -> OIDCConfig:
    """Create an :class:`OIDCConfig` from environment variables."""

    issuer = os.getenv("OIDC_ISSUER")
    if not issuer:
        server = os.getenv("KEYCLOAK_SERVER", "http://auth:8080")
        realm = os.getenv("KEYCLOAK_REALM", "master")
        issuer = f"{server.rstrip('/')}/realms/{realm}"

    audience = os.getenv("OIDC_AUDIENCE") or os.getenv("KEYCLOAK_AUDIENCE", "account")
    return OIDCConfig(issuer=issuer, audience=audience)


OIDC_CONFIG = _build_oidc_config()
JWK_CLIENT = PyJWKClient(OIDC_CONFIG.jwks_url, cache_keys=True)
STUDENTS_PATH = Path(__file__).with_name("students.json")
STUDENTS_CACHE: tuple[float, list[Dict[str, Any]]] | None = None
STUDENTS_CACHE_LOCK = Lock()
REQUEST_COUNTER: Counter[str] = Counter()
TOTAL_REQUESTS: int = 0
app = Flask(__name__)


@dataclass(frozen=True)
class Student:
    """Biểu diễn một sinh viên được khai báo trong ``students.json``."""

    id: str
    name: str
    major: str
    gpa: float

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "Student":
        """Chuyển đổi ``payload`` JSON thành :class:`Student` và kiểm tra dữ liệu."""

        if not isinstance(payload, dict):
            raise ValueError("Dữ liệu sinh viên phải là object JSON")

        try:
            raw_id = str(payload["id"]).strip()
            name = str(payload["name"]).strip()
            major = str(payload["major"]).strip()
            gpa_value = payload["gpa"]
        except KeyError as exc:
            raise ValueError(f"Thiếu trường bắt buộc: {exc.args[0]}") from exc

        if not raw_id:
            raise ValueError("Mỗi sinh viên phải có mã 'id' khác rỗng")
        if not name:
            raise ValueError(f"Sinh viên {raw_id} thiếu họ tên hợp lệ")
        if not major:
            raise ValueError(f"Sinh viên {raw_id} thiếu chuyên ngành hợp lệ")

        try:
            gpa = float(gpa_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"GPA của sinh viên {raw_id} không hợp lệ") from exc

        if not 0 <= gpa <= 4:
            raise ValueError(f"GPA của sinh viên {raw_id} phải nằm trong khoảng 0-4")

        return cls(id=raw_id, name=name, major=major, gpa=round(gpa, 2))

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _load_students() -> list[Dict[str, Any]]:
    """Read the student list from disk with basic caching."""

    global STUDENTS_CACHE

    try:
        mtime = STUDENTS_PATH.stat().st_mtime
    except FileNotFoundError:
        raise

    with STUDENTS_CACHE_LOCK:
        if STUDENTS_CACHE and STUDENTS_CACHE[0] == mtime:
            return STUDENTS_CACHE[1]

        with STUDENTS_PATH.open("r", encoding="utf-8") as handle:
            raw_data = json.load(handle)

        if not isinstance(raw_data, list):
            raise ValueError("students.json không chứa danh sách sinh viên hợp lệ")

        students: list[Student] = []
        for index, item in enumerate(raw_data, start=1):
            try:
                students.append(Student.from_payload(item))
            except ValueError as exc:
                raise ValueError(f"Lỗi ở dòng {index}: {exc}") from exc

        serialised = [student.as_dict() for student in students]
        STUDENTS_CACHE = (mtime, serialised)
        return serialised


def _extract_bearer_token(header_value: str | None) -> str:
    if not header_value:
        raise ValueError("Thiếu Authorization Header")

    token_type, _, token = header_value.partition(" ")
    if token_type.lower() != "bearer" or not token:
        raise ValueError("Token phải có dạng 'Bearer <token>'")
    return token


def _decode_token(raw_token: str) -> Dict[str, Any]:
    """Validate a JWT coming from Keycloak."""

    signing_key = JWK_CLIENT.get_signing_key_from_jwt(raw_token).key
    return jwt.decode(
        raw_token,
        signing_key,
        algorithms=OIDC_CONFIG.algorithms,
        audience=OIDC_CONFIG.audience,
        issuer=OIDC_CONFIG.issuer,
    )


@app.before_request
def _track_requests() -> None:
    global TOTAL_REQUESTS
    endpoint = request.endpoint or "unknown"
    TOTAL_REQUESTS += 1
    REQUEST_COUNTER[endpoint] += 1


@app.get("/hello")
def hello() -> Any:
    """Public endpoint used for quick smoke tests."""

    return jsonify(message="Hello from App Server!")


@app.get("/student")
def student() -> Any:
    """Return the static student catalogue used by the report demo."""

    try:
        return jsonify(_load_students())
    except FileNotFoundError:
        return jsonify(error="students.json not found"), 404
    except json.JSONDecodeError as exc:
        return jsonify(error=f"students.json bị lỗi định dạng: {exc}"), 500
    except ValueError as exc:
        return jsonify(error=str(exc)), 500


@app.get("/secure")
def secure_api() -> Any:
    """JWT-protected endpoint that returns the decoded token payload."""

    try:
        raw_token = _extract_bearer_token(request.headers.get("Authorization"))
        payload = _decode_token(raw_token)
    except ValueError as exc:
        return jsonify(error=str(exc)), 401
    except PyJWKClientError as exc:
        return jsonify(error=f"Không thể lấy public key từ Keycloak: {exc}"), 502
    except ExpiredSignatureError:
        return jsonify(error="Token đã hết hạn"), 401
    except InvalidAudienceError as exc:
        return jsonify(error=f"Token sai audience: {exc}"), 401
    except InvalidTokenError as exc:
        return jsonify(error=f"Token không hợp lệ: {exc}"), 401

    username = payload.get("preferred_username", "Không rõ")
    return jsonify(
        message=f"Xin chào {username}! Đây là API BẢO MẬT.",
        token_payload=payload,
    )


@app.get("/metrics")
def metrics() -> Response:
    """Expose lightweight Prometheus metrics."""

    try:
        student_count = len(_load_students())
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        student_count = 0

    lines = [
        "# HELP app_students_total Số lượng sinh viên trong students.json",
        "# TYPE app_students_total gauge",
        f"app_students_total {student_count}",
        "# HELP app_http_requests_total Tổng số request HTTP đến Flask",
        "# TYPE app_http_requests_total counter",
        f"app_http_requests_total {TOTAL_REQUESTS}",
    ]
    for endpoint, value in sorted(REQUEST_COUNTER.items()):
        lines.append(f'app_http_requests_total{{endpoint="{endpoint}"}} {value}')

    body = "\n".join(lines) + "\n"
    return Response(body, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)
