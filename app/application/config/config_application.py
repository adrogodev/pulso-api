from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from app.application.use_cases.search.search_usecase import SearchUseCase
from app.application.use_cases.artist.get_artist_usecase import GetArtistUseCase
from app.application.use_cases.songs.get_link_songs_usecase import GetLinkSongsUseCase
from ioc.container import Container

def config_application():

    # Registrar casos de uso
    Container.register('search_usecase', lambda: SearchUseCase(Container.resolve('search_service')), singleton=True)
    Container.register('get_album_usecase', lambda: GetAlbumUseCase(Container.resolve('album_service')), singleton=True)
    Container.register('get_artist_usecase', lambda: GetArtistUseCase(Container.resolve('artist_service')), singleton=True)
    Container.register('get_link_songs_usecase', lambda: GetLinkSongsUseCase(), singleton=True)