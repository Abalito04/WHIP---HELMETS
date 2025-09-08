// shop.js
// Configuración dinámica de la API
const API_BASE = (() => {
    // Si estamos en Railway (producción), usar la URL actual
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return window.location.origin;
    }
    // Si estamos en desarrollo local
    return "http://127.0.0.1:5000";
})();

console.log("API_BASE configurado como:", API_BASE);

// Variables globales
let products = [];
let cart = JSON.parse(localStorage.getItem("cart_v1")) || [];

// Elementos DOM
const productsGrid = document.getElementById("destacados");
const accessoriesGrid = document.getElementById("accesorios");
const cartCountEl = document.querySelector(".cart");
const miniCartCount = document.getElementById("mini-cart-count");

// Función para cargar productos desde la API
async function loadProducts() {
    try {
        showLoading(productsGrid, "Cargando cascos...");
        showLoading(accessoriesGrid, "Cargando accesorios...");
        
        const response = await fetch(`${API_BASE}/api/products`);
        if (!response.ok) throw new Error("Error al cargar productos");
        
        products = await response.json();
        renderProducts();
    } catch (error) {
        console.error("Error:", error);
        showError(productsGrid, "Error al cargar los productos. Por favor, recarga la página.");
        showError(accessoriesGrid, "Error al cargar los accesorios. Por favor, recarga la página.");
    }
}

// Función para mostrar estado de carga
function showLoading(container, message) {
    container.innerHTML = `<div class="loading-message">${message}</div>`;
}

// Función para mostrar error
function showError(container, message) {
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

// Función para renderizar productos
function renderProducts() {
    // Limpiar contenedores
    productsGrid.innerHTML = "";
    accessoriesGrid.innerHTML = "";
    
    // Separar productos por categoría
    const helmets = products.filter(p => p.category === "Cascos" && p.status === "Activo");
    const accessories = products.filter(p => p.category === "Accesorios" && p.status === "Activo");
    
    // Renderizar cascos
    if (helmets.length === 0) {
        productsGrid.innerHTML = '<div class="no-products">No hay cascos disponibles en este momento.</div>';
    } else {
        helmets.forEach(product => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });
    }
    
    // Renderizar accesorios
    if (accessories.length === 0) {
        accessoriesGrid.innerHTML = '<div class="no-products">No hay accesorios disponibles en este momento.</div>';
    } else {
        accessories.forEach(product => {
            const productCard = createProductCard(product);
            accessoriesGrid.appendChild(productCard);
        });
    }
    
    // Actualizar contador del carrito
    updateCartCount();
    
    // Inicializar eventos para los nuevos botones
    initProductEvents();
    
    // Inicializar la UI de stock después de renderizar
    setTimeout(initializeStockUI, 100);
    
    // Optimizar imágenes después de renderizar productos (comentado temporalmente)
    // setTimeout(() => {
    //     if (window.imageOptimizer) {
    //         window.imageOptimizer.optimizeExistingImages();
    //     }
    // }, 200);
}

