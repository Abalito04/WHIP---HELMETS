-- Migración para tabla de wishlist/favoritos
-- Ejecutar en PostgreSQL

CREATE TABLE IF NOT EXISTS wishlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES productos(id) ON DELETE CASCADE,
    UNIQUE(user_id, product_id) -- Evitar duplicados
);

-- Índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_wishlist_user_id ON wishlist(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_product_id ON wishlist(product_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_created_at ON wishlist(created_at);

-- Comentarios
COMMENT ON TABLE wishlist IS 'Lista de productos favoritos de usuarios';
COMMENT ON COLUMN wishlist.user_id IS 'ID del usuario propietario de la wishlist';
COMMENT ON COLUMN wishlist.product_id IS 'ID del producto en la wishlist';
COMMENT ON COLUMN wishlist.created_at IS 'Fecha cuando se agregó a favoritos';
