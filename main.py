import bcrypt


# Función para encriptar una palabra usando bcrypt
def encrypt_password(password):
    # Hashear la contraseña usando bcrypt
    password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return password_hashed


# Función de ejemplo que imprime un saludo
def print_hi(name):
    print(f'Hi, {name}')  # Presionar Ctrl+F8 para alternar el punto de interrupción.


if __name__ == '__main__':
    # Saludar con el nombre
    print_hi('PyCharm')

    # Encriptar la palabra "ubuntu" usando bcrypt
    password = "ubuntu"
    hashed_password = encrypt_password(password)

    # Mostrar la contraseña encriptada
    print(f'La contraseña encriptada es: {hashed_password.decode("utf-8")}')
