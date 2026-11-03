from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from app.domain.models.stream import VIDEO_ID_PATTERN


class AudioStreamRequest(BaseModel):
    video_id: str
    range_header: Optional[str] = None


class PrefetchInput(BaseModel):
    video_ids: List[Annotated[str, Field(pattern=VIDEO_ID_PATTERN)]] = Field(
        min_length=1, max_length=50, examples=[["dQw4w9WgXcQ", "kJQP7kiw5Fk"]]
    )
