import subprocess
import json
import ipaddress


# Función para ejecutar comandos con sudo
def ejecutar_comando_sudo(comando, descripcion=""):
    if descripcion:
        print(descripcion)
    comando_con_sudo = f"echo 'ubuntu' | sudo -S {comando}"
    proceso = subprocess.Popen(comando_con_sudo, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    salida, error = proceso.communicate()
    if salida:
        print(salida)
    if error:
        print(f"Error: {error}")


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
def configurar_headnode(config):
    print("Configuración iniciada en HeadNode")

    # Actualizar el sistema
    ejecutar_comando_sudo('apt-get update', "Actualizando el sistema... (esto puede tardar, no detener el programa)")

    # Crear un nuevo OVS llamado br-int
    ejecutar_comando_sudo('ovs-vsctl add-br br-int', "Creando el bridge OVS br-int...")
    ejecutar_comando_sudo('ip link set dev br-int up', "Levantando el bridge br-int...")

    # Prender interfaz ens5 y agregarla al OVS
    ejecutar_comando_sudo('ip link set ens5 up', "Levantando la interfaz ens5...")
    ejecutar_comando_sudo('ovs-vsctl add-port br-int ens5', "Conectando la interfaz ens5 al OVS...")

    # Activar IPv4 Forwarding
    ejecutar_comando_sudo('sysctl -w net.ipv4.ip_forward=1', "Activando IPv4 Forwarding...")

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

        # Crear namespace y levantarlo
        ejecutar_comando_sudo(f'ip netns add {ns}', f"Creando el namespace {ns}...")
        ejecutar_comando_sudo(f'ip netns exec {ns} ip link set dev lo up',
                              f"Levantando la interfaz loopback en {ns}...")

        # Añadir el par de veths
        veth_pairs.append((veth_ovs, veth_ns, ns))

        # Crear subinterface y asignarle la VLAN
        subinterface = f'br-int.{vlan_tag}'
        subinterfaces[subinterface] = vlan_tag

        # Asignar las IPs (primera IP superior es gateway, segunda IP superior es para veth)
        gateway_ip = obtener_ip_superior(red, 1) + '/' + red.split('/')[
            1]  # IP inmediatamente superior a la red es gateway
        veth_ip = obtener_ip_superior(red, 2) + '/' + red.split('/')[1]  # Segunda IP es para veth en el namespace
        gateway_ips[subinterface] = gateway_ip
        veth_ips[ns] = veth_ip

        # Configuración de dnsmasq para cada namespace (IPs en bloques de 4)
        dnsmasq_range_start = obtener_ip_superior(red, 3)  # La tercera IP superior
        dnsmasq_range_end = obtener_ip_superior(red, 6)  # Usar las siguientes 4 direcciones
        dnsmasq_configs[ns] = (veth_ns, f"{dnsmasq_range_start},{dnsmasq_range_end}", gateway_ip)

        # Asignar tag de VLAN al veth del OVS
        vlan_tags[veth_ovs] = vlan_tag

    # Crear y configurar veth pairs
    for veth_ovs, veth_ns, ns in veth_pairs:
        ejecutar_comando_sudo(f'ip link add {veth_ovs} type veth peer name {veth_ns}',
                              f"Creando el par veth {veth_ovs} y {veth_ns}...")
        ejecutar_comando_sudo(f'ip link set {veth_ns} netns {ns}', f"Moviendo {veth_ns} al namespace {ns}...")
        ejecutar_comando_sudo(f'ovs-vsctl add-port br-int {veth_ovs}', f"Añadiendo {veth_ovs} al OVS br-int...")
        ejecutar_comando_sudo(f'ip link set {veth_ovs} up', f"Levantando {veth_ovs}...")
        ejecutar_comando_sudo(f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Levantando {veth_ns} en {ns}...")

    # Crear subinterfaces en br-int y asignar VLANs
    for subinterface, vlan in subinterfaces.items():
        ejecutar_comando_sudo(f'ip link add link br-int name {subinterface} type vlan id {vlan}',
                              f"Creando subinterface {subinterface} con VLAN {vlan}...")
        ejecutar_comando_sudo(f'ip link set dev {subinterface} up', f"Levantando la subinterface {subinterface}...")

    # Asignar IPs a las subinterfaces para que actúen como gateways
    for subinterface, ip in gateway_ips.items():
        ejecutar_comando_sudo(f'ip address add {ip} dev {subinterface}', f"Asignando IP {ip} a {subinterface}...")

    # Asignar IPs a las interfaces veth del namespace
    for ns, ip in veth_ips.items():
        ejecutar_comando_sudo(f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}',
                              f"Asignando IP {ip} a {ns}...")

    # Ejecutar dnsmasq en cada namespace para proporcionar DHCP
    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        ejecutar_comando_sudo(
            f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},255.255.255.248 --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8',
            f"Configurando dnsmasq en {ns}...")

    # Asignar tag de VLAN a interfaces del peer veth del OVS
    for veth_ovs, vlan in vlan_tags.items():
        ejecutar_comando_sudo(f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Asignando tag VLAN {vlan} a {veth_ovs}...")

    # Definir la interfaz ens5 como troncal para que todas las VLANs puedan llevar y recoger tráfico
    vlan_ids = ",".join([str(vlan) for vlan in vlans.keys()])
    ejecutar_comando_sudo(f'ovs-vsctl set port ens5 trunk={vlan_ids}',
                          f"Configurando ens5 como troncal para las VLANs {vlan_ids}...")

    # Natear las redes definidas en el archivo JSON
    for red in vlans.values():
        ejecutar_comando_sudo(f'iptables -t nat -I POSTROUTING -s {red} -o ens3 -j MASQUERADE',
                              f"Aplicando regla NAT para {red}...")

    print("Configuración completa en HeadNode")


# Cargar el archivo de configuración y ejecutar la configuración
if __name__ == "__main__":
    json_file = "workers_config.json"
    config = cargar_configuracion(json_file)
    configurar_headnode(config)
