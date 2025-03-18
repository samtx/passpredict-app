from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Set Cache-Control header for API responses
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = "private, max-age=900"  # cache for 15 minutes
        return response
