from pydantic import BaseModel


class QueryReqSchema(BaseModel):
    news: str
    top_k: int = 5
