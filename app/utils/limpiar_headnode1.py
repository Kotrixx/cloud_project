import subprocess

from app.utils.general_utils import run_sudo_command


# Function to clean up VLAN subinterfaces
def clean_vlan_subinterfaces():
    vlan_subinterfaces = ['br-int.100', 'br-int.200', 'br-int.300']
    for subinterface in vlan_subinterfaces:
        run_sudo_command(f'ip link delete {subinterface}')
        print(f'Removed VLAN subinterface: {subinterface}')


# Function to delete both ends of veth pairs
def clean_veth_interfaces():
    result = subprocess.run("ip -br addr", shell=True, capture_output=True, text=True)
    interfaces = result.stdout.splitlines()

    for line in interfaces:
        interface = line.split()[0]
        if interface not in ['lo', 'ens3', 'ens4', 'ens5']:
            run_sudo_command(f'ip link delete {interface}')
            print(f'Removed interface: {interface}')


# Function to clean up OVS, ensuring no associated ports exist
def clean_ovs():
    result = subprocess.run("ovs-vsctl show", shell=True, capture_output=True, text=True)
    ovs_list = result.stdout.splitlines()

    # Remove ports from the OVS before deleting the bridge
    for line in ovs_list:
        if "Bridge" in line:
            ovs_name = line.split()[1]
            # List ports associated with the bridge and remove them
            run_sudo_command(f'ovs-vsctl list-ports {ovs_name}')
            run_sudo_command(f'ovs-vsctl --if-exists del-port {ovs_name} veth-ovs100')
            run_sudo_command(f'ovs-vsctl --if-exists del-port {ovs_name} veth-ovs200')
            run_sudo_command(f'ovs-vsctl --if-exists del-port {ovs_name} veth-ovs300')
            run_sudo_command(f'ovs-vsctl --if-exists del-port {ovs_name} ens5')
            run_sudo_command(f'ovs-vsctl del-br {ovs_name}')
            print(f'Removed OVS: {ovs_name}')


# Function to clean dnsmasq processes
def clean_dnsmasq_processes(exempt_dnsmasq_process):
    result = subprocess.run("ps -ef | grep dnsmasq", shell=True, capture_output=True, text=True)
    processes = result.stdout.splitlines()

    for line in processes:
        if exempt_dnsmasq_process not in line and "grep" not in line:
            pid = line.split()[1]
            run_sudo_command(f'kill -15 {pid}')
            print(f'Removed dnsmasq process: {pid}')


# Function to clean qemu processes
def clean_qemu_processes(exempt_qemu_process):
    result = subprocess.run("ps -ef | grep qemu", shell=True, capture_output=True, text=True)
    processes = result.stdout.splitlines()

    for line in processes:
        if exempt_qemu_process not in line and "grep" not in line:
            pid = line.split()[1]
            run_sudo_command(f'kill -15 {pid}')
            print(f'Removed qemu process: {pid}')


# Function to clean namespaces
def clean_namespaces():
    result = subprocess.run("ip netns list", shell=True, capture_output=True, text=True)
    namespaces = result.stdout.splitlines()

    for ns in namespaces:
        ns_name = ns.split()[0]
        run_sudo_command(f'ip netns del {ns_name}')
        print(f'Removed namespace: {ns_name}')


# Main function to execute the cleanup on the headnode
def clean_headnode():
    exempt_dnsmasq_process = '6631'  # Replace with the dnsmasq process to keep
    exempt_qemu_process = '6633'  # Replace with the qemu process to keep

    print("Cleanup started on HeadNode")
    clean_vlan_subinterfaces()  # Clean VLAN subinterfaces
    clean_veth_interfaces()  # Clean veth interfaces
    clean_dnsmasq_processes(exempt_dnsmasq_process)
    clean_qemu_processes(exempt_qemu_process)
    clean_namespaces()
    clean_ovs()  # Clean OVS at the end to ensure everything is deleted
    print("Cleanup complete on HeadNode")


# Run the cleanup
clean_headnode()
