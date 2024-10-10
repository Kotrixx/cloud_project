import subprocess


# Function to execute commands with sudo
def run_sudo_command(command, description=""):
    if description:
        print(description)
    sudo_command = f"echo 'ubuntu' | sudo -S {command}"
    process = subprocess.Popen(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    if output:
        print(output)
    if error:
        print(f"Error: {error}")


# Main function to configure the HeadNode
def configure_headnode(
        ovs_br_name: str = 'br-int',
        namespaces=None,
        veth_pairs=None,
        subinterfaces=None,
        gateway_ips=None,
        dnsmasq_configs=None,
        vlan_tags=None

):
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

    phy_iface = 'ens5'
    print("Configuration started on HeadNode")

    # Update the system
    run_sudo_command('apt-get update', "Updating the system... (this may take a while, do not stop the program)")

    # Create a new OVS bridge called br-int
    run_sudo_command(f'ovs-vsctl add-br {ovs_br_name}', f"Creating the OVS bridge {ovs_br_name}...")
    run_sudo_command(f'ip link set dev {ovs_br_name} up', f"Bringing up the {ovs_br_name} bridge...")

    # Bring up interface ens5 and add it to OVS
    run_sudo_command(f'ip link set {phy_iface} up', f"Bringing up the {phy_iface} interface...")
    run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {phy_iface}', f"Connecting the {phy_iface} interface to OVS...")

    # Enable IPv4 forwarding
    run_sudo_command('sysctl -w net.ipv4.ip_forward=1', "Enabling IPv4 forwarding...")

    # Create namespaces

    for ns in namespaces:
        run_sudo_command(f'ip netns add {ns}', f"Creating namespace {ns}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev lo up',
                         f"Bringing up the loopback interface in {ns}...")

    # Create and configure veth pairs
    """veth_pairs = [
        ('veth-ovs100', 'veth-ns100', 'ns-vlan100'),
        ('veth-ovs200', 'veth-ns200', 'ns-vlan200'),
        ('veth-ovs300', 'veth-ns300', 'ns-vlan300'),
        ('veth-ovs400', 'veth-ns400', 'ns-vlan400')
    ]"""

    for veth_ovs, veth_ns, ns in veth_pairs:
        run_sudo_command(f'ip link add {veth_ovs} type veth peer name {veth_ns}',
                         f"Creating the veth pair {veth_ovs} and {veth_ns}...")
        run_sudo_command(f'ip link set {veth_ns} netns {ns}', f"Moving {veth_ns} to namespace {ns}...")
        run_sudo_command(f'ovs-vsctl add-port {ovs_br_name} {veth_ovs}', f"Adding {veth_ovs} to OVS {ovs_br_name}...")
        run_sudo_command(f'ip link set {veth_ovs} up', f"Bringing up {veth_ovs}...")
        run_sudo_command(f'ip netns exec {ns} ip link set dev {veth_ns} up', f"Bringing up {veth_ns} in {ns}...")

    # Create subinterfaces on br-int and assign VLANs
    """subinterfaces = {
        'br-int.100': 100,
        'br-int.200': 200,
        'br-int.300': 300,
        'br-int.400': 400
    }"""

    for subinterface, vlan in subinterfaces.items():
        run_sudo_command(f'ip link add link br-int name {subinterface} type vlan id {vlan}',
                         f"Creating subinterface {subinterface} with VLAN {vlan}...")
        run_sudo_command(f'ip link set dev {subinterface} up', f"Bringing up subinterface {subinterface}...")

    # Assign IPs to the subinterfaces to act as gateways
    """gateway_ips = {
        'br-int.100': '10.0.50.1/29',
        'br-int.200': '10.0.50.9/29',
        'br-int.300': '10.0.50.17/29',
        'br-int.400': '10.0.50.25/29'
    }"""
    for subinterface, ip in gateway_ips.items():
        run_sudo_command(f'ip address add {ip} dev {subinterface}', f"Assigning IP {ip} to {subinterface}...")

    # Assign IPs to the veth interfaces in the namespaces
    veth_ips = {
        'ns-vlan100': '10.0.50.2/29',
        'ns-vlan200': '10.0.50.10/29',
        'ns-vlan300': '10.0.50.18/29',
        'ns-vlan400': '10.0.50.26/29'
    }

    for ns, ip in veth_ips.items():
        run_sudo_command(f'ip netns exec {ns} ip address add {ip} dev veth-ns{ns[-3:]}',
                         f"Assigning IP {ip} to {ns}...")

    # Run dnsmasq in each namespace to provide DHCP
    """dnsmasq_configs = {
        'ns-vlan100': ('veth-ns100', '10.0.50.3,10.0.50.6', '10.0.50.1'),
        'ns-vlan200': ('veth-ns200', '10.0.50.11,10.0.50.14', '10.0.50.9'),
        'ns-vlan300': ('veth-ns300', '10.0.50.19,10.0.50.22', '10.0.50.17'),
        'ns-vlan400': ('veth-ns400', '10.0.50.27,10.0.50.30', '10.0.50.25'),
    }"""

    for ns, (iface, dhcp_range, gateway) in dnsmasq_configs.items():
        run_sudo_command(
            f'ip netns exec {ns} dnsmasq --interface={iface} --dhcp-range={dhcp_range},255.255.255.248 --dhcp-option=3,{gateway} --dhcp-option=6,8.8.8.8',
            f"Configuring dnsmasq in {ns}...")

    # Assign VLAN tags to the veth interfaces in the OVS bridge
    """vlan_tags = {
        'veth-ovs100': 100,
        'veth-ovs200': 200,
        'veth-ovs300': 300,
        'veth-ovs400': 400
    }"""

    for veth_ovs, vlan in vlan_tags.items():
        run_sudo_command(f'ovs-vsctl set port {veth_ovs} tag={vlan}', f"Assigning VLAN tag {vlan} to {veth_ovs}...")

    # Set ens5 as a trunk interface to carry traffic for all VLANs
    run_sudo_command(f'ovs-vsctl set port {phy_iface} trunk=100,200,300,400',
                     f"Configuring {phy_iface} as a trunk for VLANs 100, 200, 300, and 400...")

    # NAT the 3 networks we are defining
    nat_rules = [
        'iptables -t nat -I POSTROUTING -s 10.0.50.0/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.8/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.16/29 -o ens3 -j MASQUERADE',
        'iptables -t nat -I POSTROUTING -s 10.0.50.24/29 -o ens3 -j MASQUERADE'
    ]

    for rule in nat_rules:
        run_sudo_command(rule, f"Applying NAT rule: {rule}...")

    print("Configuration completed on HeadNode")


# Execute the configuration
configure_headnode()
