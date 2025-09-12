import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import AuditMiddleware
from app.api.router import router as api_router
from app.core.config.api import config as cfg_api
from app.core.env import config as cfg_env
from app.db.mongo import pymongo_db
from app.init import init_data
from app.services.rate_limit_service import RateLimiter

# Create FastAPI instance
app = FastAPI(
    debug=cfg_api.DEBUG,
    title=cfg_env.APP_TITLE,
    contact={
        "name": cfg_env.APP_NAME,
        "url": str(cfg_env.APP_URL),
        "email": str(cfg_env.APP_EMAIL),
    },
    on_startup=[
        init_data,
    ],
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    AuditMiddleware,  # type: ignore  # noqa: PGH003
    db=pymongo_db,
)

# Add rate limiter
app.state.limiter = RateLimiter()

# Include routers
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        reload=cfg_api.DEBUG,
        host="0.0.0.0",  # noqa: S104
        port=cfg_env.APP_PORT,
    )
