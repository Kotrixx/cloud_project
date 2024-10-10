import subprocess

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

# Función principal para configurar el HeadNode
def configurar_headnode():
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

    # Crear namespaces
    namespaces = ['ns-vlan100', 'ns-vlan200', 'ns-vlan300', 'ns-vlan400']

    for ns in namespaces:
        ejecutar_comando_sudo(f'ip netns add {ns}', f"Creando el namespace {ns}...")
        ejecutar_comando_sudo(f'ip netns exec {ns} ip link set dev lo up', f"Levantando la interfaz loopback en {ns}...")




    # Crear y configurar veth pairs
    veth_pairs = [
        ('veth-ovs100', 'veth-ns100', 'ns-vlan100'),
        ('veth-ovs200', 'veth-ns200', 'ns-vlan200'),
        ('veth-ovs300', 'veth-ns300', 'ns-vlan300')
        ('veth-ovs400', 'veth-ns400', 'ns-vlan400')
    ]

    
    for veth_ovs, veth_ns, ns in veth_pairs:
        ejecutar_comando_sudo(f'ip link add {veth_ovs} type veth peer name {veth_ns}', f"Creando el par veth {veth_ovs} y {veth_ns}...")
        ejecutar_comando_sudo(f'ip link set {veth_ns} netns {ns}', f"Moviendo {veth_ns} al namespace {ns}...")
        ejecutar_comando_sudo(f'ovs-vsctl add-port br-int {veth_ovs}', f"Añadiendo {veth_ovs} al OVS br-int...")
        ejecutar_comando_sudo(f'ip link set {veth_ovs} up', f"Levantando {veth_ovs}...")
        ejecutar_comando_sudo(f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Levantando {veth_ns} en {ns}...")



    # Crear subinterfaces en br-int y asignar VLANs
    subinterfaces = {
        'br-int.100': 100,
        'br-int.200': 200,
        'br-int.300': 300,
        'br-int.400': 400
    }



    for subinterface, vlan in subinterfaces.items():
        ejecutar_comando_sudo(f'ip link add link br-int name {subinterface} type vlan id {vlan}', f"Creando subinterface {subinterface} con VLAN {vlan}...")
        ejecutar_comando_sudo(f'ip link set dev {subinterface} up', f"Levantando la subinterface {subinterface}...")

    # Asignar IPs a las subinterfaces para que actúen como gateways
    gateway_ips = {
        'br-int.100': '10.0.50.1/29',
        'br-int.200': '10.0.50.9/29',
        'br-int.300': '10.0.50.17/29',
        'br-int.400': '10.0.50.25/29'
    }
    for subinterface, ip in gateway_ips.items():
        ejecutar_comando_sudo(f'ip address add {ip} dev {subinterface}', f"Asignando IP {ip} a {subinterface}...")




    # Asignar IPs a las interfaces veth del namespace
    veth_ips = {
        'ns-vlan100': '10.0.50.2/29',
        'ns-vlan200': '10.0.50.10/29',
        'ns-vlan300': '10.0.50.18/29',
        'ns-vlan400': '10.0.50.26/29'
    }


    for ns, ip in veth_ips.items():
        ejecutar_comando_sudo(f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}', f"Asignando IP {ip} a {ns}...")

    # Ejecutar dnsmasq en cada namespace para proporcionar DHCP
    dnsmasq_configs = {
        'ns-vlan100': ('veth-ns100', '10.0.50.3,10.0.50.6', '10.0.50.1'),
        'ns-vlan200': ('veth-ns200', '10.0.50.11,10.0.50.14', '10.0.50.9'),
        'ns-vlan300': ('veth-ns300', '10.0.50.19,10.0.50.22', '10.0.50.17'),
        'ns-vlan400': ('veth-ns400', '10.0.50.27,10.0.50.30', '10.0.50.25'),
    }




    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        ejecutar_comando_sudo(f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},255.255.255.248 --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8', f"Configurando dnsmasq en {ns}...")



    # Asignar tag de Vlan a interfaces del peer veth del OVS
    vlan_tags = {
        'veth-ovs100': 100,
        'veth-ovs200': 200,
        'veth-ovs300': 300,
        'veth-ovs400': 400
    }



    for veth_ovs, vlan in vlan_tags.items():
        ejecutar_comando_sudo(f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Asignando tag VLAN {vlan} a {veth_ovs}...")

    # Definir la interfaz ens5 como troncal para que todas las VLANs puedan llevar y recoger tráfico
    ejecutar_comando_sudo('ovs-vsctl set port ens5 trunk=100,200,300,400', "Configurando ens5 como troncal para las VLANs 100, 200, 300 y 400...")

    # Natear las 3 redes que estamos definiendo
    nat_rules = [
        'iptables -t nat -I POSTROUTING -s 10.0.50.0/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.8/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.16/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.24/29 -o ens3 -j MASQUERADE'
    ]


    for rule in nat_rules:
        ejecutar_comando_sudo(rule, f"Aplicando regla NAT: {rule}...")

    print("Configuración completa en HeadNode")

# Ejecutar la configuración
configurar_headnode()
