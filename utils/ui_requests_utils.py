import requests
from datetime import datetime, timezone
import requests
import json


def list_topologies_request():
    # URL de tu endpoint
    url = "http://<tu-servidor>/topologies"

    try:
        # Hacer la solicitud GET
        response = requests.get(url)

        # Verificar que la solicitud fue exitosa
        if response.status_code == 200:
            topologies = response.json()

            # Mostrar la información de manera legible
            for topology in topologies:
                print(f"ID: {topology['_id']}")
                print(f"Name: {topology['name']}")
                print(f"Nodes: {topology['nodes']}")
                print(f"Topology Name: {topology['topology_name']}")
                print("VLAN Tags:")
                for veth, vlan in topology['vlan_tags'].items():
                    print(f"  {veth}: {vlan}")

                print("DNSMasq Configurations:")
                for namespace, config in topology['dnsmasq_configs'].items():
                    print(f"  Namespace {namespace}:")
                    for key, value in config.items():
                        print(f"    {key}: {value}")

                print("Gateway IPs:")
                for subinterface, ip in topology['gateway_ips'].items():
                    print(f"  {subinterface}: {ip}")

                print("Subinterfaces:")
                for subinterface, vlan in topology['subinterfaces'].items():
                    print(f"  {subinterface}: VLAN {vlan}")

                print("Veth Pairs:")
                for pair in topology['veth_pairs']:
                    print(f"  {pair[0]} <--> {pair[1]}")

                print("Namespaces:")
                for namespace in topology['namespaces']:
                    print(f"  {namespace}")

                print(f"Creation Timestamp: {topology['creation_timestamp']}")
                print(f"Topology Type: {topology['topology_type']}")
                print("-" * 40)
        else:
            print(f"Error al obtener los topologías: {response.status_code}")

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")


# Llamar la función para listar las topologías

"""
# URL del endpoint (modifícala según sea necesario)
url = "http://localhost:8000/linux_cluster/ring"  # Modifica la ruta según tu servidor

# Datos a enviar en el cuerpo de la solicitud
data = {
    "nodes": 4,
    "topology_name": "NetworkRing",  # El nombre de la topología
    "node_networks": {
        "node1": "192.168.1.1/24",
        "node2": "192.168.1.2/24",
        "node3": "192.168.1.3/24",
        "node4": "192.168.1.4/24"
    },
    "dhcp_settings": {
        "node1": "dhcp-range=192.168.1.100,192.168.1.150",
        "node2": "dhcp-range=192.168.1.100,192.168.1.150"
    },
    "creation_timestamp": datetime.now(tz=timezone.utc).isoformat()
}

# Hacer la solicitud POST
response = requests.post(url, json=data)

# Imprimir la respuesta
if response.status_code == 200:
    print("Topology created successfully!")
    print(response.json())  # Imprime la respuesta del servidor
else:
    print(f"Error: {response.status_code}")
    print(response.text)
    """
