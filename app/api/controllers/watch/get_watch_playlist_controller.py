from app.api.controllers.base_controller import EnvelopeController
from app.domain.models.ytmusic.watch import WatchPlaylist


class GetWatchPlaylistController(EnvelopeController[WatchPlaylist]):
    message = "Cola de reproduccion obtenida exitosamente"
