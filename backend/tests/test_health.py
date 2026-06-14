"""Smoke tests for the health endpoints.

These run without a live database: the readiness probe degrades gracefully
when MongoDB is unavailable rather than failing the request.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"]
    assert body["version"]


def test_health() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready() -> None:
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert "dependencies" in resp.json()
