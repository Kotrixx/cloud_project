import paramiko


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


# Diccionario de configuración para cada worker

#SE LE DEBE DAR 2 ITNERFACES TAP A CADA VM
workers_config = {

    '1': {
        'ip': '10.0.0.30',
        'bridge': 'br-int-w1',
        'interfaces': ['tap-w1-vm1-1', 'tap-w1-vm1-2', 'tap-w1-vm2-1', 'tap-w1-vm2-2'],
        #se crean 2 itnerfaces para CADA UNA DE las 2 vms
        'mac_addresses': ['20:20:36:07:aa:11', '20:20:36:07:aa:12', '20:20:36:07:aa:21', '20:20:36:07:aa:22'],

        'tags': [100, 200, 300]  #VM1 recibe de vlan 1 y vlan 2 VM2 recibe de vlan 2 y vlan 3
    },

    '2': {
        'ip': '10.0.0.40',
        'bridge': 'br-int-w2',
        'interfaces': ['tap-w2-vm3-1', 'tap-w2-vm3-2'],
        'mac_addresses': ['20:20:36:07:aa:31', '20:20:36:07:aa:32'],  #UNA MAC POR INTERFAZ
        'tags': [300, 400]
    },

    '3': {
        'ip': '10.0.0.50',
        'bridge': 'br-int-w3',
        'interfaces': ['tap-w3-vm4-1', 'tap-w3-vm4-2'],
        'mac_addresses': ['20:20:36:07:aa:41', '20:20:36:07:aa:42'],
        'tags': [100, 400]
    }

}


# Función para ejecutar los comandos en el worker
def ejecutar_comandos_worker1(cliente, config):
    comandos = [
        (f"ovs-vsctl add-br {config['bridge']}", f"Creando el bridge OVS {config['bridge']}..."),
        (f"ip link set dev {config['bridge']} up", f"Levantando el bridge {config['bridge']}..."),

        (f"ip tuntap add mode tap name {config['interfaces'][0]}", f"Creando interfaz {config['interfaces'][0]}..."),
        (f"ip tuntap add mode tap name {config['interfaces'][1]}", f"Creando interfaz {config['interfaces'][1]}..."),
        (f"ip tuntap add mode tap name {config['interfaces'][2]}", f"Creando interfaz {config['interfaces'][2]}..."),
        (f"ip tuntap add mode tap name {config['interfaces'][3]}", f"Creando interfaz {config['interfaces'][3]}..."),

        #vm1
        (
        f"qemu-system-x86_64 -enable-kvm -vnc 0.0.0.0:1 -netdev tap,id={config['interfaces'][0]},ifname={config['interfaces'][0]},script=no,downscript=no -device e1000,netdev={config['interfaces'][0]},mac={config['mac_addresses'][0]} -netdev tap,id={config['interfaces'][1]},ifname={config['interfaces'][1]},script=no,downscript=no -device e1000,netdev={config['interfaces'][1]},mac={config['mac_addresses'][1]} -daemonize -snapshot cirros-0.5.1-x86_64-disk.img -cpu host",
        f"Creando VM en {config['interfaces'][0]}..."),

        #vm2
        (
        f"qemu-system-x86_64 -enable-kvm -vnc 0.0.0.0:2 -netdev tap,id={config['interfaces'][2]},ifname={config['interfaces'][2]},script=no,downscript=no -device e1000,netdev={config['interfaces'][2]},mac={config['mac_addresses'][2]} -netdev tap,id={config['interfaces'][3]},ifname={config['interfaces'][3]},script=no,downscript=no -device e1000,netdev={config['interfaces'][3]},mac={config['mac_addresses'][3]} -daemonize -snapshot cirros-0.5.1-x86_64-disk.img -cpu host",
        f"Creando VM en {config['interfaces'][2]}..."),

        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][0]}",
         f"Conectando {config['interfaces'][0]} al bridge..."),
        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][1]}",
         f"Conectando {config['interfaces'][1]} al bridge..."),
        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][2]}",
         f"Conectando {config['interfaces'][2]} al bridge..."),
        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][3]}",
         f"Conectando {config['interfaces'][3]} al bridge..."),

        (f"ovs-vsctl set port {config['interfaces'][0]} tag={config['tags'][0]}",
         f"Asignando tag VLAN {config['tags'][0]} a {config['interfaces'][0]}..."),
        (f"ovs-vsctl set port {config['interfaces'][1]} tag={config['tags'][1]}",
         f"Asignando tag VLAN {config['tags'][1]} a {config['interfaces'][1]}..."),

        (f"ovs-vsctl set port {config['interfaces'][2]} tag={config['tags'][1]}",
         f"Asignando tag VLAN {config['tags'][1]} a {config['interfaces'][1]}..."),
        (f"ovs-vsctl set port {config['interfaces'][3]} tag={config['tags'][2]}",
         f"Asignando tag VLAN {config['tags'][2]} a {config['interfaces'][3]}..."),

        (f"ip link set {config['interfaces'][0]} up", f"Levantando {config['interfaces'][0]}..."),
        (f"ip link set {config['interfaces'][1]} up", f"Levantando {config['interfaces'][1]}..."),
        (f"ip link set {config['interfaces'][2]} up", f"Levantando {config['interfaces'][2]}..."),
        (f"ip link set {config['interfaces'][3]} up", f"Levantando {config['interfaces'][3]}..."),

        (f"ovs-vsctl add-port {config['bridge']} ens4", f"Conectando ens4 al bridge {config['bridge']}..."),
        ("ovs-vsctl set port ens4 trunk=100,200,300,400", "Configurando ens4 como troncal para las VLANs...")
    ]

    for comando, descripcion in comandos:
        ejecutar_comando_sudo(cliente, comando, descripcion)


