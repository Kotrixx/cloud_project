import paramiko
import json
import ipaddress


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


# Cargar la configuración JSON
def cargar_configuracion(json_file):
    with open(json_file, 'r') as f:
        config = json.load(f)
    return config


# Función para obtener la IP inmediata superior en una subred
def obtener_ip_superior(subred, offset):
    network = ipaddress.ip_network(subred, strict=False)
    return str(network.network_address + offset)


# Función principal para configurar el HeadNode de forma dinámica
def configurar_headnode(config, usuario, contrasena, ip_destino):
    print("Configuración iniciada en HeadNode")

    # Establecer conexión SSH utilizando Paramiko en el puerto 22
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip_destino, username=usuario, password=contrasena, port=22)

    # Actualizar el sistema con sudo
    ejecutar_comando_ssh(ssh_client, 'apt-get update', "Actualizando el sistema... (esto puede tardar, no detener el programa)", contrasena)

    # Crear un nuevo OVS llamado br-int con sudo
    ejecutar_comando_ssh(ssh_client, 'ovs-vsctl add-br br-int', "Creando el bridge OVS br-int...", contrasena)
    ejecutar_comando_ssh(ssh_client, 'ip link set dev br-int up', "Levantando el bridge br-int...", contrasena)

    # Prender interfaz ens5 y agregarla al OVS con sudo
    ejecutar_comando_ssh(ssh_client, 'ip link set ens5 up', "Levantando la interfaz ens5...", contrasena)
    ejecutar_comando_ssh(ssh_client, 'ovs-vsctl add-port br-int ens5', "Conectando la interfaz ens5 al OVS...", contrasena)

    # Activar IPv4 Forwarding con sudo
    ejecutar_comando_ssh(ssh_client, 'sysctl -w net.ipv4.ip_forward=1', "Activando IPv4 Forwarding...", contrasena)

    # Procesar cada VLAN
    vlans = config['vlans']
    veth_pairs = []
    subinterfaces = {}
    gateway_ips = {}
    veth_ips = {}
    dnsmasq_configs = {}
    vlan_tags = {}

    for vlan_tag, red in vlans.items():
        ns = f'ns-vlan{vlan_tag}'
        veth_ovs = f'veth-ovs{vlan_tag}'
        veth_ns = f'veth-ns{vlan_tag}'

        # Crear namespace y levantarlo con sudo
        ejecutar_comando_ssh(ssh_client, f'ip netns add {ns}', f"Creando el namespace {ns}...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ip netns exec {ns} ip link set dev lo up',
                             f"Levantando la interfaz loopback en {ns}...", contrasena)

        # Añadir el par de veths
        veth_pairs.append((veth_ovs, veth_ns, ns))

        # Crear subinterface y asignarle la VLAN
        subinterface = f'br-int.{vlan_tag}'
        subinterfaces[subinterface] = vlan_tag

        # Asignar las IPs (primera IP superior es gateway, segunda IP superior es para veth)
        gateway_ip = obtener_ip_superior(red, 1) + '/' + red.split('/')[1]
        veth_ip = obtener_ip_superior(red, 2) + '/' + red.split('/')[1]
        gateway_ips[subinterface] = gateway_ip
        veth_ips[ns] = veth_ip

        # Configuración de dnsmasq para cada namespace
        dnsmasq_range_start = obtener_ip_superior(red, 3)
        dnsmasq_range_end = obtener_ip_superior(red, 6)
        dnsmasq_configs[ns] = (veth_ns, f"{dnsmasq_range_start},{dnsmasq_range_end}", gateway_ip)

        # Asignar tag de VLAN al veth del OVS
        vlan_tags[veth_ovs] = vlan_tag

    # Crear y configurar veth pairs con sudo
    for veth_ovs, veth_ns, ns in veth_pairs:
        ejecutar_comando_ssh(ssh_client, f'ip link add {veth_ovs} type veth peer name {veth_ns}',
                             f"Creando el par veth {veth_ovs} y {veth_ns}...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ip link set {veth_ns} netns {ns}', f"Moviendo {veth_ns} al namespace {ns}...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ovs-vsctl add-port br-int {veth_ovs}', f"Añadiendo {veth_ovs} al OVS br-int...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ip link set {veth_ovs} up', f"Levantando {veth_ovs}...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Levantando {veth_ns} en {ns}...", contrasena)

    # Crear subinterfaces en br-int y asignar VLANs con sudo
    for subinterface, vlan in subinterfaces.items():
        ejecutar_comando_ssh(ssh_client, f'ip link add link br-int name {subinterface} type vlan id {vlan}',
                             f"Creando subinterface {subinterface} con VLAN {vlan}...", contrasena)
        ejecutar_comando_ssh(ssh_client, f'ip link set dev {subinterface} up', f"Levantando la subinterface {subinterface}...", contrasena)

    # Asignar IPs a las subinterfaces para que actúen como gateways con sudo
    for subinterface, ip in gateway_ips.items():
        ejecutar_comando_ssh(ssh_client, f'ip address add {ip} dev {subinterface}', f"Asignando IP {ip} a {subinterface}...", contrasena)

    # Asignar IPs a las interfaces veth del namespace con sudo
    for ns, ip in veth_ips.items():
        ejecutar_comando_ssh(ssh_client, f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}',
                             f"Asignando IP {ip} a {ns}...", contrasena)

    # Ejecutar dnsmasq en cada namespace para proporcionar DHCP con sudo
    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        ejecutar_comando_ssh(ssh_client,
                             f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},255.255.255.248 --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8',
                             f"Configurando dnsmasq en {ns}...", contrasena)

    # Asignar tag de VLAN a interfaces del peer veth del OVS con sudo
    for veth_ovs, vlan in vlan_tags.items():
        ejecutar_comando_ssh(ssh_client, f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Asignando tag VLAN {vlan} a {veth_ovs}...", contrasena)

    # Definir la interfaz ens5 como troncal para que todas las VLANs puedan llevar y recoger tráfico con sudo
    vlan_ids = ",".join([str(vlan) for vlan in vlans.keys()])
    ejecutar_comando_ssh(ssh_client, f'ovs-vsctl set port ens5 trunk={vlan_ids}',
                         f"Configurando ens5 como troncal para las VLANs {vlan_ids}...", contrasena)

    # Natear las redes definidas en el archivo JSON con sudo
    for red in vlans.values():
        ejecutar_comando_ssh(ssh_client, f'iptables -t nat -I POSTROUTING -s {red} -o ens3 -j MASQUERADE',
                             f"Aplicando regla NAT para {red}...", contrasena)

    print("Configuración completa en HeadNode")

    # Cerrar la conexión SSH
    ssh_client.close()


# Cargar el archivo de configuración y ejecutar la configuración
if __name__ == "__main__":
    json_file = "workers_config.json"
    config = cargar_configuracion(json_file)
    usuario = "tu_usuario"
    contrasena = "tu_contraseña"
    ip_destino = "10.20.12.238"
    configurar_headnode(config, usuario, contrasena, ip_destino)
