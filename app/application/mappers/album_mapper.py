from app.services.ytmusic.objects.albums.responses.get_album_data_response import Artist as SourceArtist
from app.application.dtos.outputs.album_output import Artist
from app.services.ytmusic.objects.albums.responses.get_album_data_response import Thumbnail as SourceThumbnail
from app.application.dtos.outputs.album_output import Thumbnail
from app.services.ytmusic.objects.albums.responses.get_album_data_response import AlbumTrack as SourceAlbumTrack
from app.application.dtos.outputs.album_output import TrackOutput
from app.services.ytmusic.objects.albums.responses.get_album_data_response import GetAlbumDataResponse
from app.application.dtos.outputs.album_output import AlbumDataOutput

class AlbumMapper:
    @staticmethod
    def _to_artist(source: SourceArtist) -> Artist:
        return Artist(
            id=source.id,
            name=source.name
        )
    
    @staticmethod
    def _to_thumbnail(source: SourceThumbnail) -> Thumbnail:
        return Thumbnail(
            url=source.url,
            width=source.width or 0,
            height=source.height or 0
        )
    @staticmethod
    def _to_track(source: SourceAlbumTrack) -> TrackOutput:
        return TrackOutput(
            id=source.videoId,
            title=source.title,
            duration=source.duration,
            duration_seconds=source.duration_seconds,
            track_number=source.trackNumber,
            artists=[AlbumMapper._to_artist(a) for a in source.artists],
            thumbnails=[AlbumMapper._to_thumbnail(t) for t in (source.thumbnails or [])]
        )

    @staticmethod
    def map(data: GetAlbumDataResponse) -> AlbumDataOutput:
        return AlbumDataOutput(
            title=data.title,
            year=data.year,
            description=data.description,
            thumbnails=[AlbumMapper._to_thumbnail(t) for t in data.thumbnails],
            artists=[AlbumMapper._to_artist(a) for a in data.artists],
            track_count=data.trackCount,
            duration=data.duration,
            duration_seconds=data.duration_seconds,
            audio_playlist_id=data.audioPlaylistId,
            tracks=[AlbumMapper._to_track(t) for t in data.tracks]
        )
