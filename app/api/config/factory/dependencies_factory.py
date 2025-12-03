from ioc.container import Container

def get_album_controller():
    return Container.resolve('get_album_controller')