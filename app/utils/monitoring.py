# utils/monitoring.py
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
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output


def get_cpu_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")


def get_ram_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")


def get_disk_usage(hostname, username, password):
    output = ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")
    return parse_disk_usage(output)
