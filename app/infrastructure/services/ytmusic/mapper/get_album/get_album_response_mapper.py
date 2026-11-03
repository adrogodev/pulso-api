from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.song import Song
from app.infrastructure.services.ytmusic.mapper.common import to_artists, to_thumbnail
from app.infrastructure.services.ytmusic.objects.album.get_album_response import AlbumTrack, GetAlbumResponse


class GetAlbumResponseMapper:
    @staticmethod
    def _to_track(source: AlbumTrack, album_ref: Album, thumbnail: str | None) -> Song:
        return Song(
            id=source.videoId,
            title=source.title,
            thumbnail=to_thumbnail(source.thumbnails) or thumbnail,
            duration=source.duration,
            duration_seconds=source.duration_seconds,
            track_number=source.trackNumber,
            is_explicit=source.isExplicit,
            artists=to_artists(source.artists),
            album=album_ref,
        )

    @staticmethod
    def map(album_id: str, data: GetAlbumResponse) -> Album:
        thumbnail = to_thumbnail(data.thumbnails)
        album_ref = Album(id=album_id, title=data.title)
        return Album(
            id=album_id,
            title=data.title,
            description=data.description,
            thumbnail=thumbnail,
            duration=data.duration,
            duration_seconds=data.duration_seconds,
            year=data.year,
            artists=to_artists(data.artists),
            songs_count=data.trackCount,
            songs=[GetAlbumResponseMapper._to_track(t, album_ref, thumbnail) for t in data.tracks],
        )
