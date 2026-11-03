from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.watch import Lyrics


class GetLyricsController(EnvelopeController[Lyrics]):
    message = "Letra obtenida exitosamente"
