from ioc.container import Container
from app.infrastructure.services.ytmusic.services.album_service import AlbumService
from app.infrastructure.services.ytmusic.services.search_service import SearchService
from app.infrastructure.services.ytmusic.services.artist_service import ArtistService
from ytmusicapi import YTMusic

def config_infrastructure():

    # Registrar clientes
    # YTMusic client
    Container.register('ytmusic_client', lambda: YTMusic(), singleton=True)
    
    # Registrar servicios
    Container.register('search_service', lambda: SearchService(Container.resolve('ytmusic_client')), singleton=True)
    Container.register('album_service', lambda: AlbumService(Container.resolve('ytmusic_client')), singleton=True)
    Container.register('artist_service', lambda: ArtistService(Container.resolve('ytmusic_client')), singleton=True)
    
    