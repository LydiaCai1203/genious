
import time
from datetime import datetime

from tqdm import tqdm

from app.model.concept import ConceptSchema, JobRequirementSchema
from app.db.milvus import init_milvus_db, init_milvus_collection
from app.service.concept import get_concept_stocks
from app.service.data_collector import data_collector
from app.repositry.milvus import delete_with_condition, embedding_and_insert
from utils.utils import average_split
from config import config


def init_milvus():
    client = init_milvus_db()
    init_milvus_collection(client, config.milvus_collection, ConceptSchema)


def update_concept_collection():
    data = get_concept_stocks()
    
    delete_with_condition("pk>=0")
    
    group = average_split(data, 50)
    with tqdm(total=len(group)) as pbar:
        for item in group:
            docs = [
                f"{i['name']}: {i['definition']}。{i['stock_name']}({i['stock_code']}), {i['reason']}"
                for i in item
            ]
            stock_codes = [i["stock_code"] for i in item]
            concepts = [i["name"] for i in item]
            embedding_and_insert(docs, concepts, stock_codes)
            pbar.update(1)


def update_concept_collection_everyday():
    # 每天晚上6点执行更新概念
    while True:
        hour = datetime.now().strftime("%H")
        if hour != "18":
            time.sleep(60 * 60)
        update_concept_collection()


def collect_job_requirements_daily():
    """每天收集招聘要求数据"""
    logger.info("开始收集招聘要求数据")
    try:
        # 收集主要城市的招聘要求
        cities = ["北京", "上海", "深圳", "杭州", "广州"]
        job_titles = ["Python开发", "Java开发", "Golang开发", "前端开发"]
        
        for city in cities:
            for job_title in job_titles:
                data_collector.collect_and_save_job_requirements(
                    city=city,
                    job_title=job_title,
                    limit=50
                )
                time.sleep(5)  # 避免请求过快
        
        logger.info("招聘要求数据收集完成")
    except Exception as e:
        logger.error(f"收集招聘要求失败: {e}")


def run_daily_tasks():
    """运行每日定时任务"""
    while True:
        hour = datetime.now().strftime("%H")
        if hour == "02":  # 每天凌晨2点执行
            logger.info("开始执行每日数据收集任务")
            
            # 收集招聘要求
            collect_job_requirements_daily()
            
            # 等待到下一个执行时间（避免重复执行）
            time.sleep(3600)  # 等待1小时
        else:
            time.sleep(3600)  # 每小时检查一次


if __name__ == "__main__":
    from loguru import logger
    
    init_milvus()
    
    # 可以选择运行不同的任务
    import sys
    if len(sys.argv) > 1:
        task = sys.argv[1]
        if task == "concept":
            update_concept_collection_everyday()
        elif task == "jobs":
            collect_job_requirements_daily()
        elif task == "all":
            run_daily_tasks()
        else:
            logger.error(f"未知任务: {task}")
    else:
        # 默认运行概念更新（向后兼容）
        update_concept_collection_everyday()

