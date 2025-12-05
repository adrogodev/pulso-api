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
    def _to_artist(data: List[YTMusicArtist]) -> str:
        if not data:
            return None
        names = [artist.name for artist in data if artist]

        if len(names) == 1:
            return names[0]
        
        return ', '.join(names)
    
    @staticmethod
    def _to_thumbnail(data:List[YTMusicThumbnail]) -> str:
       if not data:
           return None
       return data[0].url

    @staticmethod
    def map(category:str,data: List[SearchResponse]) -> List[Search]:
        mapped = []
        for item in data:

            if category == Category.SONGS.value:
                mapped.append(
                Search(
                    id=item.videoId,
                    title=item.title,
                    thumbnail=SearchResponseMapper._to_thumbnail(item.thumbnails),
                    duration=item.duration,
                    duration_seconds=item.duration_seconds,
                    artists=SearchResponseMapper._to_artist(item.artists)
                )
            )
            
            if category == Category.ARTISTS.value:
                mapped.append(
                Search(
                    id=item.browseId,
                    name=item.artist,
                    thumbnail=SearchResponseMapper._to_thumbnail(item.thumbnails)
                )
            )     
            
            if category == Category.ALBUMS.value:
                mapped.append(
                Search(
                    id=item.browseId,
                    title=item.title,
                    thumbnail=SearchResponseMapper._to_thumbnail(item.thumbnails),
                    duration=item.duration,
                    duration_seconds=item.duration_seconds,
                    artists=SearchResponseMapper._to_artist(item.artists)
                )
            )

        return mapped
