import subprocess
import psutil


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
    print("Selecciona la topología del slice:")
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
    print("Listando los slices existentes:")
    # Ejemplo para listar VMs en KVM
    subprocess.run(['virsh', 'list', '--all'])


def borrar_slice():
    slice_name = input("Ingrese el nombre del slice a borrar: ")
    print(f"Borrando slice {slice_name}...")
    subprocess.run(['virsh', 'destroy', slice_name])


def listar_consumo():
    print(f"CPU: {psutil.cpu_percent()}%")
    print(f"Memoria: {psutil.virtual_memory().percent}%")


def importar_imagen():
    imagen_path = input("Ingrese la ruta de la imagen de la VM: ")
    print(f"Importando imagen desde {imagen_path}...")
    # Aquí añades la lógica para importar la imagen
    subprocess.run(['virsh', 'define', imagen_path])


def generar_credenciales():
    print("Generando credenciales de acceso...")
    # Aquí añades la lógica para generar credenciales SSH o tokens
    subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '2048'])


def main():
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ")

        if opcion == "1":
            crear_slice()
        elif opcion == "2":
            editar_slice()
        elif opcion == "3":
            listar_slices()
        elif opcion == "4":
            borrar_slice()
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
