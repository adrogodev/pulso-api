from app.api.config.factory.dependencies_factory import search_controller
from core.models.response_model import ResponseHttp
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("", response_model=ResponseHttp[Search])
async def search(request: SearchInput = Depends()):
    controller = search_controller()
    response = await controller.execute(request)
    
    return JSONResponse(
        content=response.model_dump(exclude_none=True)
    )
