from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    filter: str | None = None
    scope: str | None = None
    limit: int = 20
    ignore_spelling: bool = False

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "filter": self.filter,
            "scope": self.scope,
            "limit": self.limit,
            "ignore_spelling": self.ignore_spelling
        }