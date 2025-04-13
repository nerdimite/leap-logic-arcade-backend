from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            # Let FastAPI's HTTPExceptions pass through unchanged
            raise e
        except ValueError as e:
            # Handle validation errors with 400 status
            return JSONResponse(status_code=400, content={"detail": str(e)})
        except Exception as e:
            # Handle any other exceptions as 500 internal server errors
            return JSONResponse(status_code=500, content={"detail": str(e)})
