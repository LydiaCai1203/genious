from pymilvus import MilvusClient, Collection, CollectionSchema, connections, db

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


def prepare_milvus_oper(collection_name: str = None):
    """ milvus 操作前的连接建立装饰器
    
    Args:
        collection_name: 指定的 collection 名称，如果为 None 则使用默认的 config.milvus_collection
                         如果函数名包含 'job_requirement'，则自动使用 job_requirement_collection
    """
    def decorator(func):
        def inner(*args, **kwargs):
            # 确保端口是整数类型
            port = int(config.milvus_port) if isinstance(config.milvus_port, str) else config.milvus_port
            
            # 使用连接别名，避免重复连接冲突
            alias = "default"
            
            # 每次操作时重新连接，确保使用正确的数据库
            # 如果连接已存在，先断开再连接（避免连接冲突）
            try:
                connections.disconnect(alias)
            except:
                pass
            
            # 连接到指定数据库
            connections.connect(
                host=config.milvus_host, 
                port=port,
                db_name=config.milvus_db,
                alias=alias
            )
            
            # 确定使用的 collection 名称
            if collection_name:
                coll_name = collection_name
            elif 'job_requirement' in func.__name__:
                # 如果函数名包含 job_requirement，使用招聘要求 collection
                coll_name = getattr(config, "job_requirement_collection", "job_requirements")
            else:
                # 默认使用配置的 collection
                coll_name = config.milvus_collection
            
            # 使用连接别名获取 collection
            collection = Collection(coll_name, using=alias)
            collection.load()
            return func(collection, *args, **kwargs)
        return inner
    return decorator


def init_milvus_db():
    """初始化 Milvus 数据库连接，如果数据库不存在则自动创建"""
    from loguru import logger
    
    # 确保端口是整数类型
    port = int(config.milvus_port) if isinstance(config.milvus_port, str) else config.milvus_port
    
    # 先连接到默认数据库（不指定 db_name）来创建目标数据库
    try:
        # 连接到默认数据库
        connections.connect(
            host=config.milvus_host,
            port=port
        )
        logger.debug(f"已连接到 Milvus 默认数据库: {config.milvus_host}:{port}")
    except Exception as e:
        logger.error(f"连接 Milvus 默认数据库失败: {e}")
        raise
    
    # 使用 db 模块创建目标数据库
    try:
        # 列出所有数据库
        existing_dbs = db.list_database()
        if config.milvus_db not in existing_dbs:
            db.create_database(config.milvus_db)
            logger.info(f"数据库 {config.milvus_db} 创建成功")
        else:
            logger.debug(f"数据库 {config.milvus_db} 已存在")
    except Exception as e:
        logger.warning(f"检查/创建数据库 {config.milvus_db} 时出错: {e}，尝试继续...")
        # 如果检查失败，直接尝试创建（可能已存在）
        try:
            db.create_database(config.milvus_db)
            logger.info(f"数据库 {config.milvus_db} 创建成功")
        except Exception as create_err:
            error_msg = str(create_err).lower()
            if 'already exists' in error_msg or 'exist' in error_msg:
                logger.debug(f"数据库 {config.milvus_db} 已存在")
            else:
                logger.warning(f"创建数据库失败: {create_err}")
    
    # 切换到目标数据库（使用 db.using_database 后，当前连接就会使用该数据库）
    try:
        db.using_database(config.milvus_db)
        logger.info(f"已切换到数据库: {config.milvus_db}")
    except Exception as e:
        logger.error(f"切换数据库失败: {e}")
        raise
    
    # 创建目标数据库的客户端（使用已切换的数据库）
    client = MilvusClient(
        uri=f"http://{config.milvus_host}:{port}", 
        db_name=config.milvus_db
    )
    
    logger.info(f"Milvus 初始化完成: {config.milvus_host}:{port}, db: {config.milvus_db}")
    return client


def init_milvus_collection(client: MilvusClient, collection: str, schema: CollectionSchema):
    """初始化 Milvus Collection"""
    from loguru import logger
    
    if not client.has_collection(collection_name=collection):
        try:
            client.create_collection(
                collection_name=collection,
                schema=schema,
                consistency_level="Strong"
            )
            logger.info(f"Collection {collection} 创建成功")
        except Exception as e:
            logger.error(f"创建 Collection {collection} 失败: {e}")
            raise
    else:
        logger.info(f"Collection {collection} 已存在")
    
    # 创建索引（如果不存在）
    try:
        client.create_index(collection_name=collection, index_params=sparse_vector_params)
        client.create_index(collection_name=collection, index_params=dense_vector_params)
        logger.debug(f"Collection {collection} 索引创建/检查完成")
    except Exception as e:
        logger.debug(f"Collection {collection} 索引可能已存在: {e}")

