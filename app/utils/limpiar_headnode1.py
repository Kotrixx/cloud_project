import paramiko
import time


# Función para ejecutar comandos en el servidor remoto utilizando Paramiko
def ejecutar_comando_sudo(ssh_client, comando, contrasena, descripcion=""):
    if descripcion:
        print(descripcion)
    # Ejecutar el comando con sudo
    comando_con_sudo = f'echo "{contrasena}" | sudo -S {comando}'
    stdin, stdout, stderr = ssh_client.exec_command(comando_con_sudo)
    salida = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if salida:
        print(salida)
    if error:
        print(f"Error: {error}")
    return salida, error


# Función para limpiar subinterfaces VLAN
def limpiar_subinterfaces_vlan(ssh_client, contrasena):
    subinterfaces_vlan = ['br-int.100', 'br-int.200', 'br-int.300']
    for subinterface in subinterfaces_vlan:
        ejecutar_comando_sudo(ssh_client, f'ip link delete {subinterface}', contrasena)
        print(f'Eliminada subinterface VLAN: {subinterface}')
        time.sleep(1)  # Esperar 1 segundo


# Función para eliminar ambos extremos de los pares veth
def limpiar_interfaces_veth(ssh_client, contrasena):
    salida, _ = ejecutar_comando_sudo(ssh_client, "ip -br addr", contrasena)
    interfaces = salida.splitlines()

    for linea in interfaces:
        interfaz = linea.split()[0]
        if interfaz not in ['lo', 'ens3', 'ens4', 'ens5']:
            ejecutar_comando_sudo(ssh_client, f'ip link delete {interfaz}', contrasena)
            print(f'Eliminada interfaz: {interfaz}')
            time.sleep(1)  # Esperar 1 segundo


# Función para limpiar OVS, asegurando que no existan puertos asociados
def limpiar_ovs(ssh_client, contrasena):
    salida, _ = ejecutar_comando_sudo(ssh_client, "ovs-vsctl show", contrasena)
    ovs_list = salida.splitlines()

    # Remover puertos del OVS antes de eliminar el puente
    for linea in ovs_list:
        if "Bridge" in linea:
            nombre_ovs = linea.split()[1]
            # Listar puertos asociados al bridge y eliminarlos
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl list-ports {nombre_ovs}', contrasena)
            time.sleep(1)  # Esperar 1 segundo
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs100', contrasena)
            time.sleep(1)  # Esperar 1 segundo
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs200', contrasena)
            time.sleep(1)  # Esperar 1 segundo
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs300', contrasena)
            time.sleep(1)  # Esperar 1 segundo
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl --if-exists del-port {nombre_ovs} ens5', contrasena)
            time.sleep(1)  # Esperar 1 segundo
            ejecutar_comando_sudo(ssh_client, f'ovs-vsctl del-br {nombre_ovs}', contrasena)
            print(f'Eliminado OVS: {nombre_ovs}')
            time.sleep(1)  # Esperar 1 segundo


# Función para limpiar procesos de dnsmasq
def limpiar_procesos_dnsmasq(ssh_client, contrasena, proceso_dnsmasq_exento):
    salida, _ = ejecutar_comando_sudo(ssh_client, "ps -ef | grep dnsmasq", contrasena)
    procesos = salida.splitlines()

    for linea in procesos:
        if proceso_dnsmasq_exento not in linea and "grep" not in linea:
            pid = linea.split()[1]
            ejecutar_comando_sudo(ssh_client, f'kill -15 {pid}', contrasena)
            print(f'Proceso dnsmasq eliminado: {pid}')
            time.sleep(1)  # Esperar 1 segundo


# Función para limpiar procesos qemu
def limpiar_procesos_qemu(ssh_client, contrasena, proceso_qemu_exento):
    salida, _ = ejecutar_comando_sudo(ssh_client, "ps -ef | grep qemu", contrasena)
    procesos = salida.splitlines()

    for linea in procesos:
        if proceso_qemu_exento not in linea and "grep" not in linea:
            pid = linea.split()[1]
            ejecutar_comando_sudo(ssh_client, f'kill -15 {pid}', contrasena)
            print(f'Proceso qemu eliminado: {pid}')
            time.sleep(1)  # Esperar 1 segundo


# Función para limpiar namespaces
def limpiar_namespaces(ssh_client, contrasena):
    salida, _ = ejecutar_comando_sudo(ssh_client, "ip netns list", contrasena)
    namespaces = salida.splitlines()

    for ns in namespaces:
        nombre_ns = ns.split()[0]
        ejecutar_comando_sudo(ssh_client, f'ip netns del {nombre_ns}', contrasena)
        print(f'Eliminado namespace: {nombre_ns}')
        time.sleep(1)  # Esperar 1 segundo


# Función principal para ejecutar la limpieza en el headnode
def limpiar_headnode(ssh_client, contrasena):
    proceso_dnsmasq_exento = '6631'  # Reemplazar con el proceso dnsmasq a conservar
    proceso_qemu_exento = '6633'  # Reemplazar con el proceso qemu a conservar

    print("Limpieza iniciada en HeadNode")
    limpiar_subinterfaces_vlan(ssh_client, contrasena)  # Limpiar las subinterfaces VLAN
    limpiar_interfaces_veth(ssh_client, contrasena)  # Limpiar interfaces veth
    limpiar_procesos_dnsmasq(ssh_client, contrasena, proceso_dnsmasq_exento)
    limpiar_procesos_qemu(ssh_client, contrasena, proceso_qemu_exento)
    limpiar_namespaces(ssh_client, contrasena)
    limpiar_ovs(ssh_client, contrasena)  # Limpiar el OVS al final para asegurarse de que todo fue eliminado
    print("Limpieza completa en HeadNode")


# Establecer conexión SSH utilizando Paramiko
def conectar_ssh(ip_destino, usuario, contrasena):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip_destino, username=usuario, password=contrasena, port=22)
    return ssh_client


if __name__ == "__main__":
    # Información de conexión
    ip_destino = "10.0.10.2"
    usuario = "ubuntu"

    # Solicitar la contraseña al usuario
    contrasena = "kotrix123"
    # input("Por favor, ingresa la contraseña de sudo: ")

    # Establecer la conexión SSH
    ssh_client = conectar_ssh(ip_destino, usuario, contrasena)

    # Ejecutar la limpieza en el headnode
    limpiar_headnode(ssh_client, contrasena)

    # Cerrar la conexión SSH
    ssh_client.close()