// Función para crear tarjeta de producto
function createProductCard(product) {
    const card = document.createElement("div");
    card.className = "product-card";
    card.dataset.brand = product.brand;
    card.dataset.id = product.id;
    
    // Crear imágenes (usar imagen por defecto si no hay)
    const imageUrl = product.image || "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+";
    
    // Formatear precios
    const formattedPrice = '$' + new Intl.NumberFormat('es-ES').format(product.price);
    const hasDiscount = product.porcentaje_descuento && product.porcentaje_descuento > 0;
    let priceDisplay = '';
    
    if (hasDiscount) {
        const discountAmount = product.price * (product.porcentaje_descuento / 100);
        const effectivePrice = product.price - discountAmount;
        const formattedEffectivePrice = '$' + new Intl.NumberFormat('es-ES').format(Math.round(effectivePrice));
        priceDisplay = `
            <div class="price-container">
                <p class="price original-price">${formattedPrice}</p>
                <p class="price effective-price">${formattedEffectivePrice}</p>
                <p class="discount-badge">-${product.porcentaje_descuento}%</p>
            </div>
        `;
    } else {
        priceDisplay = `<p class="price">${formattedPrice}</p>`;
    }
    
    // Determinar estado del stock
    const stock = product.stock || 0;
    const isOutOfStock = stock <= 0;
    const lowStock = stock > 0 && stock <= 5;
    
    // Clases CSS según stock
    let stockClass = "stock-high";
    let stockText = `Stock: ${stock}`;
    
    if (isOutOfStock) {
        stockClass = "stock-out";
        stockText = "Sin stock";
    } else if (lowStock) {
        stockClass = "stock-low";
        stockText = `Stock: ${stock}`;
    }
    
    // Información de condición y grado
    const condition = product.condition || 'Nuevo';
    const grade = product.grade || '';
    const conditionDisplay = condition === 'Usado' && grade ? 
        `<div class="product-condition">
            <span class="condition-badge used">${condition}</span>
            <span class="grade-badge">${grade}</span>
        </div>` : 
        `<div class="product-condition">
            <span class="condition-badge new">${condition}</span>
        </div>`;

    card.innerHTML = `
        <div class="product-images-container">
            <img src="${imageUrl}" alt="${product.name}" class="product-image main-view" onclick="openProductGallery(${product.id}, '${product.name}')" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+'">
            <button class="gallery-btn" onclick="openProductGallery(${product.id}, '${product.name}')" title="Ver galería">📷</button>
        </div>
        <h3>${product.name}</h3>
        ${conditionDisplay}
        ${priceDisplay}
        <p class="stock ${stockClass}">${stockText}</p>
        <div class="product-options">
            <label for="talles-${product.id}">Talle:</label>
            <select id="talles-${product.id}" class="size-selector" ${isOutOfStock ? 'disabled' : ''}>
                ${product.sizes.map(size => `<option value="${size}">${size}</option>`).join('')}
            </select>
        </div>
        <button class="add-to-cart-btn" data-product-id="${product.id}" ${isOutOfStock ? 'disabled' : ''}>
            ${isOutOfStock ? 'Sin stock' : 'Añadir al Carrito'}
        </button>
    `;
    
    return card;
}

// Función para actualizar contador del carrito
function updateCartCount() {
    if (cartCountEl) {
        cartCountEl.textContent = `🛒 Carrito (${cart.length})`;
    }
    
    if (miniCartCount) {
        miniCartCount.textContent = cart.length;
    }
}

// Función para mostrar notificación
function showMiniNotification(message) {
    const notification = document.createElement("div");
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #f0ad4e;
        color: #000;
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = "0";
        notification.style.transition = "opacity 0.5s";
        setTimeout(() => notification.remove(), 500);
    }, 2000);
}

// Función para inicializar eventos para productos
function initProductEvents() {
    // Manejar clic en botón "Añadir al Carrito"
    document.querySelectorAll(".add-to-cart-btn").forEach(button => {
        button.addEventListener("click", function(e) {
            const productId = this.dataset.productId;
            const sizeSelector = document.getElementById(`talles-${productId}`);
            const size = sizeSelector ? sizeSelector.value : "Único";
            const product = products.find(p => p.id == productId);
            
            if (product) {
                // Calcular precio efectivo si hay descuento
                let priceToUse = product.price;
                if (product.porcentaje_descuento && product.porcentaje_descuento > 0) {
                    const discountAmount = product.price * (product.porcentaje_descuento / 100);
                    priceToUse = product.price - discountAmount;
                }
                
                // Usar la función global para agregar al carrito
                window.addToCart(product.name, priceToUse, size, productId);
            }
        });
    });
    
    // Manejar cambio de talla
    document.querySelectorAll(".size-selector").forEach(selector => {
        selector.addEventListener("change", function() {
            const productId = this.id.replace("talles-", "");
            const size = this.value;
            
            // Actualizar UI para la talla seleccionada
            window.updateProductStockUI(productId, size);
        });
    });
    
    // Aquí puedes agregar el filtro de marcas si lo necesitas
    initBrandFilter();
}

// Función para inicializar el filtro de marcas
function initBrandFilter() {
    const brands = Array.from(new Set(products.map(p => p.brand))).filter(b => b);
    if (brands.length === 0) return;
    
    const filterContainer = document.createElement("div");
    filterContainer.id = "brand-filter";
    filterContainer.style.cssText = "text-align:center;margin:20px 0;display:flex;justify-content:center;align-items:center;gap:10px;";

    const label = document.createElement("span");
    label.textContent = "Filtrar por marcas:";
    label.style.color = "#fff";

    const selectFilter = document.createElement("select");
    selectFilter.style.cssText = "padding:5px 10px;font-size:1em;";

    const allOption = document.createElement("option");
    allOption.value = "Todas";
    allOption.textContent = "Todas";
    selectFilter.appendChild(allOption);

    brands.forEach(brand => {
        const option = document.createElement("option");
        option.value = brand;
        option.textContent = brand;
        selectFilter.appendChild(option);
    });

    filterContainer.appendChild(label);
    filterContainer.appendChild(selectFilter);
    
    // Insertar el filtro antes de la sección de productos
    const productosSection = document.getElementById("destacados");
    if (productosSection && productosSection.parentNode) {
        productosSection.parentNode.insertBefore(filterContainer, productosSection);
    }

    selectFilter.addEventListener("change", () => {
        const selected = selectFilter.value;
        document.querySelectorAll(".product-card").forEach(card => {
            card.style.display = (selected === "Todas" || card.dataset.brand === selected) ? "block" : "none";
        });
    });
}

