from unittest.mock import patch

import pytest

from app.db.models import Floor, Zone, Campaign


@pytest.fixture
def floor_zone(db):
    floor = Floor(floor_id=0, floor_name="Ground")
    db.add(floor)
    db.commit()
    db.refresh(floor)
    zone = Zone(floor_id=0, name="Pantry")
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return floor, zone


def test_post_event_success(client, floor_zone):
    _, zone = floor_zone
    with patch("app.services.event.send_fcm_to_token", return_value="msg-123"):
        r = client.post(
            "/api/v1/event",
            json={"zone_id": str(zone.id), "zone_name": "Pantry", "floor_id": 0},
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
            json={"zone_name": "Pantry", "floor_id": floor.floor_id},
            headers={"Authorization": "Bearer test-token"},
        )
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_post_event_zone_not_found(client):
    r = client.post(
        "/api/v1/event",
        json={"zone_id": "00000000-0000-0000-0000-000000000000", "zone_name": "Unknown", "floor_id": 99},
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 404
    assert "Zone not found" in r.json()["detail"]


def test_post_event_unauthorized(client, floor_zone):
    _, zone = floor_zone
    r = client.post(
        "/api/v1/event",
        json={"zone_id": str(zone.id), "zone_name": "Pantry", "floor_id": 0},
    )
    assert r.status_code == 403  # no Authorization header


def test_zone_exit_without_transaction_triggers_exit_campaign(client, floor_zone, db):
    _, zone = floor_zone

    # Create active entry and exit campaigns
    entry_campaign = Campaign(
        zone_id=zone.id,
        message="Entry",
        trigger="zone_entry",
        active=True,
    )
    exit_campaign = Campaign(
        zone_id=zone.id,
        message="Exit no txn",
        trigger="zone_exit_no_txn",
        active=True,
    )
    db.add(entry_campaign)
    db.add(exit_campaign)
    db.commit()

    with patch("app.services.event.send_fcm_to_token", return_value="msg-123"):
        # Entry
        r_entry = client.post(
            "/api/v1/event",
            json={
                "event_type": "zone_entry",
                "zone_id": str(zone.id),
                "zone_name": "Pantry",
                "floor_id": 0,
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert r_entry.status_code == 200

        # Exit without transaction
        r_exit = client.post(
            "/api/v1/event",
            json={
                "event_type": "zone_exit",
                "zone_id": str(zone.id),
                "zone_name": "Pantry",
                "floor_id": 0,
            },
            headers={"Authorization": "Bearer test-token"},
        )
    assert r_exit.status_code == 200
    data = r_exit.json()
    assert data["success"] is True
    assert data["notification_sent"] is True
    assert "campaign_message" in data


def test_zone_exit_after_transaction_does_not_trigger_exit_campaign(client, floor_zone, db):
    _, zone = floor_zone

    exit_campaign = Campaign(
        zone_id=zone.id,
        message="Exit no txn",
        trigger="zone_exit_no_txn",
        active=True,
    )
    db.add(exit_campaign)
    db.commit()

    with patch("app.services.event.send_fcm_to_token", return_value="msg-123"):
        # Entry
        r_entry = client.post(
            "/api/v1/event",
            json={
                "event_type": "zone_entry",
                "zone_id": str(zone.id),
                "zone_name": "Pantry",
                "floor_id": 0,
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert r_entry.status_code == 200

        # Record transaction
        r_txn = client.post(
            "/api/v1/transactions",
            json={
                "zone_id": str(zone.id),
                "zone_name": "Pantry",
                "floor_id": 0,
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert r_txn.status_code == 200

        # Exit
        r_exit = client.post(
            "/api/v1/event",
            json={
                "event_type": "zone_exit",
                "zone_id": str(zone.id),
                "zone_name": "Pantry",
                "floor_id": 0,
            },
            headers={"Authorization": "Bearer test-token"},
        )
    assert r_exit.status_code == 200
    data = r_exit.json()
    assert data["success"] is True
    assert data["notification_sent"] is False
