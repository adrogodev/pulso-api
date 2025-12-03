from ioc.container import Container


def get_album_usecase():
    return Container.resolve('get_album_usecase')