from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.album import Album


class GetAlbumController(EnvelopeController[Album]):
    message = "Album obtenido exitosamente"
