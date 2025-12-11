from core.contracts.usecase_contract import UseCaseContract, UseCaseArgs
from core.config.settings.env_settings import settings

class GetLinkSongsUseCase(UseCaseContract[str, str]):
    async def execute(self, args: UseCaseArgs[str]) -> str:
        song_id = args.data
        link = settings.MUSIC_SOURCE_LINK + song_id
        return link