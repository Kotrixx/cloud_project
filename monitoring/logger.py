import logging
import bcrypt
from app.database.database import get_db, engine
from app.database.models import Monitoring, Worker, create_tables  # Añadimos Worker
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


# Función para crear un nuevo registro en la tabla monitoring
def create_monitoring_record(db: Session, hostname, ip, cpu_usage, ram_usage, disk_usage, net_speed, password_hashed=None):
    record = Monitoring(
        hostname=hostname,
        ip=ip,
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
        disk_usage=disk_usage,
        net_speed=net_speed,
        password_hashed=password_hashed
        # No necesitamos pasar `timestamp`, se generará automáticamente
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# Lógica principal de la aplicación
def main():
    logger = setup_logger()
    logger.info('Iniciando la aplicación')

    # Crear las tablas si no existen
    create_tables(engine)

    # Obtener la sesión de la base de datos
    db = next(get_db())
    logger.info('Sesión de base de datos iniciada')

    # Recuperar todos los workers de la tabla 'workers'
    workers = db.query(Worker).all()

    for worker in workers:
        logger.info(f'Monitoreando el worker: {worker.hostname} ({worker.ip})')

        # Ejemplo de valores de monitoreo (puedes reemplazar estos valores con los datos reales)
        cpu_usage = 20.5  # Aquí puedes integrar la lógica de monitoreo real
        ram_usage = 50.3
        disk_usage = "50GB"
        net_speed = "1000Mb/s"

        # Crear un nuevo registro de monitoreo en la base de datos
        new_record = create_monitoring_record(
            db,
            hostname=worker.hostname,
            ip=worker.ip,
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            disk_usage=disk_usage,
            net_speed=net_speed,
            password_hashed=worker.password_hashed
        )
        logger.info(f'Registro de monitoreo creado: {new_record.hostname} con timestamp {new_record.timestamp}')

    # Cerrar la sesión de la base de datos
    db.close()
    logger.info('Sesión de base de datos cerrada')


if __name__ == '__main__':
    main()