# Función para ejecutar los comandos en el worker
def ejecutar_comandos_worker2(cliente, config):
    comandos = [
        (f"ovs-vsctl add-br {config['bridge']}", f"Creando el bridge OVS {config['bridge']}..."),
        (f"ip link set dev {config['bridge']} up", f"Levantando el bridge {config['bridge']}..."),

        (f"ip tuntap add mode tap name {config['interfaces'][0]}", f"Creando interfaz {config['interfaces'][0]}..."),
        (f"ip tuntap add mode tap name {config['interfaces'][1]}", f"Creando interfaz {config['interfaces'][1]}..."),

        #vm3
        (
        f"qemu-system-x86_64 -enable-kvm -vnc 0.0.0.0:1 -netdev tap,id={config['interfaces'][0]},ifname={config['interfaces'][0]},script=no,downscript=no -device e1000,netdev={config['interfaces'][0]},mac={config['mac_addresses'][0]} -netdev tap,id={config['interfaces'][1]},ifname={config['interfaces'][1]},script=no,downscript=no -device e1000,netdev={config['interfaces'][1]},mac={config['mac_addresses'][1]} -daemonize -snapshot cirros-0.5.1-x86_64-disk.img -cpu host",
        f"Creando VM en {config['interfaces'][0]}..."),

        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][0]}",
         f"Conectando {config['interfaces'][0]} al bridge..."),
        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][1]}",
         f"Conectando {config['interfaces'][1]} al bridge..."),

        (f"ovs-vsctl set port {config['interfaces'][0]} tag={config['tags'][0]}",
         f"Asignando tag VLAN {config['tags'][0]} a {config['interfaces'][0]}..."),
        (f"ovs-vsctl set port {config['interfaces'][1]} tag={config['tags'][1]}",
         f"Asignando tag VLAN {config['tags'][1]} a {config['interfaces'][1]}..."),

        (f"ip link set {config['interfaces'][0]} up", f"Levantando {config['interfaces'][0]}..."),
        (f"ip link set {config['interfaces'][1]} up", f"Levantando {config['interfaces'][1]}..."),

        (f"ovs-vsctl add-port {config['bridge']} ens4", f"Conectando ens4 al bridge {config['bridge']}..."),
        ("ovs-vsctl set port ens4 trunk=100,200,300,400", "Configurando ens4 como troncal para las VLANs...")
    ]

    for comando, descripcion in comandos:
        ejecutar_comando_sudo(cliente, comando, descripcion)


