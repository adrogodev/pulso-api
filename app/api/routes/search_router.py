from fastapi import APIRouter, Depends
from app.application.dtos.inputs.search_input import SearchInput
from app.api.config.factory.dependencies_factory import search_controller
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("")
async def search(request: SearchInput = Depends()):
    controller = search_controller()
    response = await controller.execute(request)
    
    return JSONResponse(
        content=response.model_dump(exclude_none=True)
    )