// Función para verificar stock disponible
window.checkStockAvailable = (productId, size) => {
    const product = products.find(p => p.id == productId);
    if (!product || product.stock <= 0) return false;
    
    // Contar cuántos de este producto ya están en el carrito
    const cart = JSON.parse(localStorage.getItem("cart_v1")) || [];
    const inCartCount = cart.filter(item => 
        item.productId == productId && item.size === size
    ).length;
    
    // Verificar si aún hay stock disponible
    return product.stock > inCartCount;
};

// Función para actualizar la UI de stock
window.updateProductStockUI = (productId, size) => {
    const product = products.find(p => p.id == productId);
    if (!product) return;
    
    // Contar cuántos de este producto ya están en el carrito
    const cart = JSON.parse(localStorage.getItem("cart_v1")) || [];
    const inCartCount = cart.filter(item => 
        item.productId == productId && item.size === size
    ).length;
    
    // Encontrar el elemento del producto en la UI
    const productElement = document.querySelector(`.product-card[data-id="${productId}"]`);
    if (!productElement) return;
    
    // Actualizar el texto de stock
    const stockElement = productElement.querySelector('.stock');
    const addButton = productElement.querySelector('.add-to-cart-btn');
    const sizeSelector = productElement.querySelector('.size-selector');
    
    const remainingStock = product.stock - inCartCount;
    
    if (remainingStock <= 0) {
        stockElement.textContent = "Sin stock";
        stockElement.className = "stock stock-out";
        addButton.disabled = true;
        addButton.textContent = "Sin stock";
        if (sizeSelector) sizeSelector.disabled = true;
    } else if (remainingStock <= 5) {
        stockElement.textContent = `¡Quedan ${remainingStock} unidad/es!`;
        stockElement.className = "stock stock-low";
        addButton.disabled = false;
        addButton.textContent = "Añadir al Carrito";
        if (sizeSelector) sizeSelector.disabled = false;
    } else {
        stockElement.textContent = `Stock: ${remainingStock}`;
        stockElement.className = "stock stock-high";
        addButton.disabled = false;
        addButton.textContent = "Añadir al Carrito";
        if (sizeSelector) sizeSelector.disabled = false;
    }
};

// Función para inicializar la UI de stock
function initializeStockUI() {
    const cart = JSON.parse(localStorage.getItem("cart_v1")) || [];
    
    products.forEach(product => {
        const productElement = document.querySelector(`.product-card[data-id="${product.id}"]`);
        if (!productElement) return;
        
        // Para cada talla del producto, verificar cuántos hay en el carrito
        const sizes = product.sizes || ["Único"];
        
        sizes.forEach(size => {
            const inCartCount = cart.filter(item => 
                item.productId == product.id && item.size === size
            ).length;
            
            // Si hay alguno en el carrito, actualizar la UI
            if (inCartCount > 0) {
                window.updateProductStockUI(product.id, size);
            }
        });
    });
}

// ==================== FUNCIONES DE GALERÍA ====================
let currentGalleryProduct = null;
let currentGalleryImages = [];
let selectedImageIndex = 0;

// Función para abrir la galería de un producto
window.openProductGallery = function(productId, productName) {
    currentGalleryProduct = productId;
    document.getElementById('gallery-title').textContent = `Galería - ${productName}`;
    
    // Cargar imágenes del producto
    loadProductImages(productId);
    
    // Mostrar modal
    document.getElementById('gallery-modal').style.display = 'block';
    
    // Prevenir scroll del body
    document.body.style.overflow = 'hidden';
};

