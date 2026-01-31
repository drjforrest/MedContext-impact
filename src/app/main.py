from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
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
