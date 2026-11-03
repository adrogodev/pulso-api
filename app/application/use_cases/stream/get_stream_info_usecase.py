from app.application.services.stream_links import StreamLinkBuilder
from app.application.services.stream_resolver import StreamResolver
from app.domain.models.stream import StreamInfo
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetStreamInfoUseCase(UseCaseContract[str, StreamInfo]):
    def __init__(self, resolver: StreamResolver, links: StreamLinkBuilder):
        self._resolver = resolver
        self._links = links

    async def execute(self, args: UseCaseArgs[str]) -> StreamInfo:
        source = await self._resolver.get(args.data)
        return StreamInfo.from_source(source, self._links.url_for(source.video_id))
