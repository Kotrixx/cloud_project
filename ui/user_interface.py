import os
import subprocess
import sys

import requests
import json


def list_topologies_request():
    # URL de tu endpoint
    url = "http://localhost:8080/linux_cluster/topologies"

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


def cargar_configuracion_json(nombre_archivo):
    try:
        # Leer el archivo JSON
        with open(nombre_archivo, 'r') as file:
            json_data = json.load(file)
        print(json_data)
        # Hacer un request POST a la API con el contenido del archivo JSON
        url = "http://localhost:8080/linux_cluster/configurar_headnode"  # Cambia a la URL correcta de tu API
        response = requests.post(url, json=json_data)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            print("Slice creado correctamente a través de la API.")
        else:
            print(f"Error al crear el slice: {response.status_code}, {response.text}")

    except FileNotFoundError:
        print(f"El archivo {nombre_archivo} no fue encontrado.")
    except json.JSONDecodeError:
        print(f"Error al leer el archivo {nombre_archivo}. Asegúrese de que esté en formato JSON válido.")
    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")


def mostrar_menu():
    print("\n")
    print("Escoge una opción:")
    print("1. Crear un nuevo slice")
    print("2. Editar un slice existente")
    print("3. Listar los slices existentes")
    print("4. Borrar un slice")
    print("5. Listar el consumo de recursos del sistema")
    print("6. Importar imagen de una VM")
    print("7. Generar credenciales para acceder a la consola de VM")
    print("8. Salir")


def crear_slice():
    print("Seleccione una opción")
    print("1. Cargar configuración con un archivo JSON")
    print("2. Llenar valores desde cero")
    print("Selecciona la topología del slice:")
    opcion = input("Ingrese la opción deseada: ")

    if opcion == "1":
        print("Creando slice con archivo JSON...")
        nombre_archivo = input("Ingrese el nombre del archivo a cargar: ")

        # Llamar a la función que hará el request a la API con el archivo JSON
        cargar_configuracion_json(nombre_archivo)

    elif opcion == "2":
        print("1. Lineal")
        print("2. Malla")
        print("3. Árbol")
        print("4. Anillo")
        print("5. Bus")
        topologia = input("Ingrese el número de la topología deseada: ")

        # Aquí procesas la opción seleccionada
        if topologia == "1":
            print("Creando slice con topología Lineal...")
        elif topologia == "2":
            print("Creando slice con topología Malla...")
        # Agrega los demás casos para las demás topologías
        # Añade lógica para crear el slice según la topología


def editar_slice():
    print("Editar un slice existente:")
    # Aquí podrías mostrar un menú para agregar nodos o enlaces
    print("1. Agregar nodo")
    print("2. Agregar enlace")
    accion = input("Elija la acción: ")

    if accion == "1":
        # Lógica para agregar nodo
        nodo = input("Ingrese el nombre del nodo a agregar: ")
        print(f"Agregando nodo {nodo}...")
    elif accion == "2":
        # Lógica para agregar enlace
        enlace = input("Ingrese el enlace a agregar: ")
        print(f"Agregando enlace {enlace}...")


def listar_slices():
    print("Listando los slices existentes...")
    # Llamar a la función para listar las topologías
    list_topologies_request()
    # También puedes listar las VMs en KVM como lo hacías antes
    # subprocess.run(['virsh', 'list', '--all'])


import subprocess
import os  # Asegúrate de importar este módulo
import sys


def borrar_slice2():
    slice_name = input("Ingrese el nombre del slice a borrar: ")
    print(f"Borrando slice {slice_name}...")

    try:
        # Ruta al directorio de virtualenv y el script
        venv_dir = '../app/venv'
        script_headnode = '../app/utils/limpiar_headnode1.py'  # Cambiar a limpiar_headnode1.py
        script_worker = '../app/utils/limpiar_worker.py'

        # Paso 1: Crear el virtualenv si no existe, sin mostrar salida
        if not os.path.exists(venv_dir):
            subprocess.run(['sudo', sys.executable, '-m', 'venv', venv_dir],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)

        # Paso 2: Instalar paramiko en el virtualenv sin mostrar salida
        subprocess.run(['sudo', f"{venv_dir}/bin/pip", 'install', 'paramiko'],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)

        # Paso 3: Ejecutar el script limpiar_headnode1.py en el entorno virtual sin mensajes
        result_headnode = subprocess.run(
            ['sudo', f"{venv_dir}/bin/python", script_headnode, 'headnode'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result_headnode.returncode == 0:
            print(f"Headnode limpiado con éxito. Output:\n{result_headnode.stdout}")
        else:
            print(f"Error al limpiar el headnode. Error:\n{result_headnode.stderr}")

        # Ejecutar el script limpiar_worker.py para los workers
        subprocess.run(
            ['sudo', f"{venv_dir}/bin/python", script_worker],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"Slice {slice_name} borrado y topología limpiada con éxito.")

    except Exception as e:
        print(f"Error al ejecutar el script: {str(e)}")


def borrar_slice():
    url_headnode = "http://localhost:8080/linux_cluster/limpiar_headnode"  # Endpoint para limpiar headnode
    headers = {'Content-Type': 'application/json'}
    try:
        # Realizar el request POST al endpoint de limpiar_headnode
        print("Limpiando headnode...")
        response_headnode = requests.post(url_headnode, headers=headers)

        # Verificar el estado de la respuesta para headnode
        if response_headnode.status_code == 200:
            print(f"Headnode limpiado con éxito.")
        else:
            print(f"Error al limpiar el headnode: {response_headnode.status_code} - {response_headnode.text}")
    except Exception as e:
        print(f"Error al realizar la solicitud: {str(e)}")


def listar_consumo():
    # URL del endpoint que deseas consumir
    url = "http://localhost:8080/linux_cluster/workers/usage/now"
    try:
        # Realizar la solicitud GET a la API
        response = requests.get(url)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Obtener la respuesta en formato JSON
            usage_data = response.json()

            # Imprimir los datos de uso obtenidos
            for usage in usage_data:
                print(f"Worker ID: {usage['worker_id']}")
                print(f"CPU Usage: {usage['cpu_usage']}%")
                print(f"RAM Usage: {usage['ram_usage_percentage']}%")
                print("Disk Usage:")
                for disk in usage['disk_usage']:
                    print(f"  Volume: {disk['volume']}")
                    print(f"  Size: {disk['size']}")
                    print(f"  Used: {disk['used']}")
                    print(f"  Available: {disk['available']}")
                print(f"Timestamp: {usage['timestamp']}")
                print("-" * 40)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error al consumir la API: {str(e)}")


def importar_imagen():
    imagen_path = input("Ingrese la ruta de la imagen de la VM: ")
    print(f"Importando imagen desde {imagen_path}...")
    # Aquí añades la lógica para importar la imagen
    # subprocess.run(['virsh', 'define', imagen_path])


def generar_credenciales():
    print("Generando credenciales de acceso...")
    # Aquí añades la lógica para generar credenciales SSH o tokens
    # subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '2048'])


def main():
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ")

        if opcion == "1":
            crear_slice()
        elif opcion == "2":
            editar_slice()
        elif opcion == "3":
            listar_slices()  # Aquí se llama la función para listar slices y topologías
        elif opcion == "4":
            borrar_slice2()
        elif opcion == "5":
            listar_consumo()
        elif opcion == "6":
            importar_imagen()
        elif opcion == "7":
            generar_credenciales()
        elif opcion == "8":
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida, por favor intenta de nuevo.")


if __name__ == "__main__":
    main()
