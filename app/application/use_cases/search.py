from typing import List
from app.application.dtos.outputs.search_output import Song
from app.application.dtos.inputs.search_input import SearchInput

class SearchUseCase:
    def __init__(self, services: YTMusicService):
        self.services = services
    
    def execute(self, query: SearchInput) -> List[Song]:
        return self.services.search(query)