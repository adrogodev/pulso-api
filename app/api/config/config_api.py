from ioc.container import Container
from app.api.controllers.artist.get_artist_controller import GetArtistController
from app.api.controllers.album.get_album_controller import GetAlbumController
from app.api.controllers.search.search_controller import SearchController
from app.api.controllers.song.get_link_song_controller import GetLinkSongController

def config_api():

    #Registrar controladores
    Container.register('search_controller', lambda: SearchController(Container.resolve('search_usecase')), singleton=True)
    
    Container.register('get_album_controller', lambda: GetAlbumController(Container.resolve('get_album_usecase')), singleton=True)
    
    Container.register('get_artist_controller', lambda: GetArtistController(Container.resolve('get_artist_usecase')), singleton=True)

    Container.register('get_link_song_controller', lambda: GetLinkSongController(Container.resolve('get_link_songs_usecase')), singleton=True)