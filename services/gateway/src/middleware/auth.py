"""Auth Middleware"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from src.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens for protected endpoints"""

    async def dispatch(self, request: Request, call_next):
        # Get request path
        path = request.url.path

        # Skip auth for public endpoints
        if self._is_public_endpoint(path):
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        # Extract token
        token = auth_header.split(" ")[1]

        try:
            # Decode JWT
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # Extract user ID and role
            user_id = payload.get("sub")
            user_role = payload.get("role")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            # Attach user ID and role to request state
            request.state.user_id = user_id
            request.state.user_role = user_role

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if path is a public endpoint"""
        # Exact match
        if path in settings.PUBLIC_ENDPOINTS:
            return True

        # Prefix match for /docs and /openapi.json
        for public_path in settings.PUBLIC_ENDPOINTS:
            if public_path.endswith("*"):
                prefix = public_path[:-1]
                if path.startswith(prefix):
                    return True

        return False
