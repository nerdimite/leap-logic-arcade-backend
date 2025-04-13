import multiprocessing
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from arcade.api.middleware.error_handler import ErrorHandlerMiddleware
from arcade.api.routes.admin_pic_perfect import router as pic_perfect_admin_router
from arcade.api.routes.pic_perfect import router as pic_perfect_router
from arcade.api.routes.teams import router as teams_router

# Load environment variables
load_dotenv()

app = FastAPI(title="Logic Arcade API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(pic_perfect_router)
app.include_router(pic_perfect_admin_router)
app.include_router(teams_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


def dev():
    """Run the API in development mode using uvicorn."""
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "True").lower() == "true"

    uvicorn.run("arcade.main:app", host=host, port=port, reload=reload_enabled)


def prod():
    """Run the API in production mode using gunicorn."""
    import gunicorn.app.base

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", str(multiprocessing.cpu_count())))

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {
        "bind": f"{host}:{port}",
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }

    StandaloneApplication(app, options).run()


if __name__ == "__main__":
    mode = os.getenv("API_MODE", "dev").lower()

    if mode == "prod":
        prod()
    else:
        dev()
