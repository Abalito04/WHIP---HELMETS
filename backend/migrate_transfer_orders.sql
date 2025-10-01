-- migration_transfer_orders.sql

-- Agregar campos necesarios para pedidos de transferencia a la tabla orders
DO $$
BEGIN
    -- Agregar columna payment_method si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'payment_method') THEN
        ALTER TABLE orders
        ADD COLUMN payment_method VARCHAR(50) DEFAULT 'mercadopago';
        RAISE NOTICE 'Columna "payment_method" agregada a la tabla orders.';
    ELSE
        RAISE NOTICE 'La columna "payment_method" ya existe en la tabla orders.';
    END IF;

    -- Agregar columnas de dirección si no existen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'customer_address') THEN
        ALTER TABLE orders
        ADD COLUMN customer_address TEXT;
        RAISE NOTICE 'Columna "customer_address" agregada a la tabla orders.';
    ELSE
        RAISE NOTICE 'La columna "customer_address" ya existe en la tabla orders.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'customer_city') THEN
        ALTER TABLE orders
        ADD COLUMN customer_city VARCHAR(100);
        RAISE NOTICE 'Columna "customer_city" agregada a la tabla orders.';
    ELSE
        RAISE NOTICE 'La columna "customer_city" ya existe en la tabla orders.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'customer_zip') THEN
        ALTER TABLE orders
        ADD COLUMN customer_zip VARCHAR(10);
        RAISE NOTICE 'Columna "customer_zip" agregada a la tabla orders.';
    ELSE
        RAISE NOTICE 'La columna "customer_zip" ya existe en la tabla orders.';
    END IF;

    -- Agregar columna user_id si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'user_id') THEN
        ALTER TABLE orders
        ADD COLUMN user_id INTEGER;
        RAISE NOTICE 'Columna "user_id" agregada a la tabla orders.';
    ELSE
        RAISE NOTICE 'La columna "user_id" ya existe en la tabla orders.';
    END IF;

    -- Actualizar valores por defecto para payment_method
    UPDATE orders 
    SET payment_method = 'mercadopago' 
    WHERE payment_method IS NULL;
    
    RAISE NOTICE 'Valores por defecto actualizados para payment_method.';
END
$$;
