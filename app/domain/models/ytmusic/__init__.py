"""YouTube Music domain models. Importing this package resolves their forward references."""

from app.domain.models.ytmusic.album import Album
from app.domain.models.ytmusic.artist import Artist
from app.domain.models.ytmusic.search import Search
from app.domain.models.ytmusic.song import Song
from app.domain.models.ytmusic.watch import Lyrics, SearchSuggestions, WatchPlaylist

_namespace = {"Album": Album, "Artist": Artist, "Song": Song}
for _model in (Song, Album, Artist, Search, WatchPlaylist):
    _model.model_rebuild(_types_namespace=_namespace)

__all__ = ["Album", "Artist", "Lyrics", "Search", "SearchSuggestions", "Song", "WatchPlaylist"]
