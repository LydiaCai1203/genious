
import time
from datetime import datetime

from tqdm import tqdm

from app.model.concept import ConceptSchema
from app.db.milvus import init_milvus_db, init_milvus_collection
from app.service.concept import get_concept_stocks
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


if __name__ == "__main__":
    init_milvus()
    update_concept_collection_everyday()
    # update_concept_collection()

