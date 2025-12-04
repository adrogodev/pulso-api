from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from app.application.use_cases.search.search_usecase import SearchUseCase
from ioc.container import Container

def config_application():

    # Registrar casos de uso
    Container.register('search_usecase', lambda: SearchUseCase(Container.resolve('search_service')), singleton=True)
    Container.register('get_album_usecase', lambda: GetAlbumUseCase(Container.resolve('album_service')), singleton=True)