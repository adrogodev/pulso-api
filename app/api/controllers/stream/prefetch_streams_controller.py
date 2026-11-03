from app.api.controllers.base_controller import EnvelopeController
from app.application.dtos.outputs.stream_output import PrefetchResult


class PrefetchStreamsController(EnvelopeController[PrefetchResult]):
    message = "Prefetch programado"
