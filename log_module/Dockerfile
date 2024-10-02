# Usar la imagen de Python 3.10-slim
FROM python:3.10.15-slim

WORKDIR /usr/src/app

# Copiar el archivo de requerimientos y luego instalar las dependencias
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos de la aplicación
COPY . .

# Ejecutar la aplicación
CMD ["python", "logger.py"]
