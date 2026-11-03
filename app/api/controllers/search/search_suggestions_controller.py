from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.watch import SearchSuggestions


class SearchSuggestionsController(EnvelopeController[SearchSuggestions]):
    message = "Sugerencias obtenidas exitosamente"
