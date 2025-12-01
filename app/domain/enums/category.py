from enum import Enum

class Category(str, Enum):
    SONGS = "songs"
    ARTISTS = "artists"
    ALBUMS = "albums"
    PLAYLISTS = "playlists"