from enum import Enum


class Category(str, Enum):
    SONGS = "songs"
    VIDEOS = "videos"
    ARTISTS = "artists"
    ALBUMS = "albums"
