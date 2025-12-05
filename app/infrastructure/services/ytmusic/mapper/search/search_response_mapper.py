from typing import List
from app.domain.models.ytmusic.search import Search
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.artist import Artist
from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse
from app.domain.models.ytmusic.album import Album

class SearchResponseMapper:

    @staticmethod
    def _to_thumbnails(thumbs: List[Thumbnail]) -> str:
        if not thumbs:
            return None

        first_url = thumbs[0].url
        if not first_url:
            return None
            
        return first_url.split("=")[0]

    @staticmethod
    def _to_artists(artists_data) -> List[Artist]:
        return [
            Artist(
                name=a.name, 
                id=a.id, 
                thumbnail=SearchResponseMapper._to_thumbnails(a.thumbnails)
            ) for a in (artists_data or []) if a.name]

    @staticmethod
    def _to_album(album_info: Optional[AlbumInfo], thumbnails: List[dict]) -> Optional[Album]:
        if not album_info or not album_info.name:
            return None
        return Album(
            title=album_info.name,
            id=album_info.id,
            year=None,
            thumbnails=SearchResponseMapper._to_thumbnails(thumbnails)
        )

    @staticmethod
    def map(items: List[SearchResponse]) -> Search:
        songs = []
        artists = []

        for item in items:
            # Top result (artista)
            if item.category == "Top result" and item.resultType == "artist":
                if item.artists:
                    artists.append(
                        Artist(
                            id=item.artists[0].id,
                            name=item.artists[0].name,
                            thumbnail=SearchResponseMapper._to_thumbnails(item.thumbnails)
                        )
                    )
                continue

            # Artistas normales
            if item.resultType == "artist":
                name = item.title or item.artist
                if name:
                    artists.append(
                        Artist(
                            name=name, 
                            id=item.browseId,
                            thumbnail=SearchResponseMapper._to_thumbnails(item.thumbnails)
                        )
                    )

            # Canciones
            if item.resultType == "song" and item.videoId:
                songs.append(
                    Song(
                        id=item.videoId,
                        title=item.title or "Unknown",
                        thumbnail=SearchResponseMapper._to_thumbnails(item.thumbnails),
                        duration=item.duration,
                        duration_seconds=item.duration_seconds,
                        artists=SearchResponseMapper._to_artists(item.artists),
                ))

        return Search(
            songs=songs,
            artists=artists
        )