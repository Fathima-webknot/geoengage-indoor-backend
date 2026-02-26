from unittest.mock import patch

import pytest

from app.db.models import Floor, Zone


@pytest.fixture
def floor_zone(db):
    floor = Floor(name="Ground", floor_number=0)
    db.add(floor)
    db.commit()
    db.refresh(floor)
    zone = Zone(
        floor_id=floor.id,
        name="Pantry",
        polygon_coordinates=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return floor, zone


def test_post_event_success(client, floor_zone):
    _, zone = floor_zone
    with patch("app.services.event.send_fcm_to_token", return_value="msg-123"):
        r = client.post(
            "/api/v1/event",
            json={"zone_id": zone.id},
            headers={"Authorization": "Bearer test-token"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["notification_sent"] is False  # no active campaign
    assert "message" in data


def test_post_event_by_zone_name_and_floor_id(client, floor_zone):
    floor, zone = floor_zone
    with patch("app.services.event.send_fcm_to_token", return_value="msg-123"):
        r = client.post(
            "/api/v1/event",
            json={"zone_name": "Pantry", "floor_id": floor.id},
            headers={"Authorization": "Bearer test-token"},
        )
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_post_event_zone_not_found(client):
    r = client.post(
        "/api/v1/event",
        json={"zone_id": 99999},
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 404
    assert "Zone not found" in r.json()["detail"]


def test_post_event_unauthorized(client, floor_zone):
    _, zone = floor_zone
    r = client.post("/api/v1/event", json={"zone_id": zone.id})
    assert r.status_code == 403  # no Authorization header
