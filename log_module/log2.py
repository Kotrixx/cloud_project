import paramiko
import json
import pandas as pd


def ssh_execute_command(hostname, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output


def get_worker_info(hostname, username, password):
    cpu_info = ssh_execute_command(hostname, username, password,
                                   "lscpu | grep 'Model name' | awk -F: '{print $2}' | xargs")
    cpu_cores = ssh_execute_command(hostname, username, password,
                                    "lscpu | grep '^CPU(s):' | awk -F: '{print $2}' | xargs")
    arch = ssh_execute_command(hostname, username, password,
                               "lscpu | grep 'Architecture' | awk -F: '{print $2}' | xargs")

    ram_total = ssh_execute_command(hostname, username, password, "free -h | grep Mem | awk '{print $2}'")
    ram_used = ssh_execute_command(hostname, username, password, "free -h | grep Mem | awk '{print $3}'")

    disk_info = ssh_execute_command(hostname, username, password,
                                    "df -h --output=source,size,used,avail | grep '^/dev'")

    return {
        "hostname": hostname,
        "cpu": {
            "model": cpu_info,
            "cores": cpu_cores,
            "architecture": arch
        },
        "ram": {
            "total": ram_total,
            "used": ram_used
        },
        "disk": disk_info
    }


def print_worker_info(worker_info):
    print(f"--- Información del worker {worker_info['hostname']} ---")
    print(f"CPU: {worker_info['cpu']['model']}")
    print(f"Núcleos: {worker_info['cpu']['cores']}")
    print(f"Arquitectura: {worker_info['cpu']['architecture']}")
    print(f"RAM Total: {worker_info['ram']['total']}")
    print(f"RAM Usada: {worker_info['ram']['used']}")
    print("Disco:")
    print(worker_info['disk'])
    print("\n")


def generate_reports(workers_info):
    # Guardar como JSON
    with open("workers_report.json", "w") as json_file:
        json.dump(workers_info, json_file, indent=4)

    # Crear un DataFrame para exportar a Excel
    df = pd.DataFrame(workers_info)
    df.to_excel("workers_report.xlsx", index=False)
    print("Reportes generados: workers_report.json y workers_report.xlsx")


# Lista de workers con sus credenciales
workers = [
    {"hostname": "10.0.0.30", "username": "ubuntu", "password": "ubuntu"},
    {"hostname": "10.0.0.40", "username": "ubuntu", "password": "ubuntu"},
    {"hostname": "10.0.0.50", "username": "ubuntu", "password": "ubuntu"}
    # Agrega más workers según sea necesario
]

# Obtener información de todos los workers
workers_info = []
for worker in workers:
    info = get_worker_info(worker['hostname'], worker['username'], worker['password'])
    print_worker_info(info)  # Imprimir la información en consola
    workers_info.append(info)

# Generar los reportes
generate_reports(workers_info)
