// shop.js
const API_BASE = "http://127.0.0.1:5000";

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
}

// Función para crear tarjeta de producto
function createProductCard(product) {
    const card = document.createElement("div");
    card.className = "product-card";
    card.dataset.brand = product.brand;
    card.dataset.id = product.id;
    
    // Crear imágenes (usar imagen por defecto si no hay)
    const imageUrl = product.image || "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+";
    
    // Formatear precio
    const formattedPrice = new Intl.NumberFormat('es-ES').format(product.price);
    
    card.innerHTML = `
        <div class="product-images-container">
            <img src="${imageUrl}" alt="${product.name}" class="product-image main-view">
            <img src="${imageUrl}" alt="${product.name}" class="product-image hover-view">
        </div>
        <h3>${product.name}</h3>
        <p class="price">$${formattedPrice}</p>
        <div class="product-options">
            <label for="talles-${product.id}">Talle:</label>
            <select id="talles-${product.id}" class="size-selector">
                ${product.sizes.map(size => `<option value="${size}">${size}</option>`).join('')}
            </select>
        </div>
        <button class="add-to-cart-btn" data-product-id="${product.id}">Añadir al Carrito</button>
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

// Inicializar eventos para productos
// En shop.js, dentro de initProductEvents():
function initProductEvents() {
  // Manejar clic en botón "Añadir al Carrito"
  document.querySelectorAll(".add-to-cart-btn").forEach(button => {
    button.addEventListener("click", function(e) {
      const productId = this.dataset.productId;
      const sizeSelector = document.getElementById(`talles-${productId}`);
      const size = sizeSelector ? sizeSelector.value : "Único";
      const product = products.find(p => p.id == productId);
      
      if (product) {
        // Llama a la función global definida en script.js
        window.addToCart(product.name, product.price, size);
      }
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

// Función para abrir modal de producto
function openProductModal(product) {
    // Implementar lógica para abrir modal con detalles del producto
    console.log("Abrir modal para:", product.name);
    // Aquí puedes implementar la lógica para mostrar un modal con más detalles
}

// Inicializar
document.addEventListener("DOMContentLoaded", function() {
    loadProducts();
    updateCartCount();
});