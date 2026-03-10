"""Proxy Router - handles request forwarding to services"""

import httpx
from fastapi import Request, Response
from src.config import PATH_ROUTES, SERVICE_URLS


async def proxy_request(request: Request) -> Response:
    """Proxy request to appropriate service"""

    # Get request path
    path = request.url.path

    # Find matching route
    matched_route = None
    for prefix, (service_name, service_path) in PATH_ROUTES.items():
        if path.startswith(prefix):
            matched_route = (service_name, service_path)
            break

    if not matched_route:
        return Response(
            content='{"error": "Route not found"}',
            status_code=404,
            media_type="application/json",
        )

    service_name, service_path = matched_route

    # Build target URL
    service_url = SERVICE_URLS[service_name]
    target_path = path.replace(
        service_path.split("/")[1], service_path.split("/")[1], 1
    )
    target_url = f"{service_url}{path}"

    # Prepare request data
    body = await request.body()
    headers = dict(request.headers)

    # Add user role from request state if available
    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role

    # Remove hop-by-hop headers
    hop_by_hop = [
        "host",
        "connection",
        "keep-alive",
        "transfer-encoding",
        "te",
        "trailer",
        "upgrade",
    ]
    for header in hop_by_hop:
        headers.pop(header, None)

    # Proxy request
    async with httpx.AsyncClient() as client:
        try:
            proxy_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
                params=request.query_params,
                timeout=30.0,
            )

            # Return response
            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=dict(proxy_response.headers),
                media_type=proxy_response.headers.get("content-type"),
            )

        except httpx.TimeoutException:
            return Response(
                content='{"error": "Service timeout"}',
                status_code=504,
                media_type="application/json",
            )
        except httpx.ConnectError:
            return Response(
                content='{"error": "Service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
        except Exception as e:
            return Response(
                content=f'{{"error": "Proxy error: {str(e)}"}}',
                status_code=500,
                media_type="application/json",
            )
