from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.watch import WatchPlaylist
from app.infrastructure.services.ytmusic.mapper.common import duration_to_seconds, to_artists, to_thumbnail
from app.infrastructure.services.ytmusic.objects.watch.get_watch_playlist_response import (
    GetWatchPlaylistResponse,
    WatchTrack,
)


class GetWatchPlaylistResponseMapper:
    @staticmethod
    def _to_song(source: WatchTrack) -> Song:
        album = source.album
        return Song(
            id=source.videoId,
            title=source.title or "Unknown",
            thumbnail=to_thumbnail(source.thumbnail),
            duration=source.length,
            duration_seconds=duration_to_seconds(source.length),
            is_explicit=source.isExplicit,
            artists=to_artists(source.artists),
            album=Album(id=album.id, title=album.name) if album and album.name else None,
        )

    @staticmethod
    def map(video_id: str, data: GetWatchPlaylistResponse) -> WatchPlaylist:
        return WatchPlaylist(
            video_id=video_id,
            playlist_id=data.playlistId,
            lyrics_id=data.lyrics,
            related_id=data.related,
            tracks=[GetWatchPlaylistResponseMapper._to_song(t) for t in data.tracks if t.videoId],
        )
