from pymilvus import MilvusClient, Collection, CollectionSchema, connections

from config import config


# index params
sparse_vector_params = MilvusClient.prepare_index_params()
sparse_vector_params.add_index(
    field_name="sparse_vector", 
    metric_type="IP", 
    index_type="SPARSE_INVERTED_INDEX", 
    index_name="sparse_vector"
)

dense_vector_params = MilvusClient.prepare_index_params()
dense_vector_params.add_index(
    field_name="dense_vector",
    metric_type="IP", 
    index_type="FLAT", 
    index_name="dense_vector"
)


def prepare_milvus_oper(func):
    """ milvus 操作前的连接建立
    """
    def inner(*args, **kwargs):
        connections.connect(
            host=config.milvus_host, 
            port=config.milvus_port,
            db_name=config.milvus_db
        )
        collection = Collection(config.milvus_collection)
        collection.load()
        return func(collection, *args, **kwargs)
    return inner


def init_milvus_db():
    connections.connect(
        host=config.milvus_host,
        port=config.milvus_port,
        db_name=config.milvus_db
    )
    client = MilvusClient(
        uri=f"http://{config.milvus_host}:{config.milvus_port}", 
        db_name=config.milvus_db
    )
    
    try:
        client.create_database(config.milvus_db)
    except:
        print(f"{config.milvus_db} has already exists.")
    return client


def init_milvus_collection(client: MilvusClient, collection: str, schema: CollectionSchema):
    if not client.has_collection(collection_name=collection):
        client.create_collection(
            collection_name=config.milvus_collection,
            schema=schema,
            consistency_level="Strong"
        )
    client.create_index(collection_name=config.milvus_collection, index_params=sparse_vector_params)
    client.create_index(collection_name=config.milvus_collection, index_params=dense_vector_params)

