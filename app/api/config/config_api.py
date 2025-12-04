from ioc.container import Container
from app.api.controllers.album.get_album_controller import GetAlbumController
from app.api.controllers.search.search_controller import SearchController

def config_api():

    #Registrar controladores
    Container.register('search_controller', lambda: SearchController(Container.resolve('search_usecase')), singleton=True)
    
    Container.register('get_album_controller', lambda: GetAlbumController(Container.resolve('get_album_usecase')), singleton=True)