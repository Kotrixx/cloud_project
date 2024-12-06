import os
import subprocess
import sys
import requests
import json

# Global variable to store the authentication token
AUTH_TOKEN = None

def login():
    """
    Authenticate user and retrieve access token
    """
    global AUTH_TOKEN

    print("\nLogin Required")
    username = input("Enter username: ")
    password = input("Enter password: ")

    url = "http://localhost:8000/v1.0/security/login"
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            # Successful login
            AUTH_TOKEN = response.json().get('access_token')
            print("Login successful!")
            return True
        elif response.status_code == 401:
            # Unauthorized - incorrect credentials
            print("Error: Incorrect username or password.")
            return False
        elif response.status_code == 403:
            # Forbidden - login incorrect or insufficient permissions
            print("Error: Access denied. Invalid login credentials.")
            return False
        elif response.status_code == 404:
            # User not found
            print("Error: User not found in the system.")
            return False
        else:
            print(f"Unexpected error: {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return False

# Rest of the script remains the same as in the previous version
def authenticated_request(method, url, json_data=None):
    """
    Make an authenticated request to the API
    """
    global AUTH_TOKEN

    if not AUTH_TOKEN:
        print("You must login first!")
        return None

    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json_data)
        else:
            print(f"Unsupported HTTP method: {method}")
            return None

        # Check for token expiration or unauthorized access
        if response.status_code == 401:
            print("Session expired. Please login again.")
            AUTH_TOKEN = None
            return None

        return response

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def list_topologies_request():
    response = authenticated_request('GET', "http://localhost:8080/linux_cluster/topologies")
    if not response:
        return

    if response.status_code == 200:
        topologies = response.json()
        for topology in topologies:
            print(f"ID: {topology['_id']}")
            print(f"Name: {topology['name']}")
            print(f"Nodes: {topology['nodes']}")
            print(f"Topology Name: {topology['topology_name']}")
            # ... rest of the printing logic remains the same
            print("-" * 40)
    else:
        print(f"Error retrieving topologies: {response.status_code}")

def cargar_configuracion_json(nombre_archivo):
    try:
        with open(nombre_archivo, 'r') as file:
            json_data = json.load(file)

        response = authenticated_request('POST', "http://localhost:8080/linux_cluster/configurar_headnode", json_data)

        if response and response.status_code == 200:
            print("Slice created successfully through the API.")
        else:
            print(f"Error creating slice: {response.status_code}, {response.text}")

    except FileNotFoundError:
        print(f"File {nombre_archivo} not found.")
    except json.JSONDecodeError:
        print(f"Error reading file {nombre_archivo}. Ensure it's in valid JSON format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# The rest of the functions remain mostly the same, but use authenticated_request

def borrar_slice():
    response = authenticated_request('POST', "http://localhost:8080/linux_cluster/limpiar_headnode")
    if response and response.status_code == 200:
        print("Headnode cleaned successfully.")
    else:
        print(f"Error cleaning headnode: {response.status_code}")

def listar_consumo():
    response = authenticated_request('GET', "http://localhost:8080/linux_cluster/workers/usage/now")
    if not response:
        return

    if response.status_code == 200:
        usage_data = response.json()
        for usage in usage_data:
            print(f"Worker ID: {usage['worker_id']}")
            print(f"CPU Usage: {usage['cpu_usage']}%")
            # ... rest of the printing logic remains the same
    else:
        print(f"Error: {response.status_code} - {response.text}")


def mostrar_menu():
    print("\n")
    print("Choose an option:")
    print("1. Create a new slice")
    print("2. Edit an existing slice")
    print("3. List existing slices")
    print("4. Delete a slice")
    print("5. List system resource consumption")
    print("6. Import VM image")
    print("7. Generate console access credentials")
    print("8. Logout")
    print("9. Exit")


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
    global AUTH_TOKEN
    while True:
        # If not authenticated, require login
        if not AUTH_TOKEN:
            login_success = login()
            if not login_success:
                continue

        mostrar_menu()
        opcion = input("Choose an option: ")

        try:
            if opcion == "1":
                crear_slice()
            elif opcion == "2":
                editar_slice()
            elif opcion == "3":
                list_topologies_request()
            elif opcion == "4":
                borrar_slice()
            elif opcion == "5":
                listar_consumo()
            elif opcion == "6":
                importar_imagen()
            elif opcion == "7":
                generar_credenciales()
            elif opcion == "8":
                print("Logging out...")
                AUTH_TOKEN = None  # Clear the token
            elif opcion == "9":
                print("Exiting the program...")
                break
            else:
                print("Invalid option, please try again.")

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
