import logging
import paramiko
import time
from app.database.database import get_db, engine
from app.database.models import WorkerUsage, Worker, create_tables
from sqlalchemy.orm import Session

from app.utils.monitoring import get_cpu_usage, get_ram_usage, get_disk_usage


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


# Función para crear un nuevo registro en la tabla worker_usage
def create_monitoring_record(db: Session, worker, cpu_usage, ram_usage, disk_usage):
    record = WorkerUsage(
        worker_id=worker.id,  # Asignar el ID del worker
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
        disk_usage=disk_usage,
        net_speed="1000Mb/s"  # Puedes agregar la función para obtener esta información
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

    # Loop de monitoreo cada 5 minutos
    while True:
        # Obtener la sesión de la base de datos
        db = next(get_db())
        logger.info('Sesión de base de datos iniciada')

        # Recuperar todos los workers de la tabla 'workers'
        workers = db.query(Worker).all()

        for worker in workers:
            logger.info(f'Monitoreando el worker: {worker.hostname} ({worker.ip})')

            # Aquí puedes integrar las credenciales reales (o extraerlas de la tabla workers)
            username = 'ubuntu'
            password = 'ubuntu'

            # Obtener los valores de monitoreo reales mediante SSH
            cpu_usage = get_cpu_usage(worker.ip, username, password)  # Usar IP para la conexión
            ram_usage = get_ram_usage(worker.ip, username, password)
            disk_usage = get_disk_usage(worker.ip, username, password)

            # Imprimir los valores en consola además de registrarlos en el log
            print(f"Monitoreo de {worker.hostname} ({worker.ip})")
            print(f"Uso de CPU: {cpu_usage}%")
            print(f"Uso de RAM: {ram_usage}%")
            print(f"Uso de Disco: {disk_usage}")
            print("\n")

            logger.info(f"Uso de CPU: {cpu_usage}%")
            logger.info(f"Uso de RAM: {ram_usage}%")
            logger.info(f"Uso de Disco: {disk_usage}")

            # Crear un nuevo registro de monitoreo en la base de datos
            new_record = create_monitoring_record(
                db,
                worker=worker,
                cpu_usage=cpu_usage,
                ram_usage=ram_usage,
                disk_usage=disk_usage
            )
            logger.info(f'Registro de monitoreo creado: {new_record.worker_id} con timestamp {new_record.timestamp}')

        # Cerrar la sesión de la base de datos
        db.close()
        logger.info('Sesión de base de datos cerrada')

        # Pausar la ejecución durante 5 minutos antes de la próxima iteración
        logger.info("Esperando 5 minutos antes de la siguiente ronda de monitoreo...")
        time.sleep(300)  # 300 segundos = 5 minutos


if __name__ == '__main__':
    main()
