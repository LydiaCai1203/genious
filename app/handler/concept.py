from fastapi import APIRouter             

from app.schema import GerneralResponse
from app.schema.concept import QueryReqSchema
from app.repositry.milvus import embedding_and_query
from app.service.concept import get_most_relevant_concept

router = APIRouter()


@router.post("/query")
async def query_concept(item: QueryReqSchema):
    """ 新闻搜相关概念
    """
    response = GerneralResponse()
    concepts = embedding_and_query(item.news, item.top_k)
    if not concepts:
        return response
    concept_name, score = get_most_relevant_concept(concepts)
    data = {"distance": score, "concept": concept_name}
    response.data = data
    return response
