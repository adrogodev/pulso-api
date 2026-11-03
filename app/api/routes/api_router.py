from fastapi import APIRouter

from app.api.routes.album_router import router as album_router
from app.api.routes.artist_router import router as artist_router
from app.api.routes.search_router import router as search_router
from app.api.routes.song_router import router as song_router
from app.api.routes.stream_router import router as stream_router
from app.api.routes.watch_router import router as watch_router

api_router = APIRouter()

api_router.include_router(album_router)
api_router.include_router(search_router)
api_router.include_router(artist_router)
api_router.include_router(song_router)
api_router.include_router(stream_router)
api_router.include_router(watch_router)
