from typing import List, Optional

from pydantic import BaseModel

from app.infrastructure.services.ytmusic.objects.common.artist import YTMusicArtist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail


class WatchAlbum(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None


class WatchTrack(BaseModel):
    videoId: Optional[str] = None
    title: Optional[str] = None
    length: Optional[str] = None
    artists: List[YTMusicArtist] = []
    album: Optional[WatchAlbum] = None
    thumbnail: List[YTMusicThumbnail] = []
    isExplicit: Optional[bool] = None


class GetWatchPlaylistResponse(BaseModel):
    tracks: List[WatchTrack] = []
    playlistId: Optional[str] = None
    lyrics: Optional[str] = None
    related: Optional[str] = None


class GetLyricsResponse(BaseModel):
    lyrics: Optional[str] = None
    source: Optional[str] = None
