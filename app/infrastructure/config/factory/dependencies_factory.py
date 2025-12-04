from ioc.container import Container

def search_service():
    return Container.resolve('ytmusic_client')

def get_album_service():
    return Container.resolve('ytmusic_client')