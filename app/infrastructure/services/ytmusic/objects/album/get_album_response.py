from typing import List, Optional, Dict
from pydantic import BaseModel

class Thumbnail(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class Artist(BaseModel):
    name: str
    id: Optional[str] = None


class FeedbackTokens(BaseModel):
    add: Optional[str] = None
    remove: Optional[str] = None


class ListenAgainTokens(BaseModel):
    pin: Optional[str] = None
    unpin: Optional[str] = None

class AlbumTrack(BaseModel):
    videoId: Optional[str] = None
    title: str
    artists: List[Artist]
    album: Optional[str] = None
    likeStatus: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None
    isAvailable: Optional[bool] = None
    isExplicit: Optional[bool] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    trackNumber: Optional[int] = None
    inLibrary: Optional[bool] = None
    feedbackTokens: Optional[FeedbackTokens] = None
    pinnedToListenAgain: Optional[bool] = None
    listenAgainFeedbackTokens: Optional[ListenAgainTokens] = None

class AlbumOtherVersion(BaseModel):
    title: str
    year: Optional[str] = None
    browseId: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None
    isExplicit: Optional[bool] = None

class GetAlbumResponse(BaseModel):
    title: str
    type: str
    thumbnails: List[Thumbnail]
    description: Optional[str] = None
    artists: List[Artist]
    year: Optional[str] = None
    trackCount: Optional[int] = None
    duration: Optional[str] = None
    audioPlaylistId: Optional[str] = None
    tracks: List[AlbumTrack]
    other_versions: Optional[List[AlbumOtherVersion]] = None
    duration_seconds: Optional[int] = None
