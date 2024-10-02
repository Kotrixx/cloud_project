-- Crear el esquema cloud_project
CREATE DATABASE IF NOT EXISTS cloud_project;

-- Usar el esquema
USE cloud_project;

-- Crear la tabla workers
CREATE TABLE IF NOT EXISTS workers (
                                       id INT AUTO_INCREMENT PRIMARY KEY,
                                       worker_name VARCHAR(50) NOT NULL, -- El nombre del worker (worker1, worker2, worker3)
    hostname VARCHAR(50) NOT NULL,    -- El hostname que será "ubuntu" para todos los workers
    ip VARCHAR(45) NOT NULL,
    password_hashed VARCHAR(255) NULL,
    UNIQUE(ip)
    );

-- Insertar los tres workers en la tabla workers
INSERT INTO workers (worker_name, hostname, ip, password_hashed)
VALUES
    ('worker1', 'ubuntu', '10.0.0.30', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy'),
    ('worker2', 'ubuntu', '10.0.0.40', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy'),
    ('worker3', 'ubuntu', '10.0.0.50', '$2b$12$.do6IkS7MxYtLzzSMuCyjO/IuK3./wrCwHEIriuJnZzVAREWrutVy');

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
