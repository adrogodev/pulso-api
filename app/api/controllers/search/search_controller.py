from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.search import Search


class SearchController(EnvelopeController[Search]):
    message = "Busqueda exitosa"
