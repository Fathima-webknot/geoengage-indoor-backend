from pydantic import BaseModel


class MeResponse(BaseModel):
    id: int
    email: str
    name: str | None
    role: str
    firebase_uid: str


class RegisterDeviceRequest(BaseModel):
    fcm_token: str
