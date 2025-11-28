from ytmusicapi import YTMusic
from app.application.dtos.inputs.search_input import SearchInput
from app.application.dtos.outputs.search_output import Song
from typing import List

class YTMusicService:
    def __init__(self):
        self.client = YTMusic()

    def search(self, data:SearchInput) -> List[Song]:
        result = self.client.search(
            query=data.query,
            filter=data.filter,
            scope=data.scope,
            limit=data.limit,
            ignore_spelling=data.ignore_spelling
        )

        return [Song(**item) for item in result]
