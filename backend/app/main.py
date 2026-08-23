from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calendar, home, inventory, menu, shopping, training
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)
app.include_router(calendar.router)
app.include_router(menu.router)
app.include_router(training.router)
app.include_router(shopping.router)
app.include_router(inventory.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
