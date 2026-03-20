"""Logging middleware for JSON structured logging."""

import time
import uuid
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for JSON structured logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request_id
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add X-Request-Id to request headers if not present
        if "x-request-id" not in request.headers:
            request.headers.__dict__["_list"].append(
                ("x-request-id", request_id)
            )
        
        # Start timer
        start_time = time.time()
        
        # Get user_id from headers (set by auth middleware)
        user_id = request.headers.get("X-User-Id")
        
        # Get request body for mutating operations
        body = None
        if request.method in ["POST", "PUT", "DELETE"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = json.loads(body_bytes.decode())
                    # Mask sensitive data
                    if "password" in body:
                        body["password"] = "***MASKED***"
                    if "refresh_token" in body:
                        body["refresh_token"] = "***MASKED***"
            except Exception:
                body = None
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add X-Request-Id to response
        response.headers["X-Request-Id"] = request_id
        
        # Create log entry
        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }
        
        # Add body for mutating operations
        if body:
            log_entry["request_body"] = body
        
        # Log as JSON
        logger.info(json.dumps(log_entry))
        
        return response
