from app.domain.models.ytmusic.artist import Artist

class IArtistService:
    def get_artist(self, artist_id: str) -> Artist:
        ...