from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator

from app.api_app.middleware.logging_middleware import request_logger
from app.api_app.models.database import init_db
from app.api_app.routes.device import device_api as device_routes
from app.api_app.routes.linux_cluster import linux_cluster_api as linux_cluster_routes


async def app_lifespan(app: FastAPI) -> AsyncGenerator:
    await init_db()
    yield


api_app = FastAPI(lifespan=app_lifespan)

# Configurar CORS directamente después de crear la instancia de FastAPI
origins = [
    "http://localhost",
    "http://localhost:5000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "https://test-hosting-map.web.app"

]

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def config():
    # api_app.include_router(device_routes.router)
    api_app.include_router(linux_cluster_routes.router)



config()

# Configurar middleware para logging
api_app.middleware("http")(request_logger)


@api_app.get("/", response_model=dict)
async def index():
    return {"message": "Welcome to the API"}
