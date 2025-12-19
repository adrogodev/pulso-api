from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.artist import Artist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail
from app.infrastructure.services.ytmusic.objects.common.artist import YTMusicArtist
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import GetArtistResponse
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import AlbumResult
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import SongResult

class GetArtistResponseMapper:

    @staticmethod
    def _to_thumbnail(source: YTMusicThumbnail) -> str:
       if not source:
           return None
       return source[0].url.split("=")[0]

    @staticmethod
    def _to_artist(source: YTMusicArtist) -> Artist:
        return Artist(
            id=source.id,
            name=source.name
        )
    
    @staticmethod
    def _to_songs(source: SongResult) -> Song:
        return Song(
            id=source.videoId,
            title=source.title,
            thumbnail=GetArtistResponseMapper._to_thumbnail(source.thumbnails),
            artist=[GetArtistResponseMapper._to_artist(artist) for artist in source.artists]
        )

    @staticmethod
    def _to_album(source: AlbumResult) -> Album:
        return Album(
            id=source.browseId,
            title=source.title,
            thumbnail=GetArtistResponseMapper._to_thumbnail(source.thumbnails),
            
        )
  
    @staticmethod
    def map(data: GetArtistResponse) -> Artist:
        return Artist(
            name=data.name,
            subscribers=data.subscribers,
            description=data.description,
            views=data.views,
            thumbnail=GetArtistResponseMapper._to_thumbnail(data.thumbnails),
            count_albums=len(data.albums.results),
            albums=[GetArtistResponseMapper._to_album(album) for album in data.albums.results],
            count_songs=len(data.songs.results),
            songs=[GetArtistResponseMapper._to_songs(song) for song in data.songs.results]
        )