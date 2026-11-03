from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.stream import StreamInfo


class GetStreamInfoController(EnvelopeController[StreamInfo]):
    message = "Informacion del stream obtenida exitosamente"
