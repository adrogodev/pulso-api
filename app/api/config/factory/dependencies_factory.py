from ioc.container import Container

def search_controller():
    return Container.resolve('search_controller')

def get_album_controller():
    return Container.resolve('get_album_controller')

def get_artist_controller():
    return Container.resolve('get_artist_controller')

def get_link_song_controller():
    return Container.resolve('get_link_song_controller')
