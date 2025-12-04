from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse
from app.domain.models.ytmusic.search import Search
from app.domain.models.common.artist import Artist
from app.domain.models.common.thumbnail import Thumbnail
from app.infrastructure.services.ytmusic.objects.search.search_response import Artist as YTMusicArtist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail
from typing import List
from app.domain.enums.category import Category

class SearchResponseMapper:

    @staticmethod
    def _to_artist(data: YTMusicArtist) -> Artist:
        if not data:
            return None            
        return Artist(
            id=data.id,
            name=data.name
        )
    
    @staticmethod
    def _to_thumbnail(data:List[YTMusicThumbnail]) -> str:
       if not data:
           return None
       return data[0].url

    @staticmethod
    def map(category:str,data: List[SearchResponse]) -> List[Search]:
        mapped = []
        for item in data:
            if category == Category.ARTISTS.value:
                mapped.append(
                Search(
                    id=item.browseId,
                    name=item.artist,
                    thumbnail=SearchResponseMapper._to_thumbnail(item.thumbnails)
                )
            )
            
            continue
            
            artist_list = []
            if item.artist:
                yt_artist = YTMusicArtist(
                id=item.browseId,
                name=item.artist
            )
                artist_list = [SearchResponseMapper._to_artist(yt_artist)]

            mapped.append(
                Search(
                    id=item.browseId,
                    name=item.artist,
                    title= None,
                    thumbnail=SearchResponseMapper._to_thumbnail(item.thumbnails),
                    description= None,
                    duration= None,
                    duration_seconds= None,
                    artist=artist_list,
                )
            )

        return mapped
