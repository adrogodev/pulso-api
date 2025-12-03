from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from ioc.container import Container

def config_application():

    # Registrar casos de uso
    Container.register('get_album_usecase', lambda: GetAlbumUseCase(Container.resolve('album_service')), singleton=True)