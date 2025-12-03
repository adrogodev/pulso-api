from ioc.container import Container

def get_album_service():
    return Container.resolve('ytmusic_client')