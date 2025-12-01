
from fastapi import APIRouter, Depends
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.success_response import SuccessResponse
from app.application.use_cases.songs.song_url import SongUrlUseCase
from app.application.use_cases.songs.get_songs import GetSongsUseCase
from app.application.dtos.outputs.search_output import SearchOutput
from app.application.use_cases.search.search_usecase import SearchUseCase

router = APIRouter(prefix="/api/search", tags=["Search"])

services = YTMusicService()
usecase = SearchUseCase(services)
get_songs_usecase = GetSongsUseCase(services)
song_url_usecase = SongUrlUseCase()

# Caso de uso de busqueda 
search_usecase = SearchUseCase(services)

@router.get("/query")
def search(params: SearchInput = Depends()) -> SuccessResponse[list[SearchOutput]]:
    results = search_usecase.execute(params)
    return SuccessResponse[list[SearchOutput]] (
        success=True, 
        message="Resultados de busqueda obtenidos exitosamente", 
        data=results
    )

# ------------------------------------------------------------------------------------------
@router.get("/get")
def get_songs(data: SearchInput = Depends()) -> SuccessResponse[list[SearchOutput]]:
    songs = get_songs_usecase.execute(data)
    return SuccessResponse[list[SearchOutput]] (
        success=True, 
        message="Resultado de busqueda exitoso", 
        data=songs
    )

@router.get("/url")
def song_url(videoId: str) -> SuccessResponse[str]:
    url = song_url_usecase.execute(videoId)
    return SuccessResponse[str] (
        success=True, 
        message="Url generada exitosamente", 
        data=url
    )
