from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from models import *


MONGO_URL = (f"mongodb+srv://cloud_user:cloud_pass"
             f"@cluster0.ek0es.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = "cloud_test"


async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    # collection_names = await db.list_collection_names()
    # print(collection_names)
    print(User.find_all().to_list())
    await init_beanie(database=db, document_models=[User, ActivityLog, Incident, Role, Resource, Permission])
