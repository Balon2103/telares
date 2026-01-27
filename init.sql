-- ===============================
-- BASE DE DATOS
-- ===============================

-- Crear la base de datos (solo si no existe)


-- ===============================
-- USUARIOS (LOGIN)
-- ===============================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usuario inicial
INSERT INTO users (username, password)
VALUES ('admin', 'admin2025')
ON CONFLICT (username) DO NOTHING;

-- ===============================
-- NODOS DE RED
-- ===============================
CREATE TABLE IF NOT EXISTS nodos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ip VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(150),
    rol VARCHAR(50),

    -- 🔹 Integración NetBox
    netbox_id INTEGER,

    -- 🔹 Posición NetVis
    pos_x DOUBLE PRECISION DEFAULT 0.0,
    pos_y DOUBLE PRECISION DEFAULT 0.0,
    fixed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- ENLACES DE RED
-- ===============================
CREATE TABLE IF NOT EXISTS enlaces (
    id SERIAL PRIMARY KEY,
    origen INTEGER REFERENCES nodos(id) ON DELETE CASCADE,
    destino INTEGER REFERENCES nodos(id) ON DELETE CASCADE,
    tipo VARCHAR(50),
    ancho_banda VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- RESPALDO AUTOMÁTICO
-- ===============================
CREATE TABLE IF NOT EXISTS backup_schedule (
    id SERIAL PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    frequency VARCHAR(20), -- daily | weekly | monthly
    time TIME
);
