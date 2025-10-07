-- Migración para verificación de email
-- Crear tabla de tokens de verificación de email

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Crear índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_email_verification_token ON email_verification_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_verification_user ON email_verification_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_email ON email_verification_tokens (email);

-- Agregar columna de verificación a la tabla users
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;

-- Crear índice para usuarios no verificados
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users (email_verified);
