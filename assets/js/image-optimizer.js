/**
 * Módulo para optimización de imágenes
 * Maneja lazy loading, responsive images y fallbacks
 */

class ImageOptimizer {
    constructor() {
        this.observer = null;
        this.initIntersectionObserver();
    }

    /**
     * Inicializa el Intersection Observer para lazy loading
     */
    initIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });
        }
    }

    /**
     * Crea un elemento de imagen optimizada
     * @param {string} imagePath - Ruta base de la imagen
     * @param {string} alt - Texto alternativo
     * @param {string} className - Clases CSS
     * @returns {HTMLElement} - Elemento img optimizado
     */
    createOptimizedImage(imagePath, alt = '', className = '') {
        const img = document.createElement('img');
        
        // Configurar atributos básicos
        img.alt = alt;
        img.className = className;
        img.loading = 'lazy';
        
        // Detectar soporte para WebP
        const supportsWebP = this.supportsWebP();
        
        // Generar rutas de imagen optimizadas
        const baseName = imagePath.replace(/\.(png|jpg|jpeg)$/i, '');
        const optimizedPath = baseName.replace('/products/', '/products/optimized/');
        
        // Crear srcset para responsive images
        const srcset = this.generateSrcset(optimizedPath, supportsWebP);
        
        // Configurar imagen
        if (srcset) {
            img.srcset = srcset;
            img.sizes = '(max-width: 480px) 300px, (max-width: 768px) 600px, 800px';
        }
        
        // Fallback para navegadores que no soportan srcset
        img.src = this.getFallbackImage(optimizedPath, supportsWebP);
        
        // Agregar placeholder mientras carga
        this.addPlaceholder(img);
        
        // Configurar lazy loading
        if (this.observer) {
            this.observer.observe(img);
        } else {
            // Fallback para navegadores sin IntersectionObserver
            this.loadImage(img);
        }
        
        return img;
    }

    /**
     * Genera srcset para responsive images
     * @param {string} basePath - Ruta base de la imagen
     * @param {boolean} supportsWebP - Si el navegador soporta WebP
     * @returns {string} - Srcset string
     */
    generateSrcset(basePath, supportsWebP) {
        const extension = supportsWebP ? 'webp' : 'png';
        const sizes = [
            { suffix: 'small', width: 300 },
            { suffix: 'medium', width: 600 },
            { suffix: 'large', width: 800 }
        ];
        
        return sizes.map(size => 
            `${basePath}_${size.suffix}.${extension} ${size.width}w`
        ).join(', ');
    }

    /**
     * Obtiene imagen de fallback
     * @param {string} basePath - Ruta base
     * @param {boolean} supportsWebP - Soporte WebP
     * @returns {string} - Ruta de imagen de fallback
     */
    getFallbackImage(basePath, supportsWebP) {
        const extension = supportsWebP ? 'webp' : 'png';
        return `${basePath}_medium.${extension}`;
    }

    /**
     * Detecta soporte para WebP
     * @returns {boolean} - True si soporta WebP
     */
    supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    /**
     * Agrega placeholder mientras la imagen carga
     * @param {HTMLElement} img - Elemento imagen
     */
    addPlaceholder(img) {
        // Placeholder SVG
        const placeholder = `data:image/svg+xml;base64,${btoa(`
            <svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f0f0f0"/>
                <text x="50%" y="50%" font-family="Arial" font-size="14" fill="#999" text-anchor="middle" dy=".3em">
                    Cargando...
                </text>
            </svg>
        `)}`;
        
        img.src = placeholder;
        img.style.opacity = '0.7';
        img.style.transition = 'opacity 0.3s ease';
    }

    /**
     * Carga la imagen real
     * @param {HTMLElement} img - Elemento imagen
     */
    loadImage(img) {
        const realSrc = img.dataset.src || img.srcset?.split(',')[0]?.split(' ')[0];
        
        if (realSrc) {
            const tempImg = new Image();
            tempImg.onload = () => {
                img.src = realSrc;
                img.style.opacity = '1';
            };
            tempImg.onerror = () => {
                // Fallback a imagen original si la optimizada falla
                const originalPath = img.src.replace('/optimized/', '/').replace('.webp', '.png');
                img.src = originalPath;
                img.style.opacity = '1';
            };
            tempImg.src = realSrc;
        }
    }

    /**
     * Optimiza todas las imágenes existentes en el DOM
     */
    optimizeExistingImages() {
        const images = document.querySelectorAll('img[data-optimize]');
        images.forEach(img => {
            const imagePath = img.dataset.optimize;
            const alt = img.alt || '';
            const className = img.className || '';
            
            const optimizedImg = this.createOptimizedImage(imagePath, alt, className);
            img.parentNode.replaceChild(optimizedImg, img);
        });
    }

    /**
     * Preload imágenes críticas
     * @param {Array} criticalImages - Array de rutas de imágenes críticas
     */
    preloadCriticalImages(criticalImages) {
        criticalImages.forEach(imagePath => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = this.getFallbackImage(imagePath, this.supportsWebP());
            document.head.appendChild(link);
        });
    }
}

// Exportar para uso global
window.ImageOptimizer = ImageOptimizer;

// Auto-inicializar si el DOM está listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.imageOptimizer = new ImageOptimizer();
    });
} else {
    window.imageOptimizer = new ImageOptimizer();
}
