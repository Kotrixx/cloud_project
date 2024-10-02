# utils/monitoring.py
import paramiko


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
    return ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")


def get_network_speed(hostname, username, password):
    # Obtener la interfaz de red principal usando un comando para rutas (ip route)
    interface_command = "ip route get 1 | awk '{print $5}'"

    # Ejecutar el comando para obtener la interfaz de red
    interface = ssh_execute_command(hostname, username, password, interface_command)

    # Ejecutar el comando ethtool para obtener la velocidad de la interfaz de red
    net_speed_command = f"ethtool {interface} | grep 'Speed' | awk '{{print $2}}'"

    # Ejecutar el comando en el worker y obtener la salida
    net_speed = ssh_execute_command(hostname, username, password, net_speed_command)

    return net_speed
