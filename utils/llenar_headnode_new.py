import paramiko
from itertools import product
import json

# Función para ejecutar comandos vía SSH utilizando Paramiko
def ejecutar_comando_ssh(ssh_client, comando, descripcion="", contrasena=None):
    if descripcion:
        print(descripcion)
    if contrasena:
        comando = f'echo "{contrasena}" | sudo -S {comando}'
    stdin, stdout, stderr = ssh_client.exec_command(comando)
    salida = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if salida:
        print(salida)
    if error:
        print(f"Error: {error}")
    return salida, error


# Generar reglas de iptables a partir de una lista de subredes
def generar_reglas_iptables(subredes):
    reglas = []
    # Crear reglas para cada combinación de subredes
    for src, dst in product(subredes, repeat=2):
        regla = f"iptables -A FORWARD -s {src} -d {dst} -j ACCEPT"
        reglas.append(regla)
    # Agregar reglas adicionales
    reglas.append("iptables -A FORWARD -j ACCEPT")
    reglas.append("iptables -A FORWARD -o ens3 -j ACCEPT")
    reglas.append("iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT")

    return reglas


# Ejecutar todas las reglas en el servidor remoto
def ejecutar_reglas_iptables(ssh_client, reglas, contrasena=None):
    for regla in reglas:
        ejecutar_comando_ssh(ssh_client, regla, f"Ejecutando {regla}...", contrasena)


# Extraer subredes de las interfaces en el archivo JSON
def extraer_subredes(json_data):
    subredes = set()  # Usamos un conjunto para evitar duplicados
    workers = json_data["workers"]

    # Recorrer cada worker y sus máquinas virtuales para obtener las subredes
    for worker in workers.values():
        for vm in worker["vms"].values():
            for interfaz in vm["interfaces"]:
                subredes.add(interfaz["red"])

    return list(subredes)  # Convertimos el conjunto en lista para trabajar con él


# Función principal para configurar las reglas de iptables
def configurar_iptables(json_file, usuario, contrasena, ip_destino):
    # Cargar el archivo JSON
    with open(json_file, 'r') as f:
        json_data = json.load(f)

    # Extraer las subredes del JSON
    subredes = extraer_subredes(json_data)

    # Generar las reglas de iptables
    reglas = generar_reglas_iptables(subredes)

    # Establecer conexión SSH utilizando Paramiko
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip_destino, username=usuario, password=contrasena, port=22)

    # Ejecutar las reglas en el servidor remoto
    ejecutar_reglas_iptables(ssh_client, reglas, contrasena)

    # Cerrar la conexión SSH
    ssh_client.close()


# Ejemplo de uso
if __name__ == "__main__":
    json_file = "workers_config.json"  # Nombre del archivo JSON con la configuración
    usuario = "tu_usuario"
    contrasena = "tu_contraseña"
    ip_destino = "10.20.12.238"  # IP del servidor al que conectarse

    configurar_iptables(json_file, usuario, contrasena, ip_destino)
