class SongUrlUseCase:
    def execute(self, videoId:str) -> str:
        return f'https://www.youtube.com/watch?v={videoId}' 