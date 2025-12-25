import sys
from pathlib import Path
import copy
import pytest
from fastapi.testclient import TestClient

# Make sure the src/ directory is importable when running tests from repo root
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from app import app, activities as activities_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    # Preserve original activities and restore after each test
    original = copy.deepcopy(activities_store)
    yield
    activities_store.clear()
    activities_store.update(original)


def test_get_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    email = "test.signup@mergington.edu"
    r = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    r2 = client.get("/activities")
    assert email in r2.json()["Chess Club"]["participants"]


def test_signup_increases_count():
    r_before = client.get("/activities")
    before = len(r_before.json()["Chess Club"]["participants"])
    email = "count.test@mergington.edu"
    client.post(f"/activities/Chess%20Club/signup?email={email}")
    r_after = client.get("/activities")
    after = len(r_after.json()["Chess Club"]["participants"])
    assert after == before + 1


def test_duplicate_signups_are_allowed():
    email = "dup@test.com"
    client.post(f"/activities/Chess%20Club/signup?email={email}")
    client.post(f"/activities/Chess%20Club/signup?email={email}")
    r = client.get("/activities")
    assert r.json()["Chess Club"]["participants"].count(email) == 2


def test_unregister_existing_participant():
    email = "michael@mergington.edu"  # exists in initial data
    r = client.delete(f"/activities/Chess%20Club/participants?email={email}")
    assert r.status_code == 200
    assert "Unregistered" in r.json().get("message", "")

    r2 = client.get("/activities")
    assert email not in r2.json()["Chess Club"]["participants"]


def test_unregister_nonexistent_returns_404():
    email = "no.one@mergington.edu"
    r = client.delete(f"/activities/Chess%20Club/participants?email={email}")
    assert r.status_code == 404
