from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Modelo de la tabla workers
class Worker(Base):
    __tablename__ = 'workers'

    id = Column(Integer, primary_key=True, index=True)
    worker_name = Column(String(50), index=True)  # Nombre del worker (worker1, worker2, worker3)
    hostname = Column(String(50), index=True)     # Hostname (ubuntu)
    ip = Column(String(45), unique=True, index=True)  # Dirección IP, debe ser única
    password_hashed = Column(String(255))  # Contraseña hasheada (opcional)

    # Relación con la tabla worker_usage
    usage_records = relationship("WorkerUsage", back_populates="worker")


# Modelo de la tabla worker_usage para registrar el consumo de los workers
class WorkerUsage(Base):
    __tablename__ = 'worker_usage'

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey('workers.id', ondelete='CASCADE'))  # Relación con la tabla workers
    cpu_usage = Column(Float, nullable=False)
    ram_usage = Column(Float, nullable=False)
    disk_usage = Column(String(255), nullable=False)
    net_speed = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Campo de timestamp

    # Relación con la tabla workers
    worker = relationship("Worker", back_populates="usage_records")


# Crear las tablas en la base de datos (si no existen)
def create_tables(engine):
    Base.metadata.create_all(bind=engine)
