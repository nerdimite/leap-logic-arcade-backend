from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from arcade.core.commons.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            # Let FastAPI's HTTPExceptions pass through unchanged
            logger.error(f"HTTPException in middleware: {str(e)}", exc_info=True)
            raise e
        except ValueError as e:
            # Handle validation errors with 400 status
            logger.error(f"Validation error in middleware: {str(e)}", exc_info=True)
            return JSONResponse(status_code=400, content={"detail": str(e)})
        except Exception as e:
            # Handle any other exceptions as 500 internal server errors
            logger.error(f"Error in middleware: {str(e)}", exc_info=True)
            return JSONResponse(status_code=500, content={"detail": str(e)})
