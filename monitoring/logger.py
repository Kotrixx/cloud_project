import asyncio
from datetime import datetime

import paramiko
import time

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.database.database import init_db
from app.database.models import Worker


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


# Función para crear un nuevo registro de monitoreo en MongoDB
async def create_monitoring_record(db, worker_id: ObjectId, cpu_usage: str, ram_usage: str, disk_usage: list):
    usage = {
        "worker_id": worker_id,
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "disk_usage": disk_usage,  # Almacenamos la lista de diccionarios
        "timestamp": datetime.utcnow()  # Genera un timestamp válido en UTC
    }
    await db["worker_usage"].insert_one(usage)


# Lógica principal de la aplicación
async def main():
    # Inicializar la base de datos y obtener la conexión a la base de datos
    db = await init_db()

    # Recuperar todos los workers utilizando Beanie
    workers = await Worker.find().to_list()
    print(f"Trabajadores desde Beanie: {workers}")

    for worker in workers:
        print(f'Monitoreando el worker: {worker.hostname} ({worker.ip})')

        # Usamos la contraseña hasheada directamente del documento Worker
        username = worker.hostname  # Suponiendo que este es el nombre de usuario en los servidores
        password = worker.password_hashed  # La contraseña viene desde el campo password_hashed

        # Obtener los valores de monitoreo reales mediante SSH
        cpu_usage = get_cpu_usage(worker.ip, username, password)
        ram_usage = get_ram_usage(worker.ip, username, password)
        disk_usage = get_disk_usage(worker.ip, username, password)

        print(f"Monitoreo de {worker.hostname} ({worker.ip})")
        print(f"Uso de CPU: {cpu_usage}%")
        print(f"Uso de RAM: {ram_usage}%")
        print(f"Uso de Disco: {disk_usage}")

        # Crear un nuevo registro de monitoreo en MongoDB usando Beanie
        await create_monitoring_record(worker.id, cpu_usage, ram_usage, disk_usage)

if __name__ == '__main__':
    asyncio.run(main())
