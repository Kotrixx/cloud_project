import ipaddress

from app.utils.general_utils import run_sudo_command


class NetworkConfiguration:
    """
    Clase para configurar una red con VLAN, DHCP y configuraciones de subinterfaces.

    Atributos:
        vlan_tag (int): Etiqueta VLAN para la configuración.
        dnsmasq_iface (str): Interfaz de DNSMASQ.
        dhcp_range_start (str): Límite bajo del rango DHCP para DNSMASQ.
        dhcp_range_end (str): Límite alto del rango DHCP para DNSMASQ.
        dnsmasq_gateway (str): Puerta de enlace para DNSMASQ.
        gateway_ip (str): IP de la puerta de enlace.
        subinterface (str): Subinterfaz OVS para la VLAN.
        vlan_id (int): ID de la VLAN.
        veth_ovs (str): Nombre del veth OVS.
        veth_ns (str): Nombre del veth en el espacio de nombres.
        namespace (str): Nombre del espacio de nombres.
    """

    def __init__(self, vlan_tag, dnsmasq_iface, dhcp_range_start, dhcp_range_end, dnsmasq_gateway,
                 gateway_ip, subinterface, vlan_id, veth_ovs, veth_ns, namespace):
        self.vlan_tag = vlan_tag
        self.dnsmasq_iface = dnsmasq_iface
        self.dhcp_range_start = dhcp_range_start
        self.dhcp_range_end = dhcp_range_end
        self.dnsmasq_gateway = dnsmasq_gateway
        self.gateway_ip = gateway_ip
        self.subinterface = subinterface
        self.vlan_id = vlan_id
        self.veth_ovs = veth_ovs
        self.veth_ns = veth_ns
        self.namespace = namespace

    def display_configuration(self):
        """Muestra toda la configuración de la red."""
        print("VLAN Tag:", self.vlan_tag)
        print("DNSMASQ Interface:", self.dnsmasq_iface)
        print("DHCP Range Start:", self.dhcp_range_start)
        print("DHCP Range End:", self.dhcp_range_end)
        print("DNSMASQ Gateway:", self.dnsmasq_gateway)
        print("Gateway IP:", self.gateway_ip)
        print("Subinterface:", self.subinterface)
        print("VLAN ID:", self.vlan_id)
        print("Veth OVS:", self.veth_ovs)
        print("Veth Namespace:", self.veth_ns)
        print("Namespace:", self.namespace)


HEADNODE_PHY_IFACE = 'ens5'


def get_next_ip(ip_with_cidr):
    # Convertir la IP en formato CIDR a un objeto IPv4Interface
    ip_interface = ipaddress.IPv4Interface(ip_with_cidr)

    # Obtener la IP sin la máscara (objeto IPv4Address)
    current_ip = ip_interface.ip

    # Calcular la siguiente IP
    next_ip = current_ip + 1

    # Retornar la IP con la máscara original
    return f"{next_ip}/{ip_interface.network.prefixlen}"


def remove_cidr(ip_with_cidr):
    # Dividir la IP en la parte de la dirección y la parte del prefijo usando '/'
    ip_without_cidr = ip_with_cidr.split('/')[0]

    return ip_without_cidr


def get_previous_ip(ip_with_cidr):
    # Convertir la IP con CIDR a un objeto IPv4Interface
    ip_interface = ipaddress.IPv4Interface(ip_with_cidr)

    # Obtener la IP actual sin el prefijo
    current_ip = ip_interface.ip

    # Calcular la IP anterior restando 1
    previous_ip = current_ip - 1

    return str(previous_ip)


