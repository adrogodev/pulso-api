from fastapi import APIRouter
from app.api.routes.album_router import router as album_router

api_router = APIRouter()

api_router.include_router(album_router)
