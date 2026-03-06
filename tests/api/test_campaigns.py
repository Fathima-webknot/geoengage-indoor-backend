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
        json={
            "zone_id": str(zone.id),
            "message": "Welcome to Pantry!",
            "name": "Pantry Offer",
        },
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["zone_id"] == str(zone.id)
    assert data["message"] == "Welcome to Pantry!"
    assert data["name"] == "Pantry Offer"
    assert data["active"] is False
    assert data["trigger"] == "zone_entry"


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
        json={
            "zone_id": str(zone.id),
            "message": "Active campaign",
            "trigger": "zone_entry",
        },
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


def test_activate_exit_campaign_does_not_deactivate_entry(admin_client, floor_zone):
    _, zone = floor_zone

    # Create entry and exit campaigns
    cr_entry = admin_client.post(
        "/api/v1/campaigns",
        json={
            "zone_id": str(zone.id),
            "message": "Entry campaign",
            "trigger": "zone_entry",
        },
        headers={"Authorization": "Bearer admin-token"},
    )
    cr_exit = admin_client.post(
        "/api/v1/campaigns",
        json={
            "zone_id": str(zone.id),
            "message": "Exit campaign",
            "trigger": "zone_exit_no_txn",
        },
        headers={"Authorization": "Bearer admin-token"},
    )
    entry_id = cr_entry.json()["id"]
    exit_id = cr_exit.json()["id"]

    # Activate entry campaign
    r1 = admin_client.put(
        f"/api/v1/campaigns/{entry_id}",
        json={"active": True},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r1.status_code == 200
    assert r1.json()["active"] is True

    # Activate exit campaign (should not deactivate entry)
    r2 = admin_client.put(
        f"/api/v1/campaigns/{exit_id}",
        json={"active": True},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r2.status_code == 200
    assert r2.json()["active"] is True

    # List campaigns and verify both are active
    r_list = admin_client.get(
        f"/api/v1/campaigns?zone_id={zone.id}",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r_list.status_code == 200
    data = r_list.json()
    entry = next(c for c in data if c["id"] == entry_id)
    exit_c = next(c for c in data if c["id"] == exit_id)
    assert entry["active"] is True
    assert exit_c["active"] is True


def test_campaign_not_found(admin_client):
    r = admin_client.put(
        "/api/v1/campaigns/99999",
        json={"active": True},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 404
