from app.api.controllers.album.get_album_controller import GetAlbumController
from app.api.controllers.artist.get_artist_controller import GetArtistController
from app.api.controllers.search.search_controller import SearchController
from app.api.controllers.search.search_suggestions_controller import SearchSuggestionsController
from app.api.controllers.song.get_link_song_controller import GetLinkSongController
from app.api.controllers.stream.get_audio_stream_controller import GetAudioStreamController
from app.api.controllers.stream.get_stream_info_controller import GetStreamInfoController
from app.api.controllers.stream.prefetch_streams_controller import PrefetchStreamsController
from app.api.controllers.watch.get_lyrics_controller import GetLyricsController
from app.api.controllers.watch.get_watch_playlist_controller import GetWatchPlaylistController
from ioc.container import Container

_CONTROLLERS = {
    'search_controller': (SearchController, 'search_usecase'),
    'search_suggestions_controller': (SearchSuggestionsController, 'search_suggestions_usecase'),
    'get_album_controller': (GetAlbumController, 'get_album_usecase'),
    'get_artist_controller': (GetArtistController, 'get_artist_usecase'),
    'get_link_song_controller': (GetLinkSongController, 'get_link_songs_usecase'),
    'get_audio_stream_controller': (GetAudioStreamController, 'get_audio_stream_usecase'),
    'get_stream_info_controller': (GetStreamInfoController, 'get_stream_info_usecase'),
    'prefetch_streams_controller': (PrefetchStreamsController, 'prefetch_streams_usecase'),
    'get_watch_playlist_controller': (GetWatchPlaylistController, 'get_watch_playlist_usecase'),
    'get_lyrics_controller': (GetLyricsController, 'get_lyrics_usecase'),
}


def config_api():

    # Registrar controladores
    for key, (controller, usecase) in _CONTROLLERS.items():
        Container.register(key, lambda c=controller, u=usecase: c(Container.resolve(u)), singleton=True)
