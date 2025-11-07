#!/usr/bin/env python3
"""测试 Milvus 连接"""
import sys
from loguru import logger

try:
    from app.db.milvus import init_milvus_db, init_milvus_collection
    from app.model.concept import ConceptSchema, JobRequirementSchema
    from config import config
    
    logger.info("=" * 50)
    logger.info("开始测试 Milvus 连接")
    logger.info(f"Milvus Host: {config.milvus_host}")
    logger.info(f"Milvus Port: {config.milvus_port}")
    logger.info(f"Milvus DB: {config.milvus_db}")
    logger.info(f"Milvus Collection: {config.milvus_collection}")
    logger.info(f"Job Requirement Collection: {getattr(config, 'job_requirement_collection', 'job_requirements')}")
    logger.info("=" * 50)
    
    # 测试连接
    try:
        client = init_milvus_db()
        logger.info("✓ Milvus 数据库连接成功")
        
        # 测试初始化 ConceptSchema
        try:
            init_milvus_collection(client, config.milvus_collection, ConceptSchema)
            logger.info(f"✓ Collection '{config.milvus_collection}' 初始化成功")
        except Exception as e:
            logger.error(f"✗ Collection '{config.milvus_collection}' 初始化失败: {e}")
            sys.exit(1)
        
        # 测试初始化 JobRequirementSchema
        job_collection = getattr(config, "job_requirement_collection", "job_requirements")
        try:
            init_milvus_collection(client, job_collection, JobRequirementSchema)
            logger.info(f"✓ Collection '{job_collection}' 初始化成功")
        except Exception as e:
            logger.error(f"✗ Collection '{job_collection}' 初始化失败: {e}")
            sys.exit(1)
        
        logger.info("=" * 50)
        logger.info("✓ 所有测试通过！Milvus 连接正常")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"✗ Milvus 连接失败: {e}")
        logger.error("请检查：")
        logger.error("1. Milvus 服务是否已启动")
        logger.error(f"2. 配置的地址 {config.milvus_host}:{config.milvus_port} 是否正确")
        logger.error("3. 网络连接是否正常")
        sys.exit(1)
        
except ImportError as e:
    logger.error(f"导入失败: {e}")
    logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)

