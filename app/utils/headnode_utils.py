import subprocess
from app.utils.general_utils import run_sudo_command

HEADNODE_PHY_IFACE = 'ens5'


def create_ring_topology(
        ovs_br_name: str = 'br-int',
        namespaces=None,
        veth_pairs=None,
        subinterfaces=None,
        gateway_ips=None,
        dnsmasq_configs=None,
        vlan_tags=None,
        network_name=None,
        mathias=False
):
    # DNS_MASK = '255.255.255.248'
    DNS_MASK = '255.255.255.0'

    if vlan_tags is None:
        vlan_tags = {
            'veth-ovs100': 100,
            'veth-ovs200': 200,
            'veth-ovs300': 300,
            'veth-ovs400': 400
        }

    if dnsmasq_configs is None:
        dnsmasq_configs = {
            'ns-vlan100': ('veth-ns100', '10.0.50.3,10.0.50.6', '10.0.50.1'),
            'ns-vlan200': ('veth-ns200', '10.0.50.11,10.0.50.14', '10.0.50.9'),
            'ns-vlan300': ('veth-ns300', '10.0.50.19,10.0.50.22', '10.0.50.17'),
            'ns-vlan400': ('veth-ns400', '10.0.50.27,10.0.50.30', '10.0.50.25'),
        }

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

    if namespaces is None:
        namespaces = ['ns-vlan100', 'ns-vlan200', 'ns-vlan300', 'ns-vlan400']

    print("Configuration started on HeadNode")

    # Updating the system
    run_sudo_command('apt-get update', "Updating the system... (this may take a while, do not stop the program)")

    # Configuring OVS bridge
    run_sudo_command(f'ovs-vsctl add-br {ovs_br_name}', f"Creating the OVS bridge {ovs_br_name}...")
    run_sudo_command(f'ip link set dev {ovs_br_name} up', f"Bringing up the {ovs_br_name} bridge...")
    run_sudo_command(f'ip link set {HEADNODE_PHY_IFACE} up', f"Bringing up the {HEADNODE_PHY_IFACE} interface...")
    run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {HEADNODE_PHY_IFACE}', f"Connecting the {HEADNODE_PHY_IFACE} interface to OVS...")
    run_sudo_command('sysctl -w net.ipv4.ip_forward=1', "Enabling IPv4 forwarding...")

    # Creating namespaces
    for ns in namespaces:
        run_sudo_command(f'ip netns add {ns}', f"Creating namespace {ns}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev lo up', f"Bringing up the loopback interface in {ns}...")

    # Configuring veth pairs
    for veth_ovs, veth_ns, ns in veth_pairs:
        run_sudo_command(f'ip link add {veth_ovs} type veth peer name {veth_ns}', f"Creating veth pair {veth_ovs} and {veth_ns}...")
        run_sudo_command(f'ip link set {veth_ns} netns {ns}', f"Moving {veth_ns} to namespace {ns}...")
        run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {veth_ovs}', f"Adding {veth_ovs} to OVS {ovs_br_name}...")
        run_sudo_command(f'ip link set {veth_ovs} up', f"Bringing up {veth_ovs}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Bringing up {veth_ns} in {ns}...")

    # Configuring subinterfaces for VLANs
    for subinterface, vlan in subinterfaces.items():
        run_sudo_command(f'ip link add link {ovs_br_name} name {subinterface} type vlan id {vlan}', f"Creating subinterface {subinterface} with VLAN {vlan}...")
        run_sudo_command(f'ip link set dev {subinterface} up', f"Bringing up subinterface {subinterface}...")

    # Assigning gateway IPs
    for subinterface, ip in gateway_ips.items():
        run_sudo_command(f'ip address add {ip} dev {subinterface}', f"Assigning IP {ip} to {subinterface}...")

    # Assigning IPs to veth interfaces in the namespaces
    if mathias is True:
        veth_ips = {
            'ns-vlan100': '10.0.50.2/29',
            'ns-vlan200': '10.0.50.10/29',
            'ns-vlan300': '10.0.50.18/29',
            'ns-vlan400': '10.0.50.26/29'
        }
    else:
        veth_ips = {
            'ring1-ns-vlan100': '10.10.1.2/24',
            'ring1-ns-vlan200': '10.10.2.2/24',
            'ring1-ns-vlan300': '10.10.3.2/24',
            'ring1-ns-vlan400': '10.10.4.2/24'
        }

    for ns, ip in veth_ips.items():
        run_sudo_command(f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}', f"Assigning IP {ip} to {ns}...")

    # Configuring dnsmasq in namespaces
    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        run_sudo_command(f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},{DNS_MASK} --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8', f"Configuring dnsmasq in {ns}...")

    # Assigning VLAN tags to veth interfaces
    for veth_ovs, vlan in vlan_tags.items():
        run_sudo_command(f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Assigning VLAN tag {vlan} to {veth_ovs}...")

    # Configuring trunk interface for VLANs
    run_sudo_command(f'ovs-vsctl set port {HEADNODE_PHY_IFACE} trunk={",".join(map(str, vlan_tags.values()))}', f"Configuring {HEADNODE_PHY_IFACE} as a trunk for VLANs {list(vlan_tags.values())}...")

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

    for rule in nat_rules:
        run_sudo_command(rule, f"Applying NAT rule: {rule}...")

    print("Configuration completed")
