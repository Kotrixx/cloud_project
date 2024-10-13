import paramiko
import json


# Función para ejecutar los comandos en el worker
def ejecutar_comandos_worker(cliente, worker_config, vlans):
    bridge = worker_config['bridge']
    vms = worker_config['vms']

    # Crear el bridge y levantarlo
    comandos = [
        (f"ovs-vsctl add-br {bridge}", f"Creando el bridge OVS {bridge}..."),
        (f"ip link set dev {bridge} up", f"Levantando el bridge {bridge}..."),
        # Añadir ens4 como troncal para todas las VLANs
        (f"ovs-vsctl add-port {bridge} ens4", f"Conectando ens4 al bridge {bridge}..."),
        (f"ovs-vsctl set port ens4 trunk={','.join(vlans)}",
         f"Configurando ens4 como troncal para las VLANs {','.join(vlans)}...")

    ]

    # Procesar cada VM
    for vm_name, vm_config in vms.items():
        interfaces = vm_config['interfaces']

        # Crear las interfaces TAP para cada VM y configurarlas
        for interfaz in interfaces:
            tap_name = interfaz['nombre']
            mac_address = interfaz['mac']
            vlan_tag = interfaz['vlan']

            comandos += [
                (f"ip tuntap add mode tap name {tap_name}", f"Creando interfaz {tap_name}..."),
                (f"ip link set {tap_name} up", f"Levantando {tap_name}..."),
                (f"ovs-vsctl add-port {bridge} {tap_name}", f"Conectando {tap_name} al bridge..."),
                (f"ovs-vsctl set port {tap_name} tag={vlan_tag}", f"Asignando tag VLAN {vlan_tag} a {tap_name}..."),
                (f"ip link set {tap_name} address {mac_address}", f"Asignando MAC {mac_address} a {tap_name}..."),
                (f"ovs-vsctl add-port {bridge} ens4", f"Conectando ens4 al bridge {bridge}..."),
                (f"ovs-vsctl set port ens4 trunk={','.join(vlans)}",
                 f"Configurando ens4 como troncal para las VLANs {','.join(vlans)}...")
            ]

        # Crear comando dinámico de QEMU según el número de interfaces
        comando_qemu = f"qemu-system-x86_64 -enable-kvm -vnc 0.0.0.0:{vm_name[-1]} "  # Usa el número de VM para VNC
        for i, interfaz in enumerate(interfaces):
            tap_name = interfaz['nombre']
            mac_address = interfaz['mac']
            comando_qemu += f"-netdev tap,id={tap_name},ifname={tap_name},script=no,downscript=no -device e1000,netdev={tap_name},mac={mac_address} "

        # Completar comando con opciones adicionales
        comando_qemu += "-daemonize -snapshot cirros-0.5.1-x86_64-disk.img -cpu host"
        comandos.append((comando_qemu, f"Creando VM {vm_name} con {len(interfaces)} interfaces..."))

    # Ejecutar todos los comandos
    for comando, descripcion in comandos:
        ejecutar_comando_sudo(cliente, comando, descripcion)



# Función para conectarse al worker mediante SSH
def conectar_worker(ip, usuario, contrasena):
    print(f"Conectando al worker {ip}...")
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(ip, username=usuario, password=contrasena)
    print(f"Conexión establecida con el worker {ip}")
    return cliente


# Función para ejecutar comandos con sudo y manejar la contraseña
def ejecutar_comando_sudo(cliente, comando, descripcion=""):
    if descripcion:
        print(descripcion)
    comando_con_sudo = f"echo 'ubuntu' | sudo -S {comando}"
    stdin, stdout, stderr = cliente.exec_command(comando_con_sudo)
    salida = stdout.read().decode()
    error = stderr.read().decode()
    if salida:
        print(salida)
    if error:
        print(f"Error: {error}")


# Cargar la configuración JSON
def cargar_configuracion(json_file):
    with open(json_file, 'r') as f:
        config = json.load(f)
    return config


# Función principal para procesar los workers y ejecutar los comandos en cada uno
def procesar_workers(config, usuario, contrasena):
    workers = config['workers']
    vlans = config['vlans'].keys()
    vlan_networks = config['vlans'].values()  # Obtener las redes de las VLANs

    for worker_name, worker_config in workers.items():
        ip = worker_config['ip']
        cliente = conectar_worker(ip, usuario, contrasena)
        ejecutar_comandos_worker(cliente, worker_config, vlans)
        cliente.close()


# Configuración de la ruta del archivo JSON y credenciales SSH
if __name__ == "__main__":
    json_file = "workers_config.json"
    usuario = "ubuntu"
    contrasena = "ubuntu"

    # Cargar la configuración y procesar los workers
    config = cargar_configuracion(json_file)
    procesar_workers(config, usuario, contrasena)
