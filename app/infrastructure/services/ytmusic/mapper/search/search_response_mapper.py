from typing import List, Optional

from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.artist import Artist
from app.domain.models.ytmusic.search import Search
from app.domain.models.ytmusic.song import Song
from app.infrastructure.services.ytmusic.mapper.common import to_artists, to_thumbnail
from app.infrastructure.services.ytmusic.objects.search.search_response import AlbumInfo, SearchResponse


class SearchResponseMapper:
    @staticmethod
    def _to_album_ref(album: Optional[AlbumInfo]) -> Optional[Album]:
        if not album or not album.name:
            return None
        return Album(id=album.id, title=album.name)

    @staticmethod
    def _to_song(item: SearchResponse) -> Song:
        return Song(
            id=item.videoId,
            title=item.title or "Unknown",
            thumbnail=to_thumbnail(item.thumbnails),
            duration=item.duration,
            duration_seconds=item.duration_seconds,
            is_explicit=item.isExplicit,
            artists=to_artists(item.artists),
            album=SearchResponseMapper._to_album_ref(item.album),
        )

    @staticmethod
    def map(items: List[SearchResponse]) -> Search:
        result = Search()
        seen_artists: set[str] = set()

        def add_artist(artist_id: Optional[str], name: Optional[str], item: SearchResponse) -> None:
            if not name or (artist_id and artist_id in seen_artists):
                return
            if artist_id:
                seen_artists.add(artist_id)
            result.artists.append(Artist(id=artist_id, name=name, thumbnail=to_thumbnail(item.thumbnails)))

        for item in items:
            kind = item.resultType
            if kind == "artist":
                if item.category == "Top result" and item.artists:
                    add_artist(item.artists[0].id, item.artists[0].name, item)
                else:
                    add_artist(item.browseId, item.title or item.artist, item)
            elif kind == "song" and item.videoId:
                result.songs.append(SearchResponseMapper._to_song(item))
            elif kind == "video" and item.videoId:
                result.videos.append(SearchResponseMapper._to_song(item))
            elif kind == "album" and item.browseId:
                result.albums.append(
                    Album(
                        id=item.browseId,
                        title=item.title or "Unknown",
                        thumbnail=to_thumbnail(item.thumbnails),
                        year=item.year,
                        artists=to_artists(item.artists),
                    )
                )

        return result
