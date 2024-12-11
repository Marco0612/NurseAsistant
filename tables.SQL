-- Drop tables if you need to reset the schema (Optional)
-- DROP TABLE IF EXISTS patient_medicines, patients, medicines, frequencies, users CASCADE;

-- USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PATIENTS TABLE
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MEDICINES TABLE
CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FREQUENCIES TABLE
-- This table stores different administration frequencies in Spanish.
CREATE TABLE frequencies (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,   -- e.g., "Diario", "Cada 8 horas", "Semanal"
    descripcion TEXT                       -- Additional description if needed
);

-- PATIENT_MEDICINES TABLE
-- Now it references a frequency rather than storing an integer value.
CREATE TABLE patient_medicines (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    medicine_id INT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    frequency_id INT NOT NULL REFERENCES frequencies(id),
    start_date DATE NOT NULL,
    end_date DATE
);

-- Optional Indexes
-- CREATE INDEX idx_patients_user_id ON patients(user_id);
-- CREATE INDEX idx_patient_medicines_patient_id ON patient_medicines(patient_id);
-- CREATE INDEX idx_patient_medicines_medicine_id ON patient_medicines(medicine_id);
INSERT INTO frequencies (nombre, descripcion) VALUES 
('Diario', 'Administrar una vez al día'),
('Cada 12 horas', 'Administrar dos veces al día, cada 12 horas'),
('Cada 8 horas', 'Administrar tres veces al día, cada 8 horas'),
('Cada 6 horas', 'Administrar cuatro veces al día, cada 6 horas'),
('Semanal', 'Administrar una vez por semana'),
('Mensual', 'Administrar una vez al mes');
