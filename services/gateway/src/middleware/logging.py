"""Logging Middleware"""

import json
import time
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests in JSON format"""

    async def dispatch(self, request: Request, call_next):
        # Get request ID from state
        request_id = getattr(request.state, "request_id", "unknown")
        user_id = getattr(request.state, "user_id", None)

        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Create log entry
        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Print JSON log
        print(json.dumps(log_entry))

        return response
