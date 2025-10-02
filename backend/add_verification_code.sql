-- Migración para agregar columna verification_code a la tabla orders
-- Ejecutar en Railway Database

-- Verificar si la columna ya existe antes de agregarla
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'orders' 
        AND column_name = 'verification_code'
    ) THEN
        -- Agregar la columna verification_code
        ALTER TABLE orders ADD COLUMN verification_code VARCHAR(20);
        
        -- Generar códigos de verificación para pedidos existentes
        UPDATE orders 
        SET verification_code = UPPER(SUBSTRING(MD5(order_number || EXTRACT(EPOCH FROM created_at)::text), 1, 8))
        WHERE verification_code IS NULL;
        
        RAISE NOTICE 'Columna verification_code agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna verification_code ya existe';
    END IF;
END $$;
