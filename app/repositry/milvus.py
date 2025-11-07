from pymilvus import RRFRanker, AnnSearchRequest

from app.db.milvus import prepare_milvus_oper
from app.cache_pool import get_bge_m3_ef


@prepare_milvus_oper
def embedding_and_insert(collection, docs: list, concepts: list, stock_codes: list):
    bge_m3_ef = get_bge_m3_ef()
    bge_m3_ef = get_bge_m3_ef()
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
    bge_m3_ef = get_bge_m3_ef()
    search_params = {"metric_type": "IP"}
    bge_m3_ef = get_bge_m3_ef()
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


# 招聘要求相关方法
@prepare_milvus_oper(collection_name=None)  # 将在装饰器内部从 config 获取 job_requirement_collection
def insert_job_requirements(collection, job_requirements: list):
    """
    插入招聘要求数据
    job_requirements: list of dict, 包含 city, salary, seniority, company_name, 
                      company_industry, company_info, job_title, job_detail
    """
    if not job_requirements:
        return
    
    # 构建文档文本用于嵌入
    docs = [
        f"{jr.get('job_title', '')} {jr.get('job_detail', '')} {jr.get('company_name', '')} {jr.get('company_industry', '')}"
        for jr in job_requirements
    ]
    
    bge_m3_ef = get_bge_m3_ef()
    docs_embeddings = bge_m3_ef.encode_documents(docs)
    
    entities = [
        [jr.get("city", "") for jr in job_requirements],
        [jr.get("salary", "") for jr in job_requirements],
        [jr.get("seniority", "") for jr in job_requirements],
        [jr.get("company_name", "") for jr in job_requirements],
        [jr.get("company_industry", "") for jr in job_requirements],
        [jr.get("company_info", "") for jr in job_requirements],
        [jr.get("job_title", "") for jr in job_requirements],
        [jr.get("job_detail", "") for jr in job_requirements],
        docs_embeddings["sparse"],
        docs_embeddings["dense"],
    ]
    
    res = collection.insert(entities)
    return res


@prepare_milvus_oper(collection_name=None)  # 将在装饰器内部从 config 获取 job_requirement_collection
def query_job_requirements(collection, query: str, top_k: int = 10, 
                           city: str = None, salary: str = None, 
                           industry: str = None, expr: str = None):
    """
    查询招聘要求
    query: 查询文本（岗位、技术栈等）
    top_k: 返回数量
    city, salary, industry: 过滤条件
    expr: 自定义过滤表达式
    """
    search_params = {"metric_type": "IP"}
    bge_m3_ef = get_bge_m3_ef()
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
    
    # 构建过滤表达式
    filter_exprs = []
    if city:
        filter_exprs.append(f'city == "{city}"')
    if salary:
        filter_exprs.append(f'salary == "{salary}"')
    if industry:
        filter_exprs.append(f'company_industry == "{industry}"')
    if expr:
        filter_exprs.append(expr)
    
    filter_expr = " && ".join(filter_exprs) if filter_exprs else None
    
    res = collection.hybrid_search(
        [sparse_req, dense_req],
        rerank=RRFRanker(),
        limit=top_k,
        expr=filter_expr,
        output_fields=["city", "salary", "seniority", "company_name", 
                      "company_industry", "company_info", "job_title", "job_detail"]
    )[0]
    
    rst = [
        {
            "distance": hit.distance,
            "city": hit.fields.get("city", ""),
            "salary": hit.fields.get("salary", ""),
            "seniority": hit.fields.get("seniority", ""),
            "company_name": hit.fields.get("company_name", ""),
            "company_industry": hit.fields.get("company_industry", ""),
            "company_info": hit.fields.get("company_info", ""),
            "job_title": hit.fields.get("job_title", ""),
            "job_detail": hit.fields.get("job_detail", ""),
        }
        for hit in res
    ]
    return rst



