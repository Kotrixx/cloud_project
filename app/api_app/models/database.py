from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.api_app.models.models import Worker, WorkerUsage, Topology

MONGO_URL = (f"mongodb+srv://cloud_user:cloud_pass"
             f"@cluster0.ek0es.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")


async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["cloud_test"]
    collection_names = await db.list_collection_names()
    print(collection_names)
    """collection_names = await db.list_collection_names(filter={"name": "DeviceData"})
    if "DeviceData" not in collection_names:
        await db.command({
            "create": "DeviceData",
            "timeseries": {
                "timeField": "timestamp",
                "metaField": "metadata",
                "granularity": "seconds"
            }
        })"""

    await init_beanie(database=db, document_models=[Worker, WorkerUsage, Topology])
