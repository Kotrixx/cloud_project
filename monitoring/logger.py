import logging
import paramiko
from app.database.database import get_db, engine
from app.database.models import Monitoring, Worker, create_tables
from sqlalchemy.orm import Session


# Función para ejecutar comandos SSH en un worker
def ssh_execute_command(hostname, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    ssh.close()
    return output


# Funciones para obtener el uso de CPU, RAM y Disco desde el worker
def get_cpu_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | xargs")

def get_ram_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "free | grep Mem | awk '{printf(\"%.0f\", $3/$2 * 100)}'")

def get_disk_usage(hostname, username, password):
    return ssh_execute_command(hostname, username, password, "df -h --output=source,size,used,avail | grep '^/dev'")


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
def create_monitoring_record(db: Session, hostname, ip, cpu_usage, ram_usage, disk_usage, password_hashed=None):
    record = Monitoring(
        hostname=hostname,
        ip=ip,
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
        disk_usage=disk_usage,
        password_hashed=password_hashed
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

        # Aquí puedes integrar las credenciales reales (o extraerlas de la tabla workers)
        username = 'ubuntu'
        password = 'ubuntu'

        # Obtener los valores de monitoreo reales mediante SSH
        cpu_usage = get_cpu_usage(worker.hostname, username, password)
        ram_usage = get_ram_usage(worker.hostname, username, password)
        disk_usage = get_disk_usage(worker.hostname, username, password)

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
            hostname=worker.hostname,
            ip=worker.ip,
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            disk_usage=disk_usage,
            password_hashed=worker.password_hashed
        )
        logger.info(f'Registro de monitoreo creado: {new_record.hostname} con timestamp {new_record.timestamp}')

    # Cerrar la sesión de la base de datos
    db.close()
    logger.info('Sesión de base de datos cerrada')


if __name__ == '__main__':
    main()
