# ESTE SCRIPT LIMPIA OVS, Interfaces (incluidas LAS VETH), procesos dnsmasq, procesos qemu Y Namespaces
import subprocess


# Función para ejecutar comandos con sudo
def ejecutar_comando_sudo(comando):
    comando_con_sudo = f"echo 'ubuntu' | sudo -S {comando}"
    proceso = subprocess.Popen(comando_con_sudo, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    salida, error = proceso.communicate()
    if salida:
        print(salida)
    if error:
        print(f"Error: {error}")


# Función para limpiar subinterfaces VLAN
def limpiar_subinterfaces_vlan():
    subinterfaces_vlan = ['br-int.100', 'br-int.200', 'br-int.300']
    for subinterface in subinterfaces_vlan:
        ejecutar_comando_sudo(f'ip link delete {subinterface}')
        print(f'Eliminada subinterface VLAN: {subinterface}')


# Función para eliminar ambos extremos de los pares veth
def limpiar_interfaces_veth():
    resultado = subprocess.run("ip -br addr", shell=True, capture_output=True, text=True)
    interfaces = resultado.stdout.splitlines()

    for linea in interfaces:
        interfaz = linea.split()[0]
        if interfaz not in ['lo', 'ens3', 'ens4', 'ens5']:
            ejecutar_comando_sudo(f'ip link delete {interfaz}')
            print(f'Eliminada interfaz: {interfaz}')


# Función para limpiar OVS, asegurando que no existan puertos asociados
def limpiar_ovs():
    resultado = subprocess.run("ovs-vsctl show", shell=True, capture_output=True, text=True)
    ovs_list = resultado.stdout.splitlines()

    # Remover puertos del OVS antes de eliminar el puente
    for linea in ovs_list:
        if "Bridge" in linea:
            nombre_ovs = linea.split()[1]
            # Listar puertos asociados al bridge y eliminarlos
            ejecutar_comando_sudo(f'ovs-vsctl list-ports {nombre_ovs}')
            ejecutar_comando_sudo(f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs100')
            ejecutar_comando_sudo(f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs200')
            ejecutar_comando_sudo(f'ovs-vsctl --if-exists del-port {nombre_ovs} veth-ovs300')
            ejecutar_comando_sudo(f'ovs-vsctl --if-exists del-port {nombre_ovs} ens5')
            ejecutar_comando_sudo(f'ovs-vsctl del-br {nombre_ovs}')
            print(f'Eliminado OVS: {nombre_ovs}')


# Función para limpiar procesos de dnsmasq
def limpiar_procesos_dnsmasq(proceso_dnsmasq_exento):
    resultado = subprocess.run("ps -ef | grep dnsmasq", shell=True, capture_output=True, text=True)
    procesos = resultado.stdout.splitlines()

    for linea in procesos:
        if proceso_dnsmasq_exento not in linea and "grep" not in linea:
            pid = linea.split()[1]
            ejecutar_comando_sudo(f'kill -15 {pid}')
            print(f'Proceso dnsmasq eliminado: {pid}')


# Función para limpiar procesos qemu
def limpiar_procesos_qemu(proceso_qemu_exento):
    resultado = subprocess.run("ps -ef | grep qemu", shell=True, capture_output=True, text=True)
    procesos = resultado.stdout.splitlines()

    for linea in procesos:
        if proceso_qemu_exento not in linea and "grep" not in linea:
            pid = linea.split()[1]
            ejecutar_comando_sudo(f'kill -15 {pid}')
            print(f'Proceso qemu eliminado: {pid}')


# Función para limpiar namespaces
def limpiar_namespaces():
    resultado = subprocess.run("ip netns list", shell=True, capture_output=True, text=True)
    namespaces = resultado.stdout.splitlines()

    for ns in namespaces:
        nombre_ns = ns.split()[0]
        ejecutar_comando_sudo(f'ip netns del {nombre_ns}')
        print(f'Eliminado namespace: {nombre_ns}')


# Función principal para ejecutar la limpieza en el headnode
def limpiar_headnode():
    proceso_dnsmasq_exento = '6631'  # Reemplazar con el proceso dnsmasq a conservar
    proceso_qemu_exento = '6633'  # Reemplazar con el proceso qemu a conservar

    print("Limpieza iniciada en HeadNode")
    limpiar_subinterfaces_vlan()  # Limpiar las subinterfaces VLAN
    limpiar_interfaces_veth()  # Limpiar interfaces veth
    limpiar_procesos_dnsmasq(proceso_dnsmasq_exento)
    limpiar_procesos_qemu(proceso_qemu_exento)
    limpiar_namespaces()
    limpiar_ovs()  # Limpiar el OVS al final para asegurarse de que todo fue eliminado
    print("Limpieza completa en HeadNode")


# Ejecutar la limpieza
limpiar_headnode()
