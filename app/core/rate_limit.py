from slowapi import Limiter
from slowapi.util import get_remote_address


def get_identifier(request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_identifier, default_limits=["100/minute"])
