from typing import Protocol

from app.domain.models.ytmusic.watch import Lyrics, WatchPlaylist


class IWatchService(Protocol):
    async def get_watch_playlist(self, video_id: str, limit: int) -> WatchPlaylist: ...

    async def get_lyrics(self, video_id: str) -> Lyrics: ...