# Función para ejecutar los comandos en el worker
def ejecutar_comandos_worker3(cliente, config):
    comandos = [
        (f"ovs-vsctl add-br {config['bridge']}", f"Creando el bridge OVS {config['bridge']}..."),
        (f"ip link set dev {config['bridge']} up", f"Levantando el bridge {config['bridge']}..."),

        (f"ip tuntap add mode tap name {config['interfaces'][0]}", f"Creando interfaz {config['interfaces'][0]}..."),
        (f"ip tuntap add mode tap name {config['interfaces'][1]}", f"Creando interfaz {config['interfaces'][1]}..."),

        #vm3
        (
        f"qemu-system-x86_64 -enable-kvm -vnc 0.0.0.0:1 -netdev tap,id={config['interfaces'][0]},ifname={config['interfaces'][0]},script=no,downscript=no -device e1000,netdev={config['interfaces'][0]},mac={config['mac_addresses'][0]} -netdev tap,id={config['interfaces'][1]},ifname={config['interfaces'][1]},script=no,downscript=no -device e1000,netdev={config['interfaces'][1]},mac={config['mac_addresses'][1]} -daemonize -snapshot cirros-0.5.1-x86_64-disk.img -cpu host",
        f"Creando VM en {config['interfaces'][0]}..."),

        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][0]}",
         f"Conectando {config['interfaces'][0]} al bridge..."),
        (f"ovs-vsctl add-port {config['bridge']} {config['interfaces'][1]}",
         f"Conectando {config['interfaces'][1]} al bridge..."),

        (f"ovs-vsctl set port {config['interfaces'][0]} tag={config['tags'][0]}",
         f"Asignando tag VLAN {config['tags'][0]} a {config['interfaces'][0]}..."),
        (f"ovs-vsctl set port {config['interfaces'][1]} tag={config['tags'][1]}",
         f"Asignando tag VLAN {config['tags'][1]} a {config['interfaces'][1]}..."),

        (f"ip link set {config['interfaces'][0]} up", f"Levantando {config['interfaces'][0]}..."),
        (f"ip link set {config['interfaces'][1]} up", f"Levantando {config['interfaces'][1]}..."),

        (f"ovs-vsctl add-port {config['bridge']} ens4", f"Conectando ens4 al bridge {config['bridge']}..."),
        ("ovs-vsctl set port ens4 trunk=100,200,300,400", "Configurando ens4 como troncal para las VLANs...")
    ]

    for comando, descripcion in comandos:
        ejecutar_comando_sudo(cliente, comando, descripcion)


# Función principal para seleccionar worker y ejecutar comandos
def configurar_worker(worker):
    if worker not in workers_config:
        print("Worker no válido")
        return

    config = workers_config[worker]
    ip = config['ip']
    usuario = 'ubuntu'
    contrasena = 'ubuntu'

    print(f"Configuración iniciada en Worker {worker} ({ip})")
    cliente = conectar_worker(ip, usuario, contrasena)

    if int(worker) == 1:
        ejecutar_comandos_worker1(cliente, config)
    if int(worker) == 2:
        ejecutar_comandos_worker2(cliente, config)
    if int(worker) == 3:
        ejecutar_comandos_worker3(cliente, config)

    cliente.close()
    print(f"Configuración completa en Worker {worker}")


# Main - Selección del Worker
if __name__ == "__main__":
    worker_seleccionado = input("Selecciona el Worker a configurar (1, 2 o 3): ")
    configurar_worker(worker_seleccionado)
