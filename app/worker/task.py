import asyncio
import os
import re
import time
from datetime import datetime, timedelta

import paramiko
from celery import Celery
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

BROKER_URL = os.getenv("BROKER_URL")
BACKEND_URL = os.getenv("BACKEND_URL")

app = Celery("tasks", broker=BROKER_URL, backend=BACKEND_URL)

"""
app.conf.beat_schedule = {
    'schedule-query-and-verify': {
        'task': 'app.worker.task.schedule_tasks',
        'schedule': 300.0,  # Cada 5 minutos
    },
}

celery_log = get_task_logger(__name__)

door_threshold = 10 * 60
twelve_sensor_threshold = 30
peru_tz = pytz.timezone('America/Lima')
"""


# Función para conectarse al worker mediante SSH
def conectar_worker(ip, usuario, contrasena):
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(ip, username=usuario, password=contrasena)
    return cliente


# Función para ejecutar un comando con sudo
def ejecutar_comando_sudo(cliente, comando):
    stdin, stdout, stderr = cliente.exec_command(f'echo "ubuntu" | sudo -S {comando}')
    return stdout, stderr


# Función para limpiar OVS
def limpiar_ovs(cliente):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ovs-vsctl show')
    ovs_list = stdout.read().decode().splitlines()

    for linea in ovs_list:
        if "Bridge" in linea:
            nombre_ovs = linea.split()[1]
            ejecutar_comando_sudo(cliente, f'ovs-vsctl del-br {nombre_ovs}')
            print(f'Eliminado OVS: {nombre_ovs}')
            time.sleep(1)  # Esperar 1 segundo entre cada eliminación


# Función para limpiar interfaces
def limpiar_interfaces(cliente):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ip -br addr')
    interfaces = stdout.read().decode().splitlines()

    for linea in interfaces:
        interfaz = linea.split()[0]
        if interfaz not in ['lo', 'ens3', 'ens4']:
            ejecutar_comando_sudo(cliente, f'ip link delete {interfaz}')
            print(f'Eliminada interfaz: {interfaz}')
            time.sleep(1)  # Esperar 1 segundo entre cada eliminación


# Función para limpiar procesos de VMs
def limpiar_procesos(cliente):
    ejecutar_comando_sudo(cliente, 'sudo pkill qemu')  # Matar todos los procesos qemu
    print("Procesos de qemu eliminados")
    time.sleep(1)  # Esperar 1 segundo después de matar procesos


# Función para limpiar namespaces
def limpiar_namespaces(cliente):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ip netns list')
    namespaces = stdout.read().decode().splitlines()

    for ns in namespaces:
        nombre_ns = ns.split()[0]
        ejecutar_comando_sudo(cliente, f'ip netns del {nombre_ns}')
        print(f'Eliminado namespace: {nombre_ns}')
        time.sleep(1)  # Esperar 1 segundo entre cada eliminación


@app.task
def limpiar_worker_task(worker):
    if worker == '1':
        ip = '10.0.0.30'
    elif worker == '2':
        ip = '10.0.0.40'
    elif worker == '3':
        ip = '10.0.0.50'
    else:
        print("Worker no válido")
        return

    usuario = 'ubuntu'
    contrasena = 'ubuntu'

    cliente = conectar_worker(ip, usuario, contrasena)

    print(f"Limpieza iniciada en Worker {worker} ({ip})")
    limpiar_ovs(cliente)
    limpiar_interfaces(cliente)
    limpiar_procesos(cliente)
    limpiar_namespaces(cliente)

    cliente.close()
    print(f"Limpieza completa en Worker {worker}")


if __name__ == "__main__":
    app.start()
