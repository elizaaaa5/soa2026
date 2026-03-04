"""Request ID Middleware"""

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and attach X-Request-ID header"""

    async def dispatch(self, request: Request, call_next):
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Attach to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
