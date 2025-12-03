from ioc.container import Container
from app.api.controllers.album.get_album_controller import GetAlbumController

def config_api():

    #Registrar controladores
    Container.register('get_album_controller', lambda: GetAlbumController(Container.resolve('get_album_usecase')), singleton=True)