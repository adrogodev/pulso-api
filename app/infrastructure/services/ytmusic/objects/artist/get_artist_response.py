from pydantic import BaseModel
from typing import Optional, List
from app.infrastructure.services.ytmusic.objects.common.artist import YTMusicArtist as Artist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail as Thumbnail

class AlbumInfo(BaseModel):
    name: str
    id:Optional[str] = None

class SongResult(BaseModel):
    videoId: str
    title: str
    artists: List[Artist]
    album: Optional[AlbumInfo] = None
    likeStatus: Optional[str] = None
    inLibrary: Optional[bool] = None
    pinnedToListenAgain: Optional[bool] = None
    thumbnails: List[Thumbnail]
    isAvailable: Optional[bool] = None
    isExplicit: Optional[bool] = None
    videoType: Optional[str] = None
    views: Optional[str] = None

class SongsSection(BaseModel):
    browseId: Optional[str]
    results: List[SongResult]

class AlbumResult(BaseModel):
    title: str
    type: str
    artists: List[Artist]
    browseId: Optional[str]
    audioPlaylistId: Optional[str]
    thumbnails: List[Thumbnail]
    isExplicit: Optional[bool] = None

class AlbumsSection(BaseModel):
    results: List[AlbumResult]
    browseId: Optional[str]
    params: Optional[str]

class GetArtistResponse(BaseModel):
    description: Optional[str] = None
    views: Optional[str] = None
    name: Optional[str] = None
    channelId: Optional[str] = None
    shuffleId: Optional[str] = None
    radioId: Optional[str] = None
    subscribers: Optional[str] = None
    subscribed: Optional[bool] = None
    thumbnails: List[Thumbnail] = []    
    songs: Optional[SongsSection] = None
    albums: Optional[AlbumsSection] = None
