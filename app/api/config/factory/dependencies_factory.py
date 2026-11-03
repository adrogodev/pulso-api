from ioc.container import Container


def search_controller():
    return Container.resolve('search_controller')


def search_suggestions_controller():
    return Container.resolve('search_suggestions_controller')


def get_album_controller():
    return Container.resolve('get_album_controller')


def get_artist_controller():
    return Container.resolve('get_artist_controller')


def get_link_song_controller():
    return Container.resolve('get_link_song_controller')


def get_audio_stream_controller():
    return Container.resolve('get_audio_stream_controller')


def get_stream_info_controller():
    return Container.resolve('get_stream_info_controller')


def prefetch_streams_controller():
    return Container.resolve('prefetch_streams_controller')


def get_watch_playlist_controller():
    return Container.resolve('get_watch_playlist_controller')


def get_lyrics_controller():
    return Container.resolve('get_lyrics_controller')
