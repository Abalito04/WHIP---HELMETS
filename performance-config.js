/**
 * Configuración de Performance para WHIP HELMETS
 * Centraliza todas las configuraciones de optimización
 */

window.PerformanceConfig = {
    // Configuración de imágenes
    images: {
        // Tamaños de imagen para diferentes dispositivos
        sizes: {
            thumb: { width: 150, height: 150 },
            small: { width: 300, height: 300 },
            medium: { width: 600, height: 600 },
            large: { width: 800, height: 800 }
        },
        
        // Calidad de compresión WebP
        webpQuality: 85,
        
        // Lazy loading offset (píxeles)
        lazyLoadOffset: 50,
        
        // Placeholder color
        placeholderColor: '#f0f0f0'
    },
    
    // Configuración de caché
    cache: {
        // Tiempo de caché para recursos estáticos (en segundos)
        staticAssets: 86400, // 24 horas
        
        // Tiempo de caché para datos de productos (en segundos)
        productData: 300, // 5 minutos
        
        // Tiempo de caché para imágenes (en segundos)
        images: 604800 // 7 días
    },
    
    // Configuración de API
    api: {
        // Timeout para requests (en milisegundos)
        timeout: 10000,
        
        // Número máximo de reintentos
        maxRetries: 3,
        
        // Delay entre reintentos (en milisegundos)
        retryDelay: 1000
    },
    
    // Configuración de animaciones
    animations: {
        // Duración de transiciones (en milisegundos)
        transitionDuration: 300,
        
        // Usar animaciones reducidas si el usuario lo prefiere
        respectReducedMotion: true
    },
    
    // Configuración de notificaciones
    notifications: {
        // Duración de notificaciones (en milisegundos)
        duration: 3000,
        
        // Posición de notificaciones
        position: 'bottom-right'
    },
    
    // Configuración de carrito
    cart: {
        // Persistencia en localStorage
        storageKey: 'whip_helmets_cart_v2',
        
        // Máximo número de items en carrito
        maxItems: 50,
        
        // Auto-guardado cada X milisegundos
        autoSaveInterval: 5000
    },
    
    // Configuración de filtros
    filters: {
        // Debounce para búsqueda (en milisegundos)
        searchDebounce: 300,
        
        // Máximo número de productos por página
        itemsPerPage: 20
    },
    
    // Configuración de analytics
    analytics: {
        // Habilitar tracking de performance
        trackPerformance: true,
        
        // Habilitar tracking de errores
        trackErrors: true,
        
        // Habilitar tracking de interacciones
        trackInteractions: true
    }
};

// Función para obtener configuración
window.getPerformanceConfig = (key) => {
    const keys = key.split('.');
    let value = window.PerformanceConfig;
    
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return null;
        }
    }
    
    return value;
};

// Función para verificar preferencias de usuario
window.checkUserPreferences = () => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isSlowConnection = navigator.connection && 
        (navigator.connection.effectiveType === 'slow-2g' || 
         navigator.connection.effectiveType === '2g');
    
    return {
        prefersReducedMotion,
        prefersDarkMode,
        isSlowConnection
    };
};

// Función para optimizar basado en conexión
window.optimizeForConnection = () => {
    const prefs = window.checkUserPreferences();
    
    if (prefs.isSlowConnection) {
        // Reducir calidad de imágenes para conexiones lentas
        window.PerformanceConfig.images.webpQuality = 60;
        window.PerformanceConfig.images.lazyLoadOffset = 100;
        window.PerformanceConfig.api.timeout = 15000;
    }
    
    if (prefs.prefersReducedMotion) {
        // Deshabilitar animaciones si el usuario lo prefiere
        document.documentElement.style.setProperty('--transition-duration', '0ms');
    }
};

// Auto-ejecutar optimizaciones
document.addEventListener('DOMContentLoaded', () => {
    window.optimizeForConnection();
});