def create_ring_topology(network: NetworkConfiguration):
    ovs_br_name: str = 'br-int'
    namespaces = None
    veth_pairs = None
    subinterfaces = None
    gateway_ips = None
    dnsmasq_configs = None
    vlan_tags = None
    network_name = None
    mathias = False

    DNS_MASK = '255.255.255.0'



    if gateway_ips is None:
        gateway_ips = {
            'br-int.100': '10.0.50.1/29',
            'br-int.200': '10.0.50.9/29',
            'br-int.300': '10.0.50.17/29',
            'br-int.400': '10.0.50.25/29'
        }

    if subinterfaces is None:
        subinterfaces = {
            'br-int.100': 100,
            'br-int.200': 200,
            'br-int.300': 300,
            'br-int.400': 400
        }

    if veth_pairs is None:
        veth_pairs = [
            ('veth-ovs100', 'veth-ns100', 'ns-vlan100'),
            ('veth-ovs200', 'veth-ns200', 'ns-vlan200'),
            ('veth-ovs300', 'veth-ns300', 'ns-vlan300'),
            ('veth-ovs400', 'veth-ns400', 'ns-vlan400')
        ]

    print("Configuration started on HeadNode")

    # Updating the system
    run_sudo_command('apt-get update', "Updating the system... (this may take a while, do not stop the program)")

    run_sudo_command(f'ovs-vsctl add-br {ovs_br_name}',
                     f"Creating the OVS bridge {ovs_br_name}...")
    run_sudo_command(f'ip link set dev {ovs_br_name} up',
                     f"Bringing up the {ovs_br_name} bridge...")
    run_sudo_command(f'ip link set {HEADNODE_PHY_IFACE} up',
                     f"Bringing up the {HEADNODE_PHY_IFACE} interface...")
    run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {HEADNODE_PHY_IFACE}',
                     f"Connecting the {HEADNODE_PHY_IFACE} interface to OVS...")
    run_sudo_command('sysctl -w net.ipv4.ip_forward=1',
                     "Enabling IPv4 forwarding...")

    # Creating namespaces
    run_sudo_command(f'ip netns add {network.namespace}',
                     f"Creating namespace {network.namespace}...")
    run_sudo_command(f'ip netns exec {network.namespace} ip link set dev lo up',
                     f"Bringing up the loopback interface in {network.namespace}...")

    # Configuring veth pairs
    run_sudo_command(f'ip link add {network.veth_ovs} type veth peer name {network.veth_ns}',
                     f"Creating veth pair {network.veth_ovs} and {network.veth_ns}...")
    run_sudo_command(f'ip link set {network.veth_ns} netns {network.namespace}',
                     f"Moving {network.veth_ns} to namespace {network.namespace}...")
    run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {network.veth_ovs}',
                     f"Adding {network.veth_ovs} to OVS {ovs_br_name}...")
    run_sudo_command(f'ip link set {network.veth_ovs} up',
                     f"Bringing up {network.veth_ovs}...")
    run_sudo_command(f'ip netns exec {network.namespace} ip link set dev {network.veth_ns} up',
                     f"Bringing up {network.veth_ns} in {network.namespace}...")

    # Configuring subinterfaces for VLANs
    run_sudo_command(f'ip link add link {ovs_br_name} name {network.subinterface} type vlan id {network.vlan_id}',
                     f"Creating subinterface {network.subinterface} with VLAN {network.vlan_id}...")
    run_sudo_command(f'ip link set dev {network.subinterface} up',
                     f"Bringing up subinterface {network.subinterface}...")

    # Assigning gateway IPs
    run_sudo_command(f'ip address add {network.gateway_ip} dev {network.subinterface}',
                     f"Assigning IP {network.gateway_ip} to {network.subinterface}...")

    # Assigning IPs to veth interfaces in the namespaces
    next_ip = get_next_ip(network.gateway_ip)
    run_sudo_command(f'ip netns exec {network.namespace} ip address add {next_ip} dev {network.veth_ns}',
                     f"Assigning IP {next_ip} to {network.namespace}...")

    if vlan_tags is None:
        vlan_tags = {
            'veth-ovs100': 100,
            'veth-ovs200': 200,
            'veth-ovs300': 300,
            'veth-ovs400': 400
        }
    # Configuring dnsmasq in namespaces
    run_sudo_command(
        f'ip netns exec {network.namespace} dnsmasq --interface={network.veth_ns}'
        f' --dhcp-range={network.dhcp_range_start},{network.dhcp_range_end},{DNS_MASK} '
        f'--dhcp-option=3,{remove_cidr(network.gateway_ip)} --dhcp-option=6,8.8.8.8',
        f"Configuring dnsmasq in {network.namespace}...")

    # Assigning VLAN tags to veth interfaces
    run_sudo_command(f'ovs-vsctl set port {network.veth_ovs} tag={network.vlan_id}',
                     f"Assigning VLAN tag {network.vlan_id} to {network.veth_ovs}...")

    # Configuring trunk interface for VLANs
    # run_sudo_command(f'ovs-vsctl set port {HEADNODE_PHY_IFACE} trunk={",".join(map(str, vlan_tags.values()))}',
    #                  f"Configuring {HEADNODE_PHY_IFACE} as a trunk for VLANs {list(vlan_tags.values())}...")
    run_sudo_command(f'ovs-vsctl set port {HEADNODE_PHY_IFACE} trunk={network.vlan_tag}',
                     f"Configuring {HEADNODE_PHY_IFACE} as a trunk for VLANs {network.vlan_tag}...")
    # Applying NAT rules
    if mathias is True:
        nat_rules = [
            'iptables -t nat -I POSTROUTING -s 10.0.50.0/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.8/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.16/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.24/29 -o ens3 -j MASQUERADE'
        ]
    else:
        nat_rules = [
            'iptables -t nat -I POSTROUTING -s 10.10.1.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.2.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.3.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.4.0/24 -o ens3 -j MASQUERADE'
        ]

    # for rule in nat_rules:
    run_sudo_command(f'iptables -t nat -I POSTROUTING -s {get_previous_ip(network.gateway_ip)} -o ens3 -j MASQUERADE',
                     f"Applying NAT rule: 'iptables -t nat -I POSTROUTING -s {get_previous_ip(network.gateway_ip)} -o ens3 -j MASQUERADE'...")


if __name__ == "__main__":
    # Ejemplo de uso:
    config = NetworkConfiguration(
        vlan_tag=100,
        dnsmasq_iface='veth-ns100',
        dhcp_range_start='10.0.50.3',
        dhcp_range_end='10.0.50.6',
        dnsmasq_gateway='10.0.50.1',
        gateway_ip='10.0.50.1/29',
        subinterface='br-int.100',
        vlan_id=100,
        veth_ovs='veth-ovs100',
        veth_ns='veth-ns100',
        namespace='ns-vlan100'
    )
    config.display_configuration()
