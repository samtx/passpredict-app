from functools import wraps


def cache_page(func):
    """
    Decorator that caches the response of a FastAPI async function.

    Example:
    ```
        app = FastAPI()

        @app.get("/")
        @cache_response
        async def example():
            return {"message": "Hello World"}
    ```
    Ref: https://blog.osull.com/2022/06/03/a-very-simple-async-response-cache-for-fastapi/
    """
    response = None

    @wraps(func)
    async def wrapper(*args, **kwargs):
        nonlocal response
        if not response:
            response = await func(*args, **kwargs)
        return response

    return wrapper