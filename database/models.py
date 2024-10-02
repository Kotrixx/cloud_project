from sqlalchemy import Column, Integer, String, Float

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Modelo de la tabla workers
class Worker(Base):
    __tablename__ = 'workers'

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(50), index=True)
    ip = Column(String(45), index=True)
    cpu_usage = Column(Float)
    ram_usage = Column(Float)
    disk_usage = Column(String(255))
    net_speed = Column(String(50))
    password_hashed = Column(String(255))  # Contraseña hasheada (opcional)


# Crear las tablas en la base de datos (si no existen)
def create_tables(engine):
    Base.metadata.create_all(bind=engine)
