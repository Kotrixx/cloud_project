# I'll transform the given code into a more modular structure, where each section is encapsulated into its own function.

import subprocess
from app.utils.general_utils import run_sudo_command

HEADNODE_PHY_IFACE = 'ens5'


# Function to update the system
def update_system():
    run_sudo_command('apt-get update', "Updating the system... (this may take a while, do not stop the program)")


# Function to configure the OVS bridge
def configure_ovs_bridge(ovs_br_name, phy_iface):
    run_sudo_command(f'ovs-vsctl add-br {ovs_br_name}', f"Creating the OVS bridge {ovs_br_name}...")
    run_sudo_command(f'ip link set dev {ovs_br_name} up', f"Bringing up the {ovs_br_name} bridge...")
    run_sudo_command(f'ip link set {phy_iface} up', f"Bringing up the {phy_iface} interface...")
    run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {phy_iface}', f"Connecting the {phy_iface} interface to OVS...")
    run_sudo_command('sysctl -w net.ipv4.ip_forward=1', "Enabling IPv4 forwarding...")


# Function to create namespaces
def create_namespaces(namespaces):
    for ns in namespaces:
        run_sudo_command(f'ip netns add {ns}', f"Creating namespace {ns}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev lo up', f"Bringing up the loopback interface in {ns}...")


# Function to create and configure veth pairs
def configure_veth_pairs(veth_pairs, ovs_br_name):
    for veth_ovs, veth_ns, ns in veth_pairs:
        run_sudo_command(f'ip link add {veth_ovs} type veth peer name {veth_ns}',
                         f"Creating veth pair {veth_ovs} and {veth_ns}...")
        run_sudo_command(f'ip link set {veth_ns} netns {ns}', f"Moving {veth_ns} to namespace {ns}...")
        run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {veth_ovs}', f"Adding {veth_ovs} to OVS {ovs_br_name}...")
        run_sudo_command(f'ip link set {veth_ovs} up', f"Bringing up {veth_ovs}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Bringing up {veth_ns} in {ns}...")


# Function to create subinterfaces on the OVS bridge and assign VLANs
def configure_subinterfaces(subinterfaces):
    for subinterface, vlan in subinterfaces.items():
        run_sudo_command(f'ip link add link br-int name {subinterface} type vlan id {vlan}',
                         f"Creating subinterface {subinterface} with VLAN {vlan}...")
        run_sudo_command(f'ip link set dev {subinterface} up', f"Bringing up subinterface {subinterface}...")


# Function to assign IPs to the subinterfaces
def assign_gateway_ips(gateway_ips):
    for subinterface, ip in gateway_ips.items():
        run_sudo_command(f'ip address add {ip} dev {subinterface}', f"Assigning IP {ip} to {subinterface}...")


# Function to assign IPs to veth interfaces in the namespaces
def assign_veth_ips(veth_ips):
    for ns, ip in veth_ips.items():
        run_sudo_command(f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}',
                         f"Assigning IP {ip} to {ns}...")


# Function to configure dnsmasq in namespaces
def configure_dnsmasq(dnsmasq_configs, DNS_MASK):
    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        run_sudo_command(
            f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},{DNS_MASK} --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8',
            f"Configuring dnsmasq in {ns}...")


# Function to assign VLAN tags to veth interfaces in the OVS bridge
def assign_vlan_tags(vlan_tags):
    for veth_ovs, vlan in vlan_tags.items():
        run_sudo_command(f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Assigning VLAN tag {vlan} to {veth_ovs}...")


# Function to set the physical interface as a trunk for VLANs
def configure_trunk_interface(phy_iface):
    run_sudo_command(f'ovs-vsctl set port {phy_iface} trunk=100,200,300,400',
                     f"Configuring {phy_iface} as a trunk for VLANs 100, 200, 300, and 400...")


# Function to apply NAT rules
def apply_nat_rules(nat_rules):
    for rule in nat_rules:
        run_sudo_command(rule, f"Applying NAT rule: {rule}...")


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

    # Execute the modular functions
    update_system()
    configure_ovs_bridge(ovs_br_name, HEADNODE_PHY_IFACE)
    create_namespaces(namespaces)
    configure_veth_pairs(veth_pairs, ovs_br_name)
    configure_subinterfaces(subinterfaces)
    assign_gateway_ips(gateway_ips)
    if mathias is True:
        assign_veth_ips({
            'ns-vlan100': '10.0.50.2/29',
            'ns-vlan200': '10.0.50.10/29',
            'ns-vlan300': '10.0.50.18/29',
            'ns-vlan400': '10.0.50.26/29'
        })
    else:
        assign_veth_ips({
            'ring1-ns-vlan100': '10.10.1.2/24',
            'ring1-ns-vlan200': '10.10.2.2/24',
            'ring1-ns-vlan300': '10.10.3.2/24',
            'ring1-ns-vlan400': '10.10.4.2/24'
        })
    configure_dnsmasq(dnsmasq_configs, DNS_MASK)
    assign_vlan_tags(vlan_tags)
    configure_trunk_interface(HEADNODE_PHY_IFACE)
    if mathias is True:
        apply_nat_rules([
            'iptables -t nat -I POSTROUTING -s 10.0.50.0/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.8/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.16/29 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.0.50.24/29 -o ens3 -j MASQUERADE'
        ])
    else:
        apply_nat_rules([
            'iptables -t nat -I POSTROUTING -s 10.10.1.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.2.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.3.0/24 -o ens3 -j MASQUERADE',
            'iptables -t nat -I POSTROUTING -s 10.10.4.0/24 -o ens3 -j MASQUERADE'
        ])

    print("Configuration completed")