async function loadProductImages(productId) {
    try {
        // Cargar imágenes reales desde la API
        const response = await fetch(`/api/products/${productId}/images`);
        if (response.ok) {
            const data = await response.json();
            currentGalleryImages = data.images || [];
        } else {
            // Fallback: usar solo la imagen principal del producto
            const product = products.find(p => p.id == productId);
            if (product && product.image) {
                currentGalleryImages = [product.image];
            } else {
                currentGalleryImages = [];
            }
        }
        
        renderGallery();
    } catch (error) {
        console.error('Error al cargar imágenes:', error);
        // Fallback: usar solo la imagen principal del producto
        const product = products.find(p => p.id == productId);
        if (product && product.image) {
            currentGalleryImages = [product.image];
        } else {
            currentGalleryImages = [];
        }
        renderGallery();
    }
}

function renderGallery() {
    if (currentGalleryImages.length === 0) {
        document.getElementById('gallery-main-img').src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgdmlld0JveD0iMCAwIDQwMCA0MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUwIDIwMEg0MDBWMzAwSDI1MFYyMEgyMDBWMjAwSDE1MFoiIGZpbGw9IiM5OTkiLz48L3N2Zz4=';
        document.getElementById('gallery-thumbnails').innerHTML = '<p style="text-align: center; color: #666;">No hay imágenes disponibles</p>';
        return;
    }
    
    // Mostrar imagen principal
    const mainImg = document.getElementById('gallery-main-img');
    const currentImage = currentGalleryImages[selectedImageIndex];
    
    // Manejar diferentes tipos de URLs
    if (currentImage.startsWith('http')) {
        // URL completa (Cloudinary)
        mainImg.src = currentImage;
    } else if (currentImage.startsWith('/')) {
        // Ruta absoluta
        mainImg.src = currentImage;
    } else {
        // Ruta relativa
        mainImg.src = `/${currentImage}`;
    }
    
    // Renderizar miniaturas
    const thumbnailsContainer = document.getElementById('gallery-thumbnails');
    thumbnailsContainer.innerHTML = '';
    
    currentGalleryImages.forEach((image, index) => {
        const thumbnail = document.createElement('img');
        
        // Manejar diferentes tipos de URLs para miniaturas
        if (image.startsWith('http')) {
            // URL completa (Cloudinary)
            thumbnail.src = image;
        } else if (image.startsWith('/')) {
            // Ruta absoluta
            thumbnail.src = image;
        } else {
            // Ruta relativa
            thumbnail.src = `/${image}`;
        }
        
        thumbnail.className = `gallery-thumbnail ${index === selectedImageIndex ? 'active' : ''}`;
        thumbnail.onclick = () => selectImage(index);
        thumbnail.onerror = () => {
            thumbnail.style.display = 'none';
        };
        thumbnailsContainer.appendChild(thumbnail);
    });
    
    // Actualizar botones de navegación
    updateNavigationButtons();
}

function selectImage(index) {
    selectedImageIndex = index;
    renderGallery();
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('gallery-prev');
    const nextBtn = document.getElementById('gallery-next');
    
    prevBtn.disabled = selectedImageIndex === 0;
    nextBtn.disabled = selectedImageIndex === currentGalleryImages.length - 1;
}

function closeGallery() {
    document.getElementById('gallery-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
    currentGalleryProduct = null;
    currentGalleryImages = [];
    selectedImageIndex = 0;
}

function navigateGallery(direction) {
    if (direction === 'prev' && selectedImageIndex > 0) {
        selectedImageIndex--;
    } else if (direction === 'next' && selectedImageIndex < currentGalleryImages.length - 1) {
        selectedImageIndex++;
    }
    renderGallery();
}

// Eventos de la galería
document.addEventListener('DOMContentLoaded', () => {
    // Cerrar galería
    const closeBtn = document.querySelector('.gallery-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeGallery);
    }
    
    // Cerrar al hacer clic fuera
    const galleryModal = document.getElementById('gallery-modal');
    if (galleryModal) {
        galleryModal.addEventListener('click', (e) => {
            if (e.target.id === 'gallery-modal') {
                closeGallery();
            }
        });
    }
    
    // Botones de navegación
    const prevBtn = document.getElementById('gallery-prev');
    const nextBtn = document.getElementById('gallery-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => navigateGallery('prev'));
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => navigateGallery('next'));
    }
    
    // Navegación con teclado
    document.addEventListener('keydown', (e) => {
        if (document.getElementById('gallery-modal').style.display === 'block') {
            if (e.key === 'Escape') {
                closeGallery();
            } else if (e.key === 'ArrowLeft') {
                navigateGallery('prev');
            } else if (e.key === 'ArrowRight') {
                navigateGallery('next');
            }
        }
    });
});

// Inicializar
document.addEventListener("DOMContentLoaded", function() {
    loadProducts();
    updateCartCount();
});