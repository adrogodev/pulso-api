from fastapi import APIRouter
from app.api.routes.album_router import router as album_router
from app.api.routes.search_router import router as search_router
from app.api.routes.artist_router import router as artist_router

api_router = APIRouter()

api_router.include_router(album_router)
api_router.include_router(search_router)
api_router.include_router(artist_router)
