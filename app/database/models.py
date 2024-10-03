from beanie import Document
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient


# Definir los modelos usando Beanie
class Worker(Document):
    name: str
    hostname: str
    ip: str
    password_hashed: str
    class Settings:
        collection = "worker"


class WorkerUsage(Document):
    worker_id: str  # Puedes usar un campo ObjectId si lo prefieres
    cpu_usage: float
    ram_usage: float
    disk_usage: str
    timestamp: str

    class Settings:
        collection = "worker_usage"
