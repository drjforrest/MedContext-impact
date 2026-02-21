from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.modules import get_all_modules
from app.middleware.demo_protection import DemoProtectionMiddleware

app = FastAPI(title="MedContext API", version="0.1.0")

# CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://localhost:80",
        "https://medcontext.drjforrest.com",
        "http://medcontext.drjforrest.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo protection (access code + rate limiting)
app.add_middleware(DemoProtectionMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/modules")
def get_module_status() -> dict:
    """Return the enabled/disabled status of all MedContext modules."""
    return {
        "modules": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "category": m.category,
                "enabled": m.enabled,
            }
            for m in get_all_modules()
        ]
    }
