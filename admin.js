// Datos de ejemplo - En una aplicación real, estos datos vendrían de una base de datos
const productsData = [
    {
        id: 1,
        name: "Casco FOX V3",
        brand: "fox",
        price: 895000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Fox V3 Frontal.png",
        status: "active"
    },
    {
        id: 2,
        name: "Casco FOX V3 RS",
        brand: "fox",
        price: 925000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Fox V3 RS MC frontal.png",
        status: "active"
    },
    {
        id: 3,
        name: "Casco FOX V1",
        brand: "fox",
        price: 495000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Fox V1 frontal.png",
        status: "active"
    },
    {
        id: 4,
        name: "Casco FLY Racing F2",
        brand: "fly",
        price: 455000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Fly Racing F2 frontal.png",
        status: "active"
    },
    {
        id: 5,
        name: "Casco Bell Moto-9 Flex",
        brand: "bell",
        price: 750000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Bell Moto-9 Flex frontal.png",
        status: "active"
    },
    {
        id: 6,
        name: "Casco Alpinestars SM5",
        brand: "alpinestars",
        price: 650000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Alpinestars SM5 frontal.png",
        status: "active"
    },
    {
        id: 7,
        name: "Casco Aircraft 2 Carbono",
        brand: "aircraft",
        price: 820000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Aircraft 2 Carbono.png",
        status: "active"
    },
    {
        id: 8,
        name: "Casco Troy Lee Design D4",
        brand: "troylee",
        price: 780000,
        category: "cascos",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Troy Lee Design D4 lateral.png",
        status: "active"
    },
    {
        id: 9,
        name: "Guantes CROSS",
        brand: "fox",
        price: 50000,
        category: "accesorios",
        sizes: ["S", "M", "L", "XL"],
        image: "css img/Guantes FOX.png",
        status: "active"
    },
    {
        id: 10,
        name: "Antiparras CROSS",
        brand: "fox",
        price: 80000,
        category: "accesorios",
        sizes: ["Único"],
        image: "css img/antiparras 2.png",
        status: "active"
    }
];

// Variables globales
let currentPage = 1;
const productsPerPage = 5;
let filteredProducts = [...productsData];

// Elementos del DOM
const productsBody = document.getElementById('products-body');
const paginationElement = document.getElementById('pagination');
const notificationElement = document.getElementById('notification');

// Inicializar la aplicación
function init() {
    renderProducts();
    setupEventListeners();
}

