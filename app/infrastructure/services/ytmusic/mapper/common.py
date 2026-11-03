from typing import Iterable, List, Optional

from app.domain.models.ytmusic.artist import Artist
from app.infrastructure.services.ytmusic.objects.common.thumbnail import YTMusicThumbnail


def to_thumbnail(thumbs: Optional[List[YTMusicThumbnail]]) -> Optional[str]:
    """Return the thumbnail URL without the size suffix, which serves the original resolution."""
    if not thumbs or not thumbs[0].url:
        return None
    return thumbs[0].url.split("=")[0]


def to_artists(artists: Optional[Iterable]) -> List[Artist]:
    return [Artist(id=a.id, name=a.name) for a in (artists or []) if a.name]


def duration_to_seconds(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None
    try:
        seconds = 0
        for part in duration.split(":"):
            seconds = seconds * 60 + int(part)
        return seconds
    except ValueError:
        return None
