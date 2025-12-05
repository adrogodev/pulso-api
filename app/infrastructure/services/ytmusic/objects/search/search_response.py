from typing import List, Optional
from pydantic import BaseModel

class Thumbnail(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None

class ArtistInfo(BaseModel):
    name: str
    id: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None

class AlbumInfo(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None

class SearchResponse(BaseModel):
    category: Optional[str] = None
    resultType: Optional[str] = None
    
    # Campos comunes
    title: Optional[str] = None
    videoId: Optional[str] = None
    artists: Optional[List[ArtistInfo]] = None
    thumbnails: Optional[List[Thumbnail]] = None
    
    # Para canciones
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    views: Optional[str] = None
    isExplicit: Optional[bool] = False
    
    # Para álbumes
    playlistId: Optional[str] = None
    year: Optional[str] = None
    type: Optional[str] = None
    browseId: Optional[str] = None
    
    # Para artistas
    artist: Optional[str] = None
    subscribers: Optional[str] = None

    # ¡NUEVO! Álbum de la canción
    album: Optional[AlbumInfo] = None