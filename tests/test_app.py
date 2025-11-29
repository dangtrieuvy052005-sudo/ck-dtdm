"""Integration-style tests for the Flask backend."""

from importlib import reload
from pathlib import Path

import pytest


@pytest.fixture()
def app_module():
    """Import the Flask application module with a clean cache."""

    import Dangtrieuvyminiclouddemo.app.app as app_module

    # Ensure students.json exists before proceeding to avoid flakiness.
    data_path = Path(app_module.STUDENTS_PATH)
    if not data_path.exists():
        pytest.skip("students.json is missing so the API cannot serve data")

    # Reload to make sure cache-related globals start fresh for each test run.
    app_module = reload(app_module)
    app_module.app.config.update(TESTING=True)
    return app_module


@pytest.fixture()
def client(app_module):
    """Provide a Flask test client for exercising the endpoints."""

    with app_module.app.test_client() as client:
        yield client


def test_hello_endpoint(client):
    response = client.get("/hello")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"message": "Hello from App Server!"}


def test_student_endpoint_handles_trailing_slash(client):
    resp_no_slash = client.get("/student")
    resp_with_slash = client.get("/student/")

    for response in (resp_no_slash, resp_with_slash):
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert data, "students list should not be empty"
        for item in data:
            assert {"id", "name", "major", "gpa"} <= set(item)


def test_secure_endpoint_requires_token(client):
    response = client.get("/secure")
    assert response.status_code == 401
    payload = response.get_json()
    assert "Authorization" in payload["error"] or "Token" in payload["error"]


def test_metrics_endpoint_reports_basic_counters(client):
    # Trigger a few requests to populate counters.
    client.get("/hello")
    client.get("/student")

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.data.decode()
    assert "app_students_total" in body
    assert "app_http_requests_total" in body
