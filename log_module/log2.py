import paramiko
import json
import pandas as pd
import threading
import time

# Función para ejecutar comandos SSH en cada worker
def ssh_execute_command(hostname, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output

# Funciones individuales para obtener CPU, RAM, disco y red
def get_cpu_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")

def get_ram_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")

def get_disk_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")

def get_network_speed(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "ethtool $(ip route get 1 | awk '{print $5}') | grep Speed | awk '{print $2}'")

# Función para monitorear constantemente un worker en un hilo separado
def monitor_worker(hostname, username, password, monitor_interval=10):
    while True:
        cpu_usage = get_cpu_usage(hostname, username, password)
        ram_usage = get_ram_usage(hostname, username, password)
        disk_usage = get_disk_usage(hostname, username, password)
        net_speed = get_network_speed(hostname, username, password)

        print(f"--- Monitoreo del worker {hostname} ---")
        print(f"Uso de CPU: {cpu_usage}%")
        print(f"Uso de RAM: {ram_usage}%")
        print("Uso de Disco:")
        print(disk_usage)
        print(f"Velocidad de red: {net_speed}")
        print("\n")

        # Evaluar si el worker soportará una nueva máquina virtual (ajustar los umbrales si es necesario)
        if float(cpu_usage) < 90 and float(ram_usage) < 90:
            print(f"El worker {hostname} soporta una nueva máquina virtual.")
        else:
            print(f"El worker {hostname} NO soporta una nueva máquina virtual en este momento.")

        # Esperar antes de la siguiente evaluación
        time.sleep(monitor_interval)

# Función para iniciar el monitoreo de todos los workers usando hilos
def start_monitoring(workers):
    threads = []
    for worker in workers:
        thread = threading.Thread(target=monitor_worker, args=(worker['hostname'], worker['username'], worker['password']))
        thread.start()
        threads.append(thread)

    # Esperar a que todos los hilos terminen (opcional)
    for thread in threads:
        thread.join()

# Lista de workers con sus credenciales
workers = [
    {"hostname": "10.0.0.30", "username": "ubuntu", "password": "ubuntu"},
    {"hostname": "10.0.0.40", "username": "ubuntu", "password": "ubuntu"},
    {"hostname": "10.0.0.50", "username": "ubuntu", "password": "ubuntu"}
    # Agrega más workers según sea necesario
]

# Iniciar el monitoreo en hilos para cada worker
start_monitoring(workers)
