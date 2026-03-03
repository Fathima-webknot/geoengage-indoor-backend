from firebase_admin import messaging

from app.core.firebase import ensure_firebase_app


def send_fcm_to_token(token: str, title: str, body: str, data: dict | None = None) -> str | None:
    ensure_firebase_app()
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        token=token,
    )
    result = messaging.send(message)
    return result
