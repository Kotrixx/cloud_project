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

    cpu_usage = ssh_execute_command(hostname, username, password,
                                    "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")  # Obtener el % de uso de CPU
    ram_usage = ssh_execute_command(hostname, username, password,
                                    "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")  # % de RAM utilizada

    disk_info = ssh_execute_command(hostname, username, password,
                                    "df -h --output=source,size,used,avail | grep '^/dev'")

    # Obtenemos la capacidad de red
    net_speed = ssh_execute_command(hostname, username, password,
                                    "ethtool $(ip route get 1 | awk '{print $5}') | grep Speed | awk '{print $2}'")

    return {
        "hostname": hostname,
        "cpu": {
            "model": cpu_info,
            "cores": cpu_cores,
            "architecture": arch,
            "usage_percent": cpu_usage
        },
        "ram": {
            "total": ram_total,
            "used": ram_used,
            "used_percent": ram_usage
        },
        "disk": disk_info,
        "network": {
            "speed": net_speed
        }
    }


def print_worker_info(worker_info):
    print(f"--- Información del worker {worker_info['hostname']} ---")
    print(f"CPU: {worker_info['cpu']['model']}")
    print(f"Núcleos: {worker_info['cpu']['cores']}")
    print(f"Arquitectura: {worker_info['cpu']['architecture']}")
    print(f"Uso de CPU: {worker_info['cpu']['usage_percent']}%")
    print(f"RAM Total: {worker_info['ram']['total']}")
    print(f"RAM Usada: {worker_info['ram']['used']} ({worker_info['ram']['used_percent']}%)")
    print(f"Capacidad de Red: {worker_info['network']['speed']}")
    print("Disco:")
    print(worker_info['disk'])
    print("\n")


def evaluate_worker(worker_info):
    # Definimos los umbrales para la evaluación
    cpu_usage_threshold = 80  # Porcentaje máximo de uso de CPU
    ram_usage_threshold = 80  # Porcentaje máximo de uso de RAM

    cpu_usage = float(worker_info['cpu']['usage_percent'])
    ram_usage = float(worker_info['ram']['used_percent'])

    if cpu_usage < cpu_usage_threshold and ram_usage < ram_usage_threshold:
        return "El worker soporta la topología virtualizada"
    else:
        return "El worker NO soporta la topología virtualizada"


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
    evaluation = evaluate_worker(info)  # Evaluar si el worker soportará la topología
    info['evaluation'] = evaluation  # Agregar el resultado de la evaluación al worker
    workers_info.append(info)

# Generar los reportes
generate_reports(workers_info)
