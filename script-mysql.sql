-- Crear el esquema cloud_project
CREATE DATABASE IF NOT EXISTS cloud_project;

-- Usar el esquema
USE cloud_project;

-- Crear la tabla workers
CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(50) NOT NULL,
    ip VARCHAR(45) NOT NULL,
    password_hashed VARCHAR(255) NULL,
    UNIQUE(ip)
);

-- Insertar los tres workers en la tabla workers
INSERT INTO workers (hostname, ip, password_hashed)
VALUES
    ('worker1', '10.0.0.30', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy'),  -- Reemplaza NULL con una contraseña hasheada si es necesario
    ('worker2', '10.0.0.40', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy'),
    ('worker3', '10.0.0.50', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy');

-- Crear la tabla worker_usage para registrar el consumo de los workers
CREATE TABLE IF NOT EXISTS worker_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    cpu_usage FLOAT NOT NULL,
    ram_usage FLOAT NOT NULL,
    disk_usage VARCHAR(255) NOT NULL,
    net_speed VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);
