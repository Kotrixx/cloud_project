import logging
import bcrypt
from db_module.database import get_db, engine
from db_module.models import Worker, create_tables
from sqlalchemy.orm import Session


# Configuración del logger
def setup_logger():
    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler('app.log')
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Función para crear un nuevo registro en la tabla de workers
def create_worker(db: Session, hostname, ip, cpu_usage, ram_usage, disk_usage, net_speed, password_plain=None):
    # Hashear la contraseña si se proporciona
    if password_plain:
        password_hashed = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt())
        password_hashed = password_hashed.decode('utf-8')  # Convertir a cadena para almacenar en la base de datos
    else:
        password_hashed = None

    worker = Worker(
        hostname=hostname,
        ip=ip,
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
        disk_usage=disk_usage,
        net_speed=net_speed,
        password_hashed=password_hashed
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


# Lógica principal de la aplicación
def main():
    logger = setup_logger()
    logger.info('Iniciando la aplicación')

    # Crear las tablas si no existen
    create_tables(engine)

    # Obtener la sesión de la base de datos
    db = next(get_db())
    logger.info('Sesión de base de datos iniciada')

    # Monitorear un worker (aquí puedes integrar tu lógica de monitoreo)
    hostname = 'worker1'
    ip = '10.0.0.30'
    cpu_usage = 20.5  # Ejemplo de valores
    ram_usage = 50.3
    disk_usage = "50GB"
    net_speed = "1000Mb/s"
    password_plain = 'ubuntu'  # Contraseña del worker

    # Crear un nuevo registro del worker en la base de datos
    new_worker = create_worker(db, hostname=hostname, ip=ip, cpu_usage=cpu_usage, ram_usage=ram_usage,
                               disk_usage=disk_usage, net_speed=net_speed, password_plain=password_plain)
    logger.info(f'Worker creado: {new_worker.hostname}')

    # Cerrar la sesión de la base de datos
    db.close()
    logger.info('Sesión de base de datos cerrada')


if __name__ == '__main__':
    main()
