from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.database.models import Worker, WorkerUsage  # Importa tus modelos
import os
import asyncio

MONGO_URL = (f"mongodb+srv://aingetk_user:aingetk_user"
             f"@cluster0.ek0es.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")


# Inicialización de la base de datos con Beanie y Motor
async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)  # Crear un cliente asíncrono de Motor
    db = client["cloud_test"]  # Seleccionar la base de datos, ajusta el nombre según tu configuración
    return db
