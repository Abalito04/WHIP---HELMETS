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
    console.log('=== CARGANDO PRODUCTOS ===');
    console.log('loadProducts llamado');
    console.log('API_BASE:', API_BASE);
    
    try {
        showLoading(productsGrid, "Cargando cascos...");
        showLoading(accessoriesGrid, "Cargando accesorios...");
        
        const response = await fetch(`${API_BASE}/api/products`);
        console.log('Respuesta de la API:', response.status);
        
        if (!response.ok) throw new Error("Error al cargar productos");
        
        products = await response.json();
        console.log('Productos cargados:', products.length);
        console.log('Detalles de productos:', products.map(p => ({ id: p.id, name: p.name, image: p.image, images: p.images })));
        renderProducts();
    } catch (error) {
        console.error("Error:", error);
        showError(productsGrid, "Error al cargar los productos. Por favor, recarga la página.");
        showError(accessoriesGrid, "Error al cargar los accesorios. Por favor, recarga la página.");
    }
}


// Función para mostrar estado de carga
function showLoading(container, message) {
    container.innerHTML = `
        <div class="loading-message">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

// Función para mostrar error
function showError(container, message) {
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

// Función para renderizar productos
function renderProducts() {
    console.log('renderProducts llamado');
    console.log('products:', products);
    console.log('productsGrid:', productsGrid);
    
    // Limpiar contenedores
    productsGrid.innerHTML = "";
    accessoriesGrid.innerHTML = "";
    
    // Separar productos por categoría
    const helmets = products.filter(p => 
        (p.category === "Cascos" || p.category === "cascos" || p.category === "CASCO") && 
        p.status === "Activo"
    );
    console.log('helmets encontrados:', helmets);
    console.log('Todos los productos:', products.map(p => ({ id: p.id, name: p.name, category: p.category, status: p.status })));
    const accessories = products.filter(p => 
        (p.category === "Accesorios" || p.category === "accesorios" || p.category === "ACCESORIOS") && 
        p.status === "Activo"
    );
    console.log('accessories encontrados:', accessories);
    
    // Renderizar cascos
    if (helmets.length === 0) {
        productsGrid.innerHTML = '<div class="no-products">No hay cascos disponibles en este momento.</div>';
    } else {
        helmets.forEach((product, index) => {
            const productCard = createProductCard(product);
            // Agregar delay escalonado para animación
            productCard.style.animationDelay = `${index * 0.1}s`;
            productsGrid.appendChild(productCard);
        });
    }
    
    // Renderizar accesorios
    if (accessories.length === 0) {
        accessoriesGrid.innerHTML = '<div class="no-products">No hay accesorios disponibles en este momento.</div>';
    } else {
        accessories.forEach((product, index) => {
            const productCard = createProductCard(product);
            // Agregar delay escalonado para animación
            productCard.style.animationDelay = `${index * 0.1}s`;
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
    
    // Crear imágenes (usar imagen principal como prioridad, sino primera de la galería)
    let imageUrl;
    if (product.image) {
        imageUrl = product.image; // Usar la imagen principal (prioridad)
    } else if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        imageUrl = product.images[0]; // Fallback: primera imagen de la galería
    } else {
        imageUrl = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+";
    }
    
    // Formatear precios - Sistema de dos precios
    const listPrice = product.price; // Precio de lista
    const formattedListPrice = '$' + new Intl.NumberFormat('es-ES').format(listPrice);
    
    // Calcular precio efectivo/transferencia (siempre aplicando descuento si existe)
    const discountPercentage = product.porcentaje_descuento || 0;
    const discountAmount = listPrice * (discountPercentage / 100);
    const effectivePrice = listPrice - discountAmount;
        const formattedEffectivePrice = '$' + new Intl.NumberFormat('es-ES').format(Math.round(effectivePrice));
    
    // Mostrar precios al estilo Pachamama Bike Shop
    const priceDisplay = `
            <div class="price-container">
            <p class="price effective-price">${formattedEffectivePrice}<br><span class="payment-method">Efectivo/Transferencia</span></p>
            ${discountPercentage > 0 ? `<p class="discount-badge">-${discountPercentage}% OFF</p>` : ''}
            </div>
        <p class="price list-price-outside">${formattedListPrice} Precio Lista</p>
        `;
    
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
    
    // Información de condición
    const condition = product.condition || 'Nuevo';
    const conditionDisplay = `<div class="product-condition">
        <span class="condition-badge ${condition === 'Nuevo' ? 'new' : 'used'}">${condition}</span>
    </div>`;
    
    card.innerHTML = `
        <div class="product-content">
        <div class="product-images-container">
            <img src="${imageUrl}" alt="${product.name}" class="product-image main-view" onclick="openProductGallery(${product.id}, '${product.name}')" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+'">
        </div>
            <div class="product-info">
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
            </div>
        </div>
        <div class="product-actions">
        <button class="add-to-cart-btn" data-product-id="${product.id}" ${isOutOfStock ? 'disabled' : ''}>
            ${isOutOfStock ? 'Sin stock' : 'Añadir al Carrito'}
        </button>
        </div>
    `;
    
    return card;
}

// Función para actualizar contador del carrito
function updateCartCount() {
    if (cartCountEl) {
        cartCountEl.textContent = `Carrito (${cart.length})`;
    }
    
    if (miniCartCount) {
        miniCartCount.textContent = cart.length;
    }
}


// Función para mostrar notificación
function showMiniNotification(message, type = 'success') {
    const notification = document.createElement("div");
    notification.textContent = message;
    
    // Colores según el tipo
    let backgroundColor, textColor;
    if (type === 'success') {
        backgroundColor = '#28a745';
        textColor = '#fff';
    } else if (type === 'error') {
        backgroundColor = '#dc3545';
        textColor = '#fff';
    } else if (type === 'info') {
        backgroundColor = '#17a2b8';
        textColor = '#fff';
    } else {
        backgroundColor = '#f0ad4e';
        textColor = '#000';
    }
    
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${backgroundColor};
        color: ${textColor};
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        font-weight: bold;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = "0";
        notification.style.transition = "opacity 0.5s";
        setTimeout(() => notification.remove(), 500);
    }, 3000);
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
    
    // Inicializar filtros solo para la sección de cascos
    initBrandFilter();
}

// Función para inicializar los filtros (solo para la sección de cascos)
function initBrandFilter() {
    // Obtener marcas solo de productos de cascos
    const helmetProducts = products.filter(p => 
        (p.category === "Cascos" || p.category === "cascos" || p.category === "CASCO") && 
        p.status === "Activo"
    );
    const brands = Array.from(new Set(helmetProducts.map(p => p.brand))).filter(b => b);
    if (brands.length === 0) return;
    
    const filterContainer = document.createElement("div");
    filterContainer.id = "product-filters";
    filterContainer.style.cssText = "text-align:center;margin:20px auto;display:flex;justify-content:center;align-items:center;gap:15px;flex-wrap:wrap;max-width:1200px;";

    // Filtro de marcas
    const brandLabel = document.createElement("span");
    brandLabel.textContent = "Marca:";
    brandLabel.style.color = "#fff";
    brandLabel.style.fontWeight = "bold";

    const brandSelect = document.createElement("select");
    brandSelect.id = "brand-select";
    brandSelect.style.cssText = "padding:8px;border-radius:5px;border:none;background:#fff;color:#333;font-size:14px;min-width:150px;";

    const allBrandOption = document.createElement("option");
    allBrandOption.value = "Todas";
    allBrandOption.textContent = "Todas las marcas";
    brandSelect.appendChild(allBrandOption);

    brands.forEach(brand => {
        const option = document.createElement("option");
        option.value = brand;
        option.textContent = brand;
        brandSelect.appendChild(option);
    });

    // Filtro de condición
    const conditionLabel = document.createElement("span");
    conditionLabel.textContent = "Condición:";
    conditionLabel.style.color = "#fff";
    conditionLabel.style.fontWeight = "bold";

    const conditionSelect = document.createElement("select");
    conditionSelect.id = "condition-select";
    conditionSelect.style.cssText = "padding:8px;border-radius:5px;border:none;background:#fff;color:#333;font-size:14px;min-width:120px;";

    const allConditionOption = document.createElement("option");
    allConditionOption.value = "Todas";
    allConditionOption.textContent = "Todas";
    conditionSelect.appendChild(allConditionOption);

    const newOption = document.createElement("option");
    newOption.value = "Nuevo";
    newOption.textContent = "Nuevo";
    conditionSelect.appendChild(newOption);

    const usedOption = document.createElement("option");
    usedOption.value = "Usado";
    usedOption.textContent = "Usado";
    conditionSelect.appendChild(usedOption);

    // Filtro de talles
    const sizeLabel = document.createElement("span");
    sizeLabel.textContent = "Talle:";
    sizeLabel.style.color = "#fff";
    sizeLabel.style.fontWeight = "bold";

    const sizeSelect = document.createElement("select");
    sizeSelect.id = "size-select";
    sizeSelect.style.cssText = "padding:8px;border-radius:5px;border:none;background:#fff;color:#333;font-size:14px;min-width:120px;";

    const allSizeOption = document.createElement("option");
    allSizeOption.value = "Todos";
    allSizeOption.textContent = "Todos los talles";
    sizeSelect.appendChild(allSizeOption);

    // Obtener todos los talles únicos solo de los productos de cascos
    const allSizes = new Set();
    helmetProducts.forEach(product => {
        if (product.sizes && Array.isArray(product.sizes)) {
            product.sizes.forEach(size => allSizes.add(size.trim()));
        }
    });
    
    // Ordenar talles de manera inteligente (S, M, L, XL, XXL, etc.)
    const sortedSizes = Array.from(allSizes).sort((a, b) => {
        const sizeOrder = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'];
        const aIndex = sizeOrder.indexOf(a.toUpperCase());
        const bIndex = sizeOrder.indexOf(b.toUpperCase());
        
        if (aIndex !== -1 && bIndex !== -1) {
            return aIndex - bIndex;
        }
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        
        // Si no está en la lista, ordenar alfabéticamente
        return a.localeCompare(b);
    });

    sortedSizes.forEach(size => {
        const option = document.createElement("option");
        option.value = size;
        option.textContent = size;
        sizeSelect.appendChild(option);
    });

    // Filtro de ordenamiento por precio
    const sortLabel = document.createElement("span");
    sortLabel.textContent = "Ordenar por precio:";
    sortLabel.style.color = "#fff";
    sortLabel.style.fontWeight = "bold";

    const sortSelect = document.createElement("select");
    sortSelect.id = "price-sort";
    sortSelect.style.cssText = "padding:8px;border-radius:5px;border:none;background:#fff;color:#333;font-size:14px;min-width:150px;";

    const defaultSortOption = document.createElement("option");
    defaultSortOption.value = "default";
    defaultSortOption.textContent = "Sin ordenar";
    sortSelect.appendChild(defaultSortOption);

    const priceAscOption = document.createElement("option");
    priceAscOption.value = "price-asc";
    priceAscOption.textContent = "Precio: Menor a Mayor";
    sortSelect.appendChild(priceAscOption);

    const priceDescOption = document.createElement("option");
    priceDescOption.value = "price-desc";
    priceDescOption.textContent = "Precio: Mayor a Menor";
    sortSelect.appendChild(priceDescOption);

    // Crear wrappers para cada par de filtros
    const brandWrapper = document.createElement("div");
    brandWrapper.className = "filter-group";
    brandWrapper.appendChild(brandLabel);
    brandWrapper.appendChild(brandSelect);
    
    const conditionWrapper = document.createElement("div");
    conditionWrapper.className = "filter-group";
    conditionWrapper.appendChild(conditionLabel);
    conditionWrapper.appendChild(conditionSelect);
    
    const sizeWrapper = document.createElement("div");
    sizeWrapper.className = "filter-group";
    sizeWrapper.appendChild(sizeLabel);
    sizeWrapper.appendChild(sizeSelect);
    
    const sortWrapper = document.createElement("div");
    sortWrapper.className = "filter-group";
    sortWrapper.appendChild(sortLabel);
    sortWrapper.appendChild(sortSelect);
    
    // Agregar wrappers al contenedor
    filterContainer.appendChild(brandWrapper);
    filterContainer.appendChild(conditionWrapper);
    filterContainer.appendChild(sizeWrapper);
    filterContainer.appendChild(sortWrapper);
    
    // Insertar el filtro antes de la sección de productos
    const productosSection = document.getElementById("destacados");
    if (productosSection && productosSection.parentNode) {
        productosSection.parentNode.insertBefore(filterContainer, productosSection);
    }

    // Event listeners para los filtros
    brandSelect.addEventListener("change", applyProductFilters);
    conditionSelect.addEventListener("change", applyProductFilters);
    sizeSelect.addEventListener("change", applyProductFilters);
    sortSelect.addEventListener("change", applyProductFilters);
}

// Función para aplicar todos los filtros
function applyProductFilters() {
    const brandFilter = document.getElementById("brand-select")?.value || "Todas";
    const conditionFilter = document.getElementById("condition-select")?.value || "Todas";
    const sizeFilter = document.getElementById("size-select")?.value || "Todos";
    const sortFilter = document.getElementById("price-sort")?.value || "default";
    
    // Solo obtener las tarjetas de la sección de cascos (destacados)
    const productsGrid = document.getElementById("destacados");
    if (!productsGrid) return;
    
    const productCards = productsGrid.querySelectorAll(".product-card");
    
    // Filtrar productos
    let filteredProducts = Array.from(productCards).filter(card => {
        const cardBrand = card.dataset.brand;
        const cardCondition = card.querySelector(".condition-badge")?.textContent;
        const productId = card.dataset.id;
        
        // Filtro por marca
        const brandMatch = brandFilter === "Todas" || cardBrand === brandFilter;
        
        // Filtro por condición
        const conditionMatch = conditionFilter === "Todas" || cardCondition === conditionFilter;
        
        // Filtro por talla
        let sizeMatch = true;
        if (sizeFilter !== "Todos") {
            const product = products.find(p => p.id == productId);
            if (product && product.sizes) {
                sizeMatch = product.sizes.some(size => size.trim() === sizeFilter);
            } else {
                sizeMatch = false;
            }
        }
        
        return brandMatch && conditionMatch && sizeMatch;
    });
    
    // Ordenar por precio si se selecciona
    if (sortFilter !== "default") {
        filteredProducts.sort((a, b) => {
            const priceA = getProductPrice(a);
            const priceB = getProductPrice(b);
            
            if (sortFilter === "price-asc") {
                return priceA - priceB;
            } else if (sortFilter === "price-desc") {
                return priceB - priceA;
            }
            return 0;
        });
    }
    
    // Ocultar todos los productos primero
    productCards.forEach(card => {
        card.style.display = "none";
    });
    
    // Mostrar solo los productos filtrados
    filteredProducts.forEach(card => {
        card.style.display = "block";
    });
    
    // Reorganizar el grid para mantener el orden
    if (sortFilter !== "default") {
        filteredProducts.forEach(card => {
            productsGrid.appendChild(card);
        });
    }
    
    // Forzar recálculo del grid para mantener alturas uniformes
    setTimeout(() => {
        if (brandFilter === "Todas" && conditionFilter === "Todas" && sizeFilter === "Todos") {
            // Si no hay filtros activos, resetear alturas
            resetGridHeights();
        } else {
            // Si hay filtros activos, recalcular alturas
            recalculateGridHeights();
        }
    }, 10);
}

// Función para recalcular las alturas del grid después de filtrar
function recalculateGridHeights() {
    // Solo recalcular alturas para la sección de cascos
    const productsGrid = document.getElementById("destacados");
    if (!productsGrid) return;
    
    const productCards = productsGrid.querySelectorAll(".product-card");
    const visibleCards = Array.from(productCards).filter(card => 
        card.style.display !== "none" && card.offsetParent !== null
    );
    
    if (visibleCards.length === 0) return;
    
    // Encontrar la altura máxima de las tarjetas visibles
    let maxHeight = 0;
    visibleCards.forEach(card => {
        // Resetear altura para obtener la altura natural
        card.style.height = "auto";
        const cardHeight = card.offsetHeight;
        if (cardHeight > maxHeight) {
            maxHeight = cardHeight;
        }
    });
    
    // Aplicar la altura máxima a todas las tarjetas visibles
    visibleCards.forEach(card => {
        card.style.height = maxHeight + "px";
    });
    
    // Asegurar que los botones estén alineados
    alignButtonsInCards(visibleCards);
}

// Función para alinear botones dentro de las tarjetas
function alignButtonsInCards(cards) {
    cards.forEach(card => {
        const actionsContainer = card.querySelector('.product-actions');
        if (actionsContainer) {
            // Asegurar que el contenedor de acciones esté en la parte inferior
            actionsContainer.style.marginTop = 'auto';
        }
    });
}

// Función para resetear las alturas del grid cuando no hay filtros
function resetGridHeights() {
    // Solo resetear alturas para la sección de cascos
    const productsGrid = document.getElementById("destacados");
    if (!productsGrid) return;
    
    const productCards = productsGrid.querySelectorAll(".product-card");
    
    productCards.forEach(card => {
        // Resetear altura para que use la altura natural del CSS
        card.style.height = "auto";
    });
    
    // Asegurar que los botones estén alineados
    alignButtonsInCards(Array.from(productCards));
}

// Función auxiliar para obtener el precio de un producto
function getProductPrice(card) {
    // Buscar precio efectivo (siempre presente ahora)
    const effectivePriceElement = card.querySelector(".effective-price");
    if (effectivePriceElement) {
        const priceText = effectivePriceElement.textContent.replace(/[^\d]/g, "");
        return parseInt(priceText) || 0;
    }
    
    // Fallback: buscar precio normal (por compatibilidad)
    const priceElement = card.querySelector(".price");
    if (priceElement) {
        const priceText = priceElement.textContent.replace(/[^\d]/g, "");
        return parseInt(priceText) || 0;
    }
    
    return 0;
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
    console.log('=== CARGANDO IMÁGENES DEL PRODUCTO (PÁGINA PRINCIPAL) ===');
    console.log('loadProductImages llamado para producto:', productId);
    
    try {
        // Primero intentar cargar desde la API para obtener datos actualizados
        const response = await fetch(`${API_BASE}/api/products/${productId}`);
        console.log('Respuesta de la API:', response.status);
        
        if (response.ok) {
            const product = await response.json();
            console.log('Producto cargado desde API:', product);
            
            // Crear array de imágenes con la imagen principal como primera
            currentGalleryImages = [];
            
            // Agregar imagen principal como primera
            if (product.image && product.image.trim() !== '') {
                currentGalleryImages.push(product.image);
                console.log('Imagen principal agregada:', product.image);
            }
            
            // Agregar imágenes adicionales de la galería (sin duplicar la principal)
            if (product.images && Array.isArray(product.images) && product.images.length > 0) {
                product.images.forEach((img, index) => {
                    if (img && img.trim() !== '' && img !== product.image) { // Evitar duplicar la imagen principal
                        currentGalleryImages.push(img);
                        console.log(`Imagen adicional ${index} agregada:`, img);
                    }
                });
                console.log('Total de imágenes adicionales agregadas:', product.images.length);
            }
            
            console.log('Galería final:', currentGalleryImages);
        } else {
            console.log('No se pudo cargar desde API, usando datos locales');
            // Fallback: buscar el producto en la lista cargada
            const product = products.find(p => p.id == productId);
            console.log('Producto encontrado en datos locales:', product);
            
            if (product) {
                currentGalleryImages = [];
                
                // Agregar imagen principal
                if (product.image && product.image.trim() !== '') {
                    currentGalleryImages.push(product.image);
                    console.log('Imagen principal (local) agregada:', product.image);
                }
                
                // Agregar imágenes adicionales
                if (product.images && Array.isArray(product.images) && product.images.length > 0) {
                    product.images.forEach((img, index) => {
                        if (img && img.trim() !== '' && img !== product.image) {
                            currentGalleryImages.push(img);
                            console.log(`Imagen adicional ${index} (local) agregada:`, img);
                        }
                    });
                }
                
                console.log('Galería final (local):', currentGalleryImages);
            } else {
                console.log('Producto no encontrado en datos locales');
                currentGalleryImages = [];
            }
        }
        
        console.log('Imágenes a mostrar en galería:', currentGalleryImages);
        renderGallery();
    } catch (error) {
        console.error('Error al cargar imágenes:', error);
            currentGalleryImages = [];
        renderGallery();
    }
}

function renderGallery() {
    console.log('Renderizando galería con', currentGalleryImages.length, 'imágenes');
    
    if (currentGalleryImages.length === 0) {
        console.log('No hay imágenes para mostrar');
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
    
    console.log('Creando miniaturas para', currentGalleryImages.length, 'imágenes');
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
    const prevBtnBottom = document.getElementById('gallery-prev-bottom');
    const nextBtnBottom = document.getElementById('gallery-next-bottom');
    
    // Con navegación circular, los botones nunca se deshabilitan
    // Solo se deshabilitan si hay menos de 2 imágenes
    const hasMultipleImages = currentGalleryImages.length > 1;
    
    if (prevBtn) prevBtn.disabled = !hasMultipleImages;
    if (nextBtn) nextBtn.disabled = !hasMultipleImages;
    if (prevBtnBottom) prevBtnBottom.disabled = !hasMultipleImages;
    if (nextBtnBottom) nextBtnBottom.disabled = !hasMultipleImages;
}

function closeGallery() {
    document.getElementById('gallery-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
    currentGalleryProduct = null;
    currentGalleryImages = [];
    selectedImageIndex = 0;
}

function navigateGallery(direction) {
    if (direction === 'prev') {
        if (selectedImageIndex > 0) {
        selectedImageIndex--;
        } else {
            // Si estamos en la primera imagen, ir a la última
            selectedImageIndex = currentGalleryImages.length - 1;
        }
    } else if (direction === 'next') {
        if (selectedImageIndex < currentGalleryImages.length - 1) {
        selectedImageIndex++;
        } else {
            // Si estamos en la última imagen, ir a la primera
            selectedImageIndex = 0;
        }
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
    const prevBtnBottom = document.getElementById('gallery-prev-bottom');
    const nextBtnBottom = document.getElementById('gallery-next-bottom');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => navigateGallery('prev'));
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => navigateGallery('next'));
    }
    
    if (prevBtnBottom) {
        prevBtnBottom.addEventListener('click', () => navigateGallery('prev'));
    }
    
    if (nextBtnBottom) {
        nextBtnBottom.addEventListener('click', () => navigateGallery('next'));
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
    
    // Asegurar que las alturas estén correctas después de cargar los productos
    setTimeout(() => {
        resetGridHeights();
    }, 100);
});