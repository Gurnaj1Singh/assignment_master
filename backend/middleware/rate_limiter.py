"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_user_id_or_ip(request: Request) -> str:
    """
    Key function for per-user rate limits.
    Extracts user_id from the JWT-authenticated request state if available,
    otherwise falls back to IP address.
    """
    # After get_current_user runs, the user object is available on the request
    # but slowapi key functions run before the endpoint. We parse the
    # Authorization header directly to extract the user_id claim.
    from jose import JWTError, jwt
    from ..config import settings

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("user_id")
            if user_id:
                return user_id
        except JWTError:
            pass

    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)
