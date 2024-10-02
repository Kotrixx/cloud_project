FROM python:3.10.15-slim

WORKDIR /usr/src/app

# Copy the requirements file from the project root
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary modules and packages
COPY log_module/logger.py .
COPY db_module/ ./db_module/
COPY utils/ ./utils/

CMD ["python", "logger.py"]
