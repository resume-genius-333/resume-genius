import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute


logger = logging.getLogger(__name__)


class LoggingRoute(APIRoute):
    """Custom APIRoute that logs validation errors with details"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            body = await request.body()

            # Store the body for potential logging
            request.state.body = body

            # Create a new request with the body we just read
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

            try:
                response = await original_route_handler(request)
            except Exception as exc:
                # If it's a validation error, log details
                if (
                    hasattr(exc, "status_code")
                    and int(getattr(exc, "status_code")) == 422
                ):
                    try:
                        request_data = json.loads(body.decode()) if body else {}
                    except:  # noqa: E722
                        request_data = (
                            body.decode() if body else "Could not decode body"
                        )

                    logger.error(f"""
=== 422 Validation Error (Exception) ===
Endpoint: {request.method} {request.url.path}
Request Body: {json.dumps(request_data, indent=2) if isinstance(request_data, dict) else request_data}
Error: {str(exc)}
Error Details: {getattr(exc, "detail") if hasattr(exc, "detail") else "No details"}
=========================================
                    """)
                raise

            return response

        return custom_route_handler
