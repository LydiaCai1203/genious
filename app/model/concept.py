from pymilvus import FieldSchema, CollectionSchema, DataType

from app.cache_pool import bge_m3_ef


JobSchema = CollectionSchema(
    [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="city", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="salary", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="seniority", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="company_name", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="company_industry", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="company_info", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="job_title", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="job_detail", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=bge_m3_ef.dim["dense"]),
    ],
    description="招聘要求"
)

