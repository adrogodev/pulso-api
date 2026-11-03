from app.domain.contracts.services.ytmusic.watch_service import IWatchService
from app.domain.errors import NotFoundError
from app.domain.models.ytmusic.watch import Lyrics, WatchPlaylist
from app.infrastructure.services.ytmusic.client import YTMusicGateway
from app.infrastructure.services.ytmusic.mapper.watch.get_watch_playlist_response_mapper import (
    GetWatchPlaylistResponseMapper,
)
from app.infrastructure.services.ytmusic.objects.watch.get_watch_playlist_response import (
    GetLyricsResponse,
    GetWatchPlaylistResponse,
)


class WatchService(IWatchService):
    def __init__(self, gateway: YTMusicGateway):
        self._gateway = gateway

    async def _watch_raw(self, video_id: str, limit: int) -> GetWatchPlaylistResponse:
        raw = await self._gateway.call("get_watch_playlist", videoId=video_id, limit=limit)
        return GetWatchPlaylistResponse.model_validate(raw)

    async def get_watch_playlist(self, video_id: str, limit: int) -> WatchPlaylist:
        return GetWatchPlaylistResponseMapper.map(video_id, await self._watch_raw(video_id, limit))

    async def get_lyrics(self, video_id: str) -> Lyrics:
        # Lyrics are addressed by a browse id that only the watch playlist exposes
        watch = await self._watch_raw(video_id, limit=1)
        if not watch.lyrics:
            raise NotFoundError("No lyrics available for this song", code="LYRICS_NOT_FOUND")
        raw = await self._gateway.call("get_lyrics", watch.lyrics)
        data = GetLyricsResponse.model_validate(raw or {})
        if not data.lyrics:
            raise NotFoundError("No lyrics available for this song", code="LYRICS_NOT_FOUND")
        return Lyrics(video_id=video_id, text=data.lyrics, source=data.source)
