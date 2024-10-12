import asyncio
from datetime import datetime

import httpx
import paramiko
import time

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.api_app.models.database import init_db
from app.api_app.models.schemas import WorkerUsageOutput


# Función para ejecutar comandos SSH en un worker
def ssh_execute_command(hostname, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output


# Función para parsear el uso de disco en una lista de diccionarios
def parse_disk_usage(output):
    """
    Convierte la salida de df -h en una lista de diccionarios con detalles de cada volumen de disco.
    """
    lines = output.strip().split("\n")
    disk_info = []

    for line in lines:
        parts = line.split()
        if len(parts) == 4:  # Aseguramos que la línea tenga todos los campos
            volume_info = {
                'volume': parts[0],        # El nombre del dispositivo
                'size': parts[1],          # Tamaño total
                'used': parts[2],          # Espacio utilizado
                'available': parts[3],     # Espacio disponible
            }
            disk_info.append(volume_info)

    return disk_info


# Funciones para obtener el uso de CPU, RAM y Disco desde el worker
def get_cpu_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")


def get_ram_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")


def get_disk_usage(hostname, username, password):
    output = ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")
    return parse_disk_usage(output)


async def create_monitoring_record(api_url, worker_id: ObjectId, cpu_usage: str, ram_usage: str, disk_usage: list):
    usage = WorkerUsageOutput(
        worker_id=str(worker_id),
        cpu_usage=float(cpu_usage),
        ram_usage=float(ram_usage),
        disk_usage=disk_usage,  # Lista de diccionarios de la función parse_disk_usage
        timestamp=datetime.utcnow()
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{api_url}/monitoring", json=usage.dict())  # Convertimos a dict para enviar el JSON
        if response.status_code == 200:
            print(f"Registro de monitoreo creado correctamente para {worker_id}")
        else:
            print(f"Error al crear el registro de monitoreo: {response.text}")


# Lógica principal de la aplicación
async def main():
    # api_url = "http://localhost:8080/linux_cluster"
    api_url = "http://central_api:8080/linux_cluster"

    # Obtener los trabajadores desde la API
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/workers")
        workers = response.json()
    print(workers)
    for worker in workers:
        print(f'Monitoreando el worker: {worker["hostname"]} ({worker["ip"]})')

        username = worker["hostname"]
        password = worker["password_hashed"]

        cpu_usage = get_cpu_usage(worker["ip"], username, password)
        ram_usage = get_ram_usage(worker["ip"], username, password)
        disk_usage = get_disk_usage(worker["ip"], username, password)

        await create_monitoring_record(api_url, worker["_id"], cpu_usage, ram_usage, disk_usage)


if __name__ == '__main__':
    asyncio.run(main())
