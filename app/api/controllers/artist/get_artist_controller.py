from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.artist import Artist


class GetArtistController(EnvelopeController[Artist]):
    message = "Artista obtenido exitosamente"
