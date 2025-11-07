from pymilvus import FieldSchema, CollectionSchema, DataType

# BGE-M3 的 dense vector 维度固定为 1024
# 使用固定值，避免在导入 Schema 时就触发 embedding model 的加载
BGE_M3_DENSE_DIM = 1024


# 临时概念检索 Schema（用于向后兼容）
ConceptSchema = CollectionSchema(
    [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="concept", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="stock_code", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=BGE_M3_DENSE_DIM),
    ],
    description="概念检索（临时）"
)


# 招聘要求 Schema
JobRequirementSchema = CollectionSchema(
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
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=BGE_M3_DENSE_DIM),
    ],
    description="招聘要求"
)



