import os
os.environ['DATABASE_URL'] = 'sqlite:////tmp/test_api.db'
os.environ.setdefault('ALLOW_PUBLIC', 'true')
os.environ.setdefault('RUN_BOT', 'false')

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.schedule import Day
from app.services.schedule import ScheduleService


def setup_module(module):
    # Prepare fresh test DB and seed minimal data
    try:
        if os.path.exists('/tmp/test_api.db'):
            os.remove('/tmp/test_api.db')
    except Exception:
        pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ScheduleService.create_test_data(db)
    finally:
        db.close()


client = TestClient(app)


def test_root_serves_index():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<!DOCTYPE html>" in resp.text


def test_test_db_endpoint_lists_groups():
    resp = client.get("/test_db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["groups_count"] >= 1


def test_groups_endpoint_returns_list():
    resp = client.get("/groups/")
    assert resp.status_code == 200
    groups = resp.json()
    assert isinstance(groups, list) and len(groups) >= 1


def test_lessons_by_day_id():
    db = SessionLocal()
    try:
        day = db.query(Day).first()
        assert day is not None
        resp = client.get(f"/days/{day.id}/lessons")
    finally:
        db.close()
    assert resp.status_code == 200
    lessons = resp.json()
    assert isinstance(lessons, list)


def test_secure_endpoint_ok_when_public():
    resp = client.post("/secure-endpoint")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok" 