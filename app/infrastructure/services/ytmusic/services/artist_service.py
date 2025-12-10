from app.infrastructure.services.ytmusic.mapper.artist.get_artist.get_artist_response_mapper import GetArtistResponseMapper
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import GetArtistResponse
from app.infrastructure.services.ytmusic.objects.album.get_album_response import GetAlbumResponse
from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse
from app.domain.contracts.services.ytmusic.artist_service import IArtistService
from app.domain.models.ytmusic.artist import Artist
from ytmusicapi import YTMusic
from typing import Optional, List

class ArtistService(IArtistService):
    def __init__(self, client: YTMusic):
        self._client = client
    
    def get_artist(self, artist_id: str) -> Optional[Artist]:
        try:
            raw = self._client.get_artist(artist_id)
            data = GetArtistResponse(**raw)

            # albums: List[GetAlbumResponse] = []
            # for album in data.albums.results:
            #     raw_album = self._client.get_album(browseId=album.browseId)
            #     artist_album = GetAlbumResponse(**raw_album)
            #     albums.append(artist_album)
            
            # raw_songs = self._client.search(query=data.name, filter="songs")

            # songs: List[SearchResponse] = []
            # for item in raw_songs:
            #     song = SearchResponse(**item)
            #     songs.append(song)

            return GetArtistResponseMapper.map(data)

        except Exception as e:
            print(f"Error en get_artist: {e}")
            return None