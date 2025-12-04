from ioc.container import Container

def search_usecase():
    return Container.resolve('search_usecase')

def get_album_usecase():
    return Container.resolve('get_album_usecase')
