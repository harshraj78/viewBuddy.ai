from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    dev_cors_origins = [
        "http://127.0.0.1:5175",
        "http://localhost:5175",
        "http://127.0.0.1:5199",
        "http://localhost:5199",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[*settings.cors_origins, *dev_cors_origins],
        allow_origin_regex=settings.backend_cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
