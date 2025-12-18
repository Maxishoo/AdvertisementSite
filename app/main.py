from fastapi import FastAPI
from app.db.session import db
from app.config import settings
from app.api.v1 import (users, ads, categories, locations,
                        tags, favorites, views, messages,
                        reports, analitics, batch_import)

app = FastAPI(
    title="Advertisements API",
    description="Апи сайта с объявлениями о продаже всякого",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(ads.router, prefix=settings.API_V1_STR)
app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(locations.router, prefix=settings.API_V1_STR)
app.include_router(tags.router, prefix=settings.API_V1_STR)
app.include_router(favorites.router, prefix=settings.API_V1_STR)
app.include_router(views.router, prefix=settings.API_V1_STR)
app.include_router(messages.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(analitics.router, prefix=settings.API_V1_STR)
app.include_router(batch_import.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Advertisements API",
        "docs": f"http://localhost:8000{settings.API_V1_STR}/docs"
    }