// Renderizar productos en la tabla
function renderProducts() {
    productsBody.innerHTML = '';
    
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = startIndex + productsPerPage;
    const productsToRender = filteredProducts.slice(startIndex, endIndex);
    
    if (productsToRender.length === 0) {
        productsBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No se encontraron productos</td></tr>';
        return;
    }
    
    productsToRender.forEach(product => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td class="product-image-cell">
                <img src="${product.image}" alt="${product.name}" class="product-image" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjYwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjRUVFRUVFIi8+CjxwYXRoIGQ9Ik0zMCAzNUwzNSA0MEg0MFYzNUgzNVYzMEgzNVYyNUgzMFYzMFIMjVWMzVIMzBWMzVaIiBmaWxsPSIjOTk5OTk5Ii8+Cjwvc3ZnPgo='">
            </td>
            <td>
                <input type="text" value="${product.name}" data-field="name" data-id="${product.id}">
            </td>
            <td>
                <select data-field="brand" data-id="${product.id}">
                    <option value="fox" ${product.brand === 'fox' ? 'selected' : ''}>Fox</option>
                    <option value="bell" ${product.brand === 'bell' ? 'selected' : ''}>Bell</option>
                    <option value="fly" ${product.brand === 'fly' ? 'selected' : ''}>Fly Racing</option>
                    <option value="alpinestars" ${product.brand === 'alpinestars' ? 'selected' : ''}>Alpinestars</option>
                    <option value="aircraft" ${product.brand === 'aircraft' ? 'selected' : ''}>Aircraft</option>
                    <option value="troylee" ${product.brand === 'troylee' ? 'selected' : ''}>Troy Lee Design</option>
                </select>
            </td>
            <td>
                <input type="number" value="${product.price}" data-field="price" data-id="${product.id}">
            </td>
            <td>
                <select data-field="category" data-id="${product.id}">
                    <option value="cascos" ${product.category === 'cascos' ? 'selected' : ''}>Cascos</option>
                    <option value="accesorios" ${product.category === 'accesorios' ? 'selected' : ''}>Accesorios</option>
                </select>
            </td>
            <td>
                <select multiple data-field="sizes" data-id="${product.id}" style="height: 80px;">
                    <option value="S" ${product.sizes.includes('S') ? 'selected' : ''}>S</option>
                    <option value="M" ${product.sizes.includes('M') ? 'selected' : ''}>M</option>
                    <option value="L" ${product.sizes.includes('L') ? 'selected' : ''}>L</option>
                    <option value="XL" ${product.sizes.includes('XL') ? 'selected' : ''}>XL</option>
                    <option value="Único" ${product.sizes.includes('Único') ? 'selected' : ''}>Único</option>
                </select>
            </td>
            <td>
                <select data-field="status" data-id="${product.id}">
                    <option value="active" ${product.status === 'active' ? 'selected' : ''}>Activo</option>
                    <option value="inactive" ${product.status === 'inactive' ? 'selected' : ''}>Inactivo</option>
                </select>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn save-btn" data-id="${product.id}">💾</button>
                    <button class="action-btn cancel-btn" data-id="${product.id}">❌</button>
                </div>
            </td>
        `;
        
        productsBody.appendChild(row);
    });
    
    renderPagination();
}

// Renderizar controles de paginación
function renderPagination() {
    const totalPages = Math.ceil(filteredProducts.length / productsPerPage);
    
    paginationElement.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Botón Anterior
    const prevButton = document.createElement('button');
    prevButton.className = 'page-btn';
    prevButton.textContent = '←';
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderProducts();
        }
    });
    paginationElement.appendChild(prevButton);
    
    // Números de página
    for (let i = 1; i <= totalPages; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        pageButton.textContent = i;
        pageButton.addEventListener('click', () => {
            currentPage = i;
            renderProducts();
        });
        paginationElement.appendChild(pageButton);
    }
    
    // Botón Siguiente
    const nextButton = document.createElement('button');
    nextButton.className = 'page-btn';
    nextButton.textContent = '→';
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderProducts();
        }
    });
    paginationElement.appendChild(nextButton);
}

// Configurar event listeners
function setupEventListeners() {
    // Filtros
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Guardar todos los cambios
    document.getElementById('save-all').addEventListener('click', saveAllChanges);
    
    // Exportar datos
    document.getElementById('export-data').addEventListener('click', exportData);
    
    // Cerrar sesión
    document.getElementById('logout').addEventListener('click', () => {
        alert('Función de cerrar sesión implementada en sistema real');
    });
    
    // Rango de precios
    const priceRange = document.getElementById('price-range');
    const priceOutput = document.getElementById('price-output');
    
    priceRange.addEventListener('input', () => {
        if (priceRange.value === priceRange.max) {
            priceOutput.textContent = 'Todos los precios';
        } else {
            priceOutput.textContent = `Hasta $${parseInt(priceRange.value).toLocaleString()}`;
        }
    });
}

// Aplicar filtros
function applyFilters() {
    const searchTerm = document.getElementById('search').value.toLowerCase();
    const categoryFilter = document.getElementById('category').value;
    const brandFilter = document.getElementById('brand').value;
    const priceFilter = document.getElementById('price-range').value;
    
    filteredProducts = productsData.filter(product => {
        // Filtro de búsqueda
        if (searchTerm && !product.name.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // Filtro de categoría
        if (categoryFilter !== 'all' && product.category !== categoryFilter) {
            return false;
        }
        
        // Filtro de marca
        if (brandFilter !== 'all' && product.brand !== brandFilter) {
            return false;
        }
        
        // Filtro de precio
        if (priceFilter < productsData.reduce((max, p) => Math.max(max, p.price), 0) && 
            product.price > parseInt(priceFilter)) {
            return false;
        }
        
        return true;
    });
    
    currentPage = 1;
    renderProducts();
}

// Restablecer filtros
function resetFilters() {
    document.getElementById('search').value = '';
    document.getElementById('category').value = 'all';
    document.getElementById('brand').value = 'all';
    document.getElementById('price-range').value = document.getElementById('price-range').max;
    document.getElementById('price-output').textContent = 'Todos los precios';
    
    filteredProducts = [...productsData];
    currentPage = 1;
    renderProducts();
}

// Guardar todos los cambios
function saveAllChanges() {
    // En una aplicación real, aquí se enviarían los cambios al servidor
    showNotification('Todos los cambios han sido guardados correctamente', 'success');
}

// Exportar datos
function exportData() {
    const dataStr = JSON.stringify(productsData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'whip-helmets-products.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    showNotification('Datos exportados correctamente', 'success');
}

// Mostrar notificación
function showNotification(message, type) {
    notificationElement.textContent = message;
    notificationElement.className = `notification ${type}`;
    
    setTimeout(() => {
        notificationElement.className = 'notification';
    }, 3000);
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', init);