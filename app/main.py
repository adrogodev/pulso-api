from fastapi import FastAPI
from app.infrastructure.config.config_infrastructure import config_infrastructure
from app.application.config.config_application import config_application
from app.api.config.config_api import config_api
from app.api.routes.api_router import api_router
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.artist import Artist
from app.domain.models.ytmusic.search import Search

app = FastAPI(title="rythmx")

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

