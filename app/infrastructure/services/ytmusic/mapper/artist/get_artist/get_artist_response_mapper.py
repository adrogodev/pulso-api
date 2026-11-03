from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.artist import Artist
from app.domain.models.ytmusic.song import Song
from app.infrastructure.services.ytmusic.mapper.common import to_artists, to_thumbnail
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import (
    AlbumResult,
    GetArtistResponse,
    SongResult,
)


class GetArtistResponseMapper:
    @staticmethod
    def _to_song(source: SongResult) -> Song:
        return Song(
            id=source.videoId,
            title=source.title,
            thumbnail=to_thumbnail(source.thumbnails),
            is_explicit=source.isExplicit,
            artists=to_artists(source.artists),
            album=Album(id=source.album.id, title=source.album.name) if source.album else None,
        )

    @staticmethod
    def _to_album(source: AlbumResult) -> Album:
        return Album(
            id=source.browseId,
            title=source.title,
            year=source.year,
            thumbnail=to_thumbnail(source.thumbnails),
        )

    @staticmethod
    def map(artist_id: str, data: GetArtistResponse) -> Artist:
        songs = data.songs.results if data.songs else []
        albums = data.albums.results if data.albums else []
        return Artist(
            id=data.channelId or artist_id,
            name=data.name or "Unknown",
            subscribers=data.subscribers,
            description=data.description,
            views=data.views,
            thumbnail=to_thumbnail(data.thumbnails),
            count_albums=len(albums),
            albums=[GetArtistResponseMapper._to_album(a) for a in albums],
            count_songs=len(songs),
            songs=[GetArtistResponseMapper._to_song(s) for s in songs if s.videoId],
        )
