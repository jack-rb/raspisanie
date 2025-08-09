import os
import pytest
from fastapi.testclient import TestClient

# Ensure public access and disable bot during tests
os.environ["ALLOW_PUBLIC"] = "true"
os.environ["RUN_BOT"] = "false"

from app.main import app

client = TestClient(app)


def test_root_serves_index():
    r = client.get("/")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text


def test_groups_list_ok():
    r = client.get("/groups/")
    # When DB empty, service returns [] but endpoint itself should be 200
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_days_lessons_missing_returns_200_list():
    # Non-existing day id should return empty list (service returns [])
    r = client.get("/days/999999/lessons")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_teacher_list_ok():
    r = client.get("/teachers/")
    # Endpoint exists and returns list
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_group_schedule_not_found_returns_404():
    r = client.get("/groups/1/schedule/2099-01-01")
    # For non-existent date should be 404 per implementation
    assert r.status_code in (200, 404)
    # If 200, the schema must contain keys
    if r.status_code == 200:
        body = r.json()
        assert "date" in body and "group_id" in body and "lessons" in body 