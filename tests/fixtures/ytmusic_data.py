"""Raw payloads shaped like ytmusicapi responses, shared by tests and the benchmark simulator."""

from copy import deepcopy

THUMBS = [
    {"url": "https://lh3.googleusercontent.com/thumb=w60-h60", "width": 60, "height": 60},
    {"url": "https://lh3.googleusercontent.com/thumb=w120-h120", "width": 120, "height": 120},
]

_SEARCH = [
    {
        "category": "Top result",
        "resultType": "artist",
        "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
        "thumbnails": THUMBS,
    },
    {
        "category": "Songs",
        "resultType": "song",
        "title": "Get Lucky",
        "videoId": "song_vid_01",
        "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
        "album": {"name": "Random Access Memories", "id": "MPREb_album_1"},
        "duration": "6:09",
        "duration_seconds": 369,
        "thumbnails": THUMBS,
    },
    {
        "category": "Videos",
        "resultType": "video",
        "title": "Get Lucky (Official Video)",
        "videoId": "video_vid_1",
        "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
        "views": "1B",
        "duration": "4:08",
        "duration_seconds": 248,
        "thumbnails": THUMBS,
    },
    {
        "category": "Albums",
        "resultType": "album",
        "title": "Random Access Memories",
        "browseId": "MPREb_album_1",
        "type": "Album",
        "year": "2013",
        "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
        "thumbnails": THUMBS,
    },
    {
        "category": "Artists",
        "resultType": "artist",
        "artist": "Daft Punk",
        "browseId": "UC_artist_1",
        "thumbnails": THUMBS,
    },
]

_ALBUM = {
    "title": "Random Access Memories",
    "type": "Album",
    "thumbnails": THUMBS,
    "description": "Fourth studio album.",
    "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
    "year": "2013",
    "trackCount": 2,
    "duration": "10 minutes",
    "audioPlaylistId": "OLAK5uy_playlist",
    "duration_seconds": 643,
    "tracks": [
        {
            "videoId": "track_vid_1",
            "title": "Give Life Back to Music",
            "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
            "album": "Random Access Memories",
            "isAvailable": True,
            "duration": "4:34",
            "duration_seconds": 274,
            "trackNumber": 1,
            "thumbnails": None,
        },
        {
            "videoId": "song_vid_01",
            "title": "Get Lucky",
            "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
            "album": "Random Access Memories",
            "isAvailable": True,
            "duration": "6:09",
            "duration_seconds": 369,
            "trackNumber": 2,
            "thumbnails": None,
        },
    ],
}

_ARTIST = {
    "name": "Daft Punk",
    "description": "French electronic duo.",
    "views": "2,000,000,000 views",
    "channelId": "UC_artist_1",
    "subscribers": "9M",
    "thumbnails": THUMBS,
    "songs": {
        "browseId": "VLsongs",
        "results": [
            {
                "videoId": "song_vid_01",
                "title": "Get Lucky",
                "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
                "album": {"name": "Random Access Memories", "id": "MPREb_album_1"},
                "thumbnails": THUMBS,
            }
        ],
    },
    "albums": {
        "browseId": "MPADalbums",
        "results": [
            {
                "title": "Random Access Memories",
                "type": "Album",
                "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
                "browseId": "MPREb_album_1",
                "audioPlaylistId": "OLAK5uy_playlist",
                "thumbnails": THUMBS,
                "year": "2013",
            }
        ],
    },
}

_WATCH = {
    "tracks": [
        {
            "videoId": "song_vid_01",
            "title": "Get Lucky",
            "length": "6:09",
            "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
            "album": {"name": "Random Access Memories", "id": "MPREb_album_1"},
            "thumbnail": THUMBS,
        },
        {
            "videoId": "track_vid_1",
            "title": "Give Life Back to Music",
            "length": "4:34",
            "artists": [{"name": "Daft Punk", "id": "UC_artist_1"}],
            "album": None,
            "thumbnail": THUMBS,
        },
    ],
    "playlistId": "RDAMVMsong_vid_01",
    "lyrics": "MPLYt_lyrics_1",
    "related": "MPTRt_related_1",
}

_LYRICS = {"lyrics": "Like the legend of the phoenix...", "source": "Source: LyricFind", "hasTimestamps": False}

_SUGGESTIONS = ["daft punk", "daft punk get lucky", "daft punk one more time"]


def search_results() -> list[dict]:
    return deepcopy(_SEARCH)


def album() -> dict:
    return deepcopy(_ALBUM)


def artist() -> dict:
    return deepcopy(_ARTIST)


def watch_playlist() -> dict:
    return deepcopy(_WATCH)


def lyrics() -> dict:
    return deepcopy(_LYRICS)


def suggestions() -> list[str]:
    return list(_SUGGESTIONS)
