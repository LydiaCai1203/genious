from pymilvus import RRFRanker, AnnSearchRequest

from app.db.milvus import prepare_milvus_oper
from app.cache_pool import bge_m3_ef


@prepare_milvus_oper
def embedding_and_insert(collection, docs: list, concepts: list, stock_codes: list):
    docs_embeddings = bge_m3_ef.encode_documents(docs)
    entities = [
        docs,
        concepts,
        stock_codes,
        docs_embeddings["sparse"],
        docs_embeddings["dense"],
    ]
    res = collection.insert(entities)
    return res


@prepare_milvus_oper
def embedding_and_query(collection, query: str, top_k: int):
    search_params = {"metric_type": "IP"}
    query_embeddings = bge_m3_ef.encode_documents([query])
    sparse_req = AnnSearchRequest(
        query_embeddings["sparse"],
        "sparse_vector",
        search_params,
        limit=top_k
    )
    dense_req = AnnSearchRequest(
        query_embeddings["dense"],
        "dense_vector",
        search_params,
        limit=top_k
    )
    res = collection.hybrid_search(
        [sparse_req, dense_req],
        rerank=RRFRanker(), 
        limit=top_k, 
        output_fields=["content", "concept", "stock_code"]
    )[0]
    rst = [
        {
            "distance": hit.distance,
            "content": hit.fields["content"],
            "concept": hit.fields["concept"],
            "stock_code": hit.fields["stock_code"],
        }
        for hit in res
    ]
    return rst


@prepare_milvus_oper
def delete_with_condition(collection, expr: str):
    collection.delete(expr)

