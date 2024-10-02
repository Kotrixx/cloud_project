from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Configuración de la base de datos
DATABASE_URL = (f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/"
                f"{os.getenv('DB_NAME')}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Crear una sesión para conectarse a la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
