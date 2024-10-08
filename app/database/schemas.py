from pydantic import BaseModel
from datetime import datetime
from typing import List, Union


# Definir schemas basados en los modelos

class WorkerCreationInput(BaseModel):
    name: str
    hostname: str
    ip: str
    password_hashed: str


class WorkerUsageInput(BaseModel):
    worker_id: str  # Aquí también puedes usar ObjectId si fuera necesario
    cpu_usage: float
    ram_usage: float
    disk_usage: str
    timestamp: datetime


# Para posibles respuestas o outputs
class WorkerOutput(BaseModel):
    name: str
    hostname: str
    ip: str

    class Config:
        orm_mode = True


class WorkerUsageOutput(BaseModel):
    worker_id: str
    cpu_usage: float
    ram_usage: float
    disk_usage: str
    timestamp: datetime

    class Config:
        orm_mode = True
