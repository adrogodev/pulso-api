from app.infrastructure.services.ytmusic.objects.common.artist import YTMusicArtist
from app.domain.models.common.artist import CommonArtist as Artist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail
from app.domain.models.common.thumbnail import CommonThumbnail as Thumbnail
from app.infrastructure.services.ytmusic.objects.album.get_album_response import AlbumTrack as YTMusicAlbumTrack
from app.domain.models.common.track import CommonTrack as Track 
from app.infrastructure.services.ytmusic.objects.album.get_album_response import GetAlbumResponse
from app.domain.models.common.album import CommonAlbum as Album


class GetAlbumResponseMapper:
    @staticmethod
    def _to_artist(source: YTMusicArtist) -> Artist:
        return Artist(
            id=source.id,
            name=source.name
        )
    
    @staticmethod
    def _to_thumbnail(source: YTMusicThumbnail) -> str:
       if not source:
           return None
       return source[0].url
       
    @staticmethod
    def _to_track(source: YTMusicAlbumTrack) -> Track:
        return Track(
            id=source.videoId,
            title=source.title,
            duration=source.duration,
            duration_seconds=source.duration_seconds,
            track_number=source.trackNumber,
            artists=[GetAlbumResponseMapper._to_artist(a) for a in source.artists],
            thumbnails=GetAlbumResponseMapper._to_thumbnail(source.thumbnails),
        )

    @staticmethod
    def map(data: GetAlbumResponse) -> Album:
        return Album(
            title=data.title,
            year=data.year,
            description=data.description,
            thumbnails=GetAlbumResponseMapper._to_thumbnail(data.thumbnails),
            artists=[GetAlbumResponseMapper._to_artist(a) for a in data.artists],
            track_count=data.trackCount,
            duration=data.duration,
            duration_seconds=data.duration_seconds,
            audio_playlist_id=data.audioPlaylistId,
            tracks=[GetAlbumResponseMapper._to_track(t) for t in data.tracks]
        )