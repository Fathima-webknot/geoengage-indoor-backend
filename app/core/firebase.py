from firebase_admin import auth, credentials, initialize_app

from app.config import settings

_app_initialized = False


def ensure_firebase_app():
    global _app_initialized
    if _app_initialized:
        return
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        initialize_app(cred)
    else:
        initialize_app()
    _app_initialized = True


def verify_id_token(token: str) -> dict:
    ensure_firebase_app()
    return auth.verify_id_token(token)
