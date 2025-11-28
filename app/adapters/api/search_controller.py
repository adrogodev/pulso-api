
from fastapi import APIRouter, Depends
from app.application.use_cases.search import SearchUseCase
from app.services.ytmusic_service import YTMusicService
from app.application.dtos.inputs.search_input import SearchInput

router = APIRouter(prefix="/api/songs", tags=["Songs"])

services = YTMusicService()
usecase = SearchUseCase(services)

@router.get("/search")
def search(params: SearchInput = Depends()):
    return usecase.execute(params)