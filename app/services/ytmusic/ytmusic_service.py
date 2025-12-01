from typing import List
from ytmusicapi import YTMusic
from app.services.ytmusic.objects.search.requests.search_request import SearchRequest
from app.services.ytmusic.objects.search.responses.song_response import SongResponse
from app.services.ytmusic.objects.search.responses.album_response import AlbumResponse
from app.services.ytmusic.objects.search.responses.artist_response import ArtistResponse
from app.services.ytmusic.objects.search.responses.playlist_response import PlaylistResponse

class YTMusicService:
    """Se incializa el cliente de YTMusic"""
    def __init__(self):
        self.client = YTMusic()

    """Realiza una busqueda de canciones"""
    def search_songs(self, data:SearchRequest) -> List[SongResponse]:
        result = self.client.search(
            query=data.value,
            filter='songs',
            scope=None,
            limit=data.limit,
            ignore_spelling=False
        )

        return [SongResponse(**item) for item in result]
    
    
    """Realiza una busqueda de albums"""
    def search_albums(self, data:SearchRequest) -> List[AlbumResponse]:
        result = self.client.search(
            query=data.value,
            filter='albums',
            scope=None,
            limit=data.limit,
            ignore_spelling=False
        )

        return [AlbumResponse(**item) for item in result]
    
    """Realiza una busqueda de artistas"""
    def search_artists(self, data:SearchRequest) -> List[ArtistResponse]:
        result = self.client.search(
            query=data.value,
            filter='artists',
            scope=None,
            limit=data.limit,
            ignore_spelling=False
        )

        return [ArtistResponse(**item) for item in result]

    """Realiza una busqueda de playlists"""
    def search_playlists(self, data:SearchRequest) -> List[PlaylistResponse]:
        result = self.client.search(
            query=data.value,
            filter='playlists',
            scope=None,
            limit=data.limit,
            ignore_spelling=False
        )

        return [PlaylistResponse(**item) for item in result]
