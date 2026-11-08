import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app  # noqa: E402


def test_index():
    res = app.test_client().get("/")
    assert res.status_code == 200 and res.get_json()["service"] == "CargoPulse API"


def test_health_does_not_need_database():
    res = app.test_client().get("/health")
    assert res.status_code == 200 and res.get_json() == {"status": "ok"}


def test_create_shipment_validates_input():
    res = app.test_client().post("/shipments", json={"origin": "Sharjah"})
    assert res.status_code == 400
