from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.config.factory.dependencies_factory import search_controller, search_suggestions_controller
from app.api.http.openapi import ERR_429, ERR_UPSTREAM, SEARCH_EXAMPLE, SUGGESTIONS_EXAMPLE
from app.api.http.responses import json_response
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from app.domain.models.ytmusic.watch import SearchSuggestions
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get(
    "",
    response_model=ResponseHttp[Search],
    summary="Search songs, videos, albums and artists",
    description="Every song and video includes a `stream_url` that plays through this API.",
    responses={**SEARCH_EXAMPLE, **ERR_429, **ERR_UPSTREAM},
)
async def search(request: Request, params: Annotated[SearchInput, Query()]):
    response = await search_controller().execute(params)
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)


@router.get(
    "/suggestions",
    response_model=ResponseHttp[SearchSuggestions],
    summary="Search suggestions for autocomplete",
    responses={**SUGGESTIONS_EXAMPLE, **ERR_429, **ERR_UPSTREAM},
)
async def suggestions(request: Request, q: Annotated[str, Query(min_length=1, max_length=100, examples=["daft"])]):
    response = await search_suggestions_controller().execute(q)
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)
