import pytest

from app.db.models import Floor, Zone


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


def test_analytics_admin(admin_client, floor_zone):
    r = admin_client.get(
        "/api/v1/analytics",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "zone_entries" in data
    assert "notifications_sent" in data
    assert "clicks" in data
    assert "ctr" in data
    assert "top_zones" in data
    assert isinstance(data["zone_entries"], list)
    assert isinstance(data["top_zones"], list)


def test_analytics_forbidden_as_user(client):
    r = client.get(
        "/api/v1/analytics",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 403
