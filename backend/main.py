from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routes import health, agent

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# Allow Streamlit frontend to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running"}