import pytest


def test_get_notifications_empty(client):
    r = client.get(
        "/api/v1/notifications",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_get_notifications_pagination(client):
    r = client.get(
        "/api/v1/notifications?limit=10&offset=0",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_notification_click_not_found(client):
    r = client.post(
        "/api/v1/notification-click",
        json={"campaign_id": 99999},
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    assert r.json()["success"] is False
