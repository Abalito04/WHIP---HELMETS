-- Migración para agregar la columna precio_efectivo a la tabla productos
-- Ejecutar este script en la base de datos de Railway

-- Verificar si la columna 'precio_efectivo' ya existe
DO $$
BEGIN
    -- Agregar la columna 'precio_efectivo' si no existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'productos' AND column_name = 'precio_efectivo'
    ) THEN
        -- Agregar la columna 'precio_efectivo'
        ALTER TABLE productos 
        ADD COLUMN precio_efectivo DECIMAL(10,2);
        
        -- Calcular precio_efectivo para productos existentes
        UPDATE productos 
        SET precio_efectivo = CASE 
            WHEN porcentaje_descuento IS NOT NULL AND porcentaje_descuento > 0 
            THEN price - (price * porcentaje_descuento / 100)
            ELSE price 
        END;
        
        RAISE NOTICE 'Columna precio_efectivo agregada y calculada para productos existentes';
    ELSE
        RAISE NOTICE 'La columna precio_efectivo ya existe en la tabla productos';
    END IF;
END $$;
