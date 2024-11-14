import uvicorn

from app.db.milvus import init_milvus_collection, init_milvus_db
from app.model.concept import ConceptSchema
from config import config, PLog

PLog()


def init_milvus():
    client = init_milvus_db()
    init_milvus_collection(client, config.milvus_collection, ConceptSchema)


if __name__ == '__main__':

    init_milvus()
    uvicorn.run(
        app="app:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        reload=config.reload
    )
