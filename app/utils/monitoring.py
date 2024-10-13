import paramiko

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


def ssh_execute_command(hostname, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, port=5800)
    print(f"Conexión establecida con el worker {hostname}")

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output


def get_cpu_usage(hostname, username, password):
    # Uso de CPU
    return ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")


def get_ram_usage(hostname, username, password):
    # Porcentaje de uso de RAM
    return ssh_execute_command(hostname, username, password, "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")


def get_ram_info(hostname, username, password):
    # Información de la RAM en gigabytes (total y disponible)
    output = ssh_execute_command(hostname, username, password, "free -g | grep Mem")
    parts = output.split()
    ram_info = {
        'total_gb': parts[1],        # Total de RAM en GB
        'used_gb': parts[2],         # RAM usada en GB
        'available_gb': parts[6]     # RAM disponible en GB
    }
    return ram_info


def get_cpu_cores_info(hostname, username, password):
    # Obtener número total de núcleos y núcleos disponibles (idle)
    total_cores = ssh_execute_command(hostname, username, password, "nproc --all")
    available_cores = ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk -F',' '{print $4}' | awk '{print $1}'")

    try:
        cpu_info = {
            'total_cores': int(total_cores),           # Total de núcleos del sistema
            'idle_cores_percentage': float(available_cores)  # Porcentaje de núcleos inactivos
        }
    except ValueError as e:
        raise ValueError(f"Error al convertir valores de CPU: {str(e)}")

    return cpu_info



def get_disk_usage(hostname, username, password):
    output = ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")
    return parse_disk_usage(output)


# Ejemplo de uso
if __name__ == "__main__":
    hostname = "10.0.0.30"
    username = "ubuntu"
    password = "tu_contraseña"

    # Obtener la información de uso de CPU, RAM y discos
    cpu_usage = get_cpu_usage(hostname, username, password)
    ram_usage_percentage = get_ram_usage(hostname, username, password)
    ram_info = get_ram_info(hostname, username, password)
    cpu_cores_info = get_cpu_cores_info(hostname, username, password)
    disk_usage = get_disk_usage(hostname, username, password)

    print(f"Uso de CPU: {cpu_usage}%")
    print(f"Porcentaje de RAM utilizada: {ram_usage_percentage}%")
    print(f"Total RAM: {ram_info['total_gb']} GB, RAM Disponible: {ram_info['available_gb']} GB")
    print(f"Núcleos totales: {cpu_cores_info['total_cores']}, Porcentaje de núcleos inactivos: {cpu_cores_info['idle_cores_percentage']}%")
    print(f"Uso de discos: {disk_usage}")
