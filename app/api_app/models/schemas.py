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


class WorkerUsageOutput(BaseModel):
    worker_id: str
    cpu_usage: float
    ram_usage: float
    disk_usage: list
    timestamp: datetime


class RingTopologyInput(BaseModel):
    name: str
    nodes: int
    topology_name: str
    vlan_tags: dict
    dnsmasq_configs: dict
    gateway_ips: dict
    subinterfaces: dict
    veth_pairs: list
    namespaces: list
    creation_timestamp: str
