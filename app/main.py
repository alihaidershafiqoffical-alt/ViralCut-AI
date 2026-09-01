from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routers import videos
from app.api.routers import ingest_url
from app.api.routers import jobs
import logging

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
import asyncio
from app.services.cleanup import CleanupService


async def periodic_cleanup_loop():
    logger.info("Starting background periodic cleanup loop.")
    # Run initial cleanup on start
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, CleanupService.cleanup_expired_jobs)
    except Exception as e:
        logger.error("Error running initial cleanup on startup: %s", e)

    while True:
        try:
            # Run cleanup every hour (3600 seconds)
            await asyncio.sleep(3600)
            logger.info("Running background periodic cleanup.")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, CleanupService.cleanup_expired_jobs)
        except asyncio.CancelledError:
            logger.info("Background periodic cleanup loop cancelled.")
            break
        except Exception as e:
            logger.error("Error in periodic cleanup loop: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(periodic_cleanup_loop())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS for the Next.js frontend, Vercel deployments, and local test runners
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ] + settings.ALLOWED_CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe exception handler: Prevents raw stack traces from reaching anonymous users
@app.exception_handler(Exception)
async def safe_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "A temporary processing error occurred. Please try again.",
            "status": "failed"
        }
    )

# Include routers
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
app.include_router(videos.router, prefix=f"{settings.API_V1_STR}/videos", tags=["videos"])
app.include_router(ingest_url.router, prefix=f"{settings.API_V1_STR}/videos", tags=["ingest"])

@app.get("/health")
def health_check():
    return {"status": "ok"}


