from typing import Union
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime

# Definir los modelos con la estructura corregida


class Worker(Document):
    name: str = Field(...)
    hostname: str = Field(...)
    ip: str = Field(...)
    password_hashed: str = Field(...)

    class Settings:
        collection = "workers"  # Corregido el nombre para consistencia plural
        # Puedes agregar índices o configuraciones adicionales aquí si es necesario


class WorkerUsage(Document):
    worker_id: str = Field(...)
    cpu_usage: float = Field(...)
    ram_usage: float = Field(...)
    disk_usage: str = Field(...)
    timestamp: datetime = Field(...)

    class Settings:
        collection = "worker_usages"  # Corregido el nombre para consistencia plural
        # Índices o configuraciones adicionales pueden ser añadidas aquí
