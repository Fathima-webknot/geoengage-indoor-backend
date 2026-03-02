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


def test_create_campaign(admin_client, floor_zone):
    _, zone = floor_zone
    r = admin_client.post(
        "/api/v1/campaigns",
        json={"zone_id": str(zone.id), "message": "Welcome to Pantry!"},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["zone_id"] == str(zone.id)
    assert data["message"] == "Welcome to Pantry!"
    assert data["active"] is False


def test_list_campaigns(admin_client, floor_zone):
    _, zone = floor_zone
    admin_client.post(
        "/api/v1/campaigns",
        json={"zone_id": str(zone.id), "message": "Msg 1"},
        headers={"Authorization": "Bearer admin-token"},
    )
    r = admin_client.get(
        "/api/v1/campaigns",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_update_campaign_activate(admin_client, floor_zone):
    _, zone = floor_zone
    cr = admin_client.post(
        "/api/v1/campaigns",
        json={"zone_id": str(zone.id), "message": "Active campaign"},
        headers={"Authorization": "Bearer admin-token"},
    )
    cid = cr.json()["id"]
    r = admin_client.put(
        f"/api/v1/campaigns/{cid}",
        json={"active": True},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 200
    assert r.json()["active"] is True


def test_campaign_not_found(admin_client):
    r = admin_client.put(
        "/api/v1/campaigns/99999",
        json={"active": True},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 404
