from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from app.infrastructure.config.config_infrastructure import config_infrastructure
from app.application.config.config_application import config_application
from app.api.config.config_api import config_api
from app.api.routes.api_router import api_router
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.artist import Artist
from app.domain.models.ytmusic.search import Search
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Rythmx API", docs_url=None, redoc_url=None)

@app.get("/docs", include_in_schema=True)
async def scalar_html():
    return get_scalar_api_reference()

@app.get("/")
def root():
    return {"message": "rythmx api running..."}


Song.model_rebuild()
Album.model_rebuild()
Artist.model_rebuild()
Search.model_rebuild()

config_infrastructure()
config_application()
config_api()

# Registrar routers
app.include_router(api_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


