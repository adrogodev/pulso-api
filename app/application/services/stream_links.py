from typing import Iterable

from app.domain.models.ytmusic.song import Song


class StreamLinkBuilder:
    """Builds the URLs the frontend uses to play audio through this API."""

    def __init__(self, public_base_url: str):
        self._base = public_base_url.rstrip("/")

    def url_for(self, video_id: str) -> str:
        return f"{self._base}/api/stream/{video_id}"

    def apply(self, songs: Iterable[Song]) -> None:
        for song in songs:
            if song.id:
                song.stream_url = self.url_for(song.id)
