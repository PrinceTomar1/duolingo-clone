"""FastAPI application: middleware, error mapping and router registration.

Deliberately thin. It wires things together and owns exactly one policy
decision -- how a domain error becomes an HTTP status code.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import course, dev, leaderboard, lessons, users
from app.services.exceptions import DomainError

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Backend for a Duolingo-style learning app. All grading, hearts, XP, "
        "streak and unlock logic is computed server-side."
    ),
)

# The browser calls this API cross-origin from the Next.js dev server or from a
# deployed frontend, so the allowed origins come from configuration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    """Translate a service-layer error into its HTTP status.

    One handler instead of try/except in every route: services raise meaning,
    this decides transport.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error": type(exc).__name__},
    )


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe for the platform's health check."""
    return {"status": "ok"}


app.include_router(course.router, prefix=settings.api_v1_prefix)
app.include_router(lessons.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(leaderboard.router, prefix=settings.api_v1_prefix)

# Registered only in debug builds -- see the module docstring.
if settings.debug:
    app.include_router(dev.router, prefix=settings.api_v1_prefix)
