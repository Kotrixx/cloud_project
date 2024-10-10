from typing import Union, Dict, List
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
        name = "workers"  # Corregido el nombre para consistencia plural


class WorkerUsage(Document):
    worker_id: str = Field(...)
    cpu_usage: float = Field(...)
    ram_usage: float = Field(...)
    disk_usage: str = Field(...)
    timestamp: datetime = Field(...)

    class Settings:
        collection = "worker_usages"  # Corregido el nombre para consistencia plural
        # Índices o configuraciones adicionales pueden ser añadidas aquí


class Topology(Document):
    name: str = Field(..., description="The name of the topology")
    nodes: int = Field(..., description="The number of nodes in the topology")
    topology_name: str = Field(..., description="The general name of the network topology")
    vlan_tags: dict = Field(..., description="VLAN tags for each veth interface")
    dnsmasq_configs: dict = Field(..., description="DHCP configurations for each namespace")
    gateway_ips: dict = Field(..., description="Gateway IPs assigned to each subinterface")
    subinterfaces: dict = Field(..., description="Subinterfaces with associated VLAN IDs")
    veth_pairs: list = Field(..., description="Veth pairs connecting OVS to namespaces")
    namespaces: list = Field(..., description="List of namespaces for the topology")
    creation_timestamp: datetime = Field(..., description="Timestamp when the topology was created")
    topology_type: str = Field(..., description="The type of the topology, e.g., ring, star, etc.")

    class Settings:
        collection = "topologies"
        name = "topologies"
