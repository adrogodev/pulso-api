from app.api.controllers.base_controller import EnvelopeController


class GetLinkSongController(EnvelopeController[str]):
    message = "Link obtenido exitosamente"
