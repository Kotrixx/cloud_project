import paramiko


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


# Función para limpiar interfaces
def limpiar_interfaces(cliente):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ip -br addr')
    interfaces = stdout.read().decode().splitlines()

    for linea in interfaces:
        interfaz = linea.split()[0]
        if interfaz not in ['lo', 'ens3', 'ens4']:
            ejecutar_comando_sudo(cliente, f'ip link delete {interfaz}')
            print(f'Eliminada interfaz: {interfaz}')


# Función para limpiar procesos de VMs
def limpiar_procesos(cliente, proceso_qemu_exento):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ps -ef | grep qemu')
    procesos = stdout.read().decode().splitlines()

    for linea in procesos:
        if proceso_qemu_exento not in linea and "grep" not in linea:
            pid = linea.split()[1]
            ejecutar_comando_sudo(cliente, f'kill -15 {pid}')
            print(f'Proceso eliminado: {pid}')


# Función para limpiar namespaces
def limpiar_namespaces(cliente):
    stdout, stderr = ejecutar_comando_sudo(cliente, 'ip netns list')
    namespaces = stdout.read().decode().splitlines()

    for ns in namespaces:
        nombre_ns = ns.split()[0]
        ejecutar_comando_sudo(cliente, f'ip netns del {nombre_ns}')
        print(f'Eliminado namespace: {nombre_ns}')


# Función principal para seleccionar worker y ejecutar limpieza
def limpiar_worker(worker):
    if worker == '1':
        ip = '10.0.0.30'
        proceso_qemu_exento = '6942'  # Aquí debe ir el proceso a conservar para Worker 1
    elif worker == '2':
        ip = '10.0.0.40'
        proceso_qemu_exento = '5948'  # Aquí debe ir el proceso a conservar para Worker 2
    elif worker == '3':
        ip = '10.0.0.50'
        proceso_qemu_exento = '5875'  # Aquí debe ir el proceso a conservar para Worker 3
    else:
        print("Worker no válido")
        return

    usuario = 'ubuntu'
    contrasena = 'ubuntu'

    cliente = conectar_worker(ip, usuario, contrasena)

    print(f"Limpieza iniciada en Worker {worker} ({ip})")
    limpiar_ovs(cliente)
    limpiar_interfaces(cliente)
    limpiar_procesos(cliente, proceso_qemu_exento)
    limpiar_namespaces(cliente)

    cliente.close()
    print(f"Limpieza completa en Worker {worker}")


"""
# Main - Selección del Worker
worker_seleccionado = input("Selecciona el Worker a limpiar (1, 2 o 3): ")
limpiar_worker(worker_seleccionado)"""
