import uvicorn

from app.db.milvus import init_milvus_collection, init_milvus_db
from app.model.concept import ConceptSchema, JobRequirementSchema
from config import config, PLog

PLog()


def init_milvus():
    """初始化 Milvus 连接和必要的 Collections"""
    from loguru import logger
    
    try:
        client = init_milvus_db()
        
        # 初始化 ConceptSchema（向后兼容）
        init_milvus_collection(client, config.milvus_collection, ConceptSchema)
        
        # 初始化 JobRequirementSchema（招聘要求）
        job_collection = getattr(config, "job_requirement_collection", "job_requirements")
        from app.model.concept import JobRequirementSchema
        init_milvus_collection(client, job_collection, JobRequirementSchema)
        
        logger.info("Milvus 初始化完成")
    except Exception as e:
        logger.error(f"Milvus 初始化失败: {e}")
        raise


if __name__ == '__main__':

    init_milvus()
    uvicorn.run(
        app="app:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        reload=config.reload
    )
