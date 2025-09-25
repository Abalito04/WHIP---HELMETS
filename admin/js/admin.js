// ==================== CONFIG ====================
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

// ==================== VARIABLES GLOBALES ====================
let productsData = [];
let filteredProducts = [];
let currentPage = 1;
const productsPerPage = 5;
let selectedImages = []; // Para almacenar múltiples imágenes seleccionadas

// ==================== ELEMENTOS DEL DOM ====================
const productsBody = document.getElementById("products-body");
const paginationElement = document.getElementById("pagination");
const notificationElement = document.getElementById("notification");
const addProductModal = document.getElementById("add-product-modal");
const newProductForm = document.getElementById("new-product-form");
const imageStatsModal = document.getElementById("image-stats-modal");

// ==================== API CALLS ====================
async function fetchProducts() {
  try {
    console.log("Intentando conectar con la API...");
    console.log("API_BASE:", API_BASE);
    const url = `${API_BASE}/api/products`;
    console.log("URL completa:", url);
    const res = await fetch(url);
    
    if (!res.ok) {
      throw new Error(`Error HTTP: ${res.status} ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log("Datos recibidos:", data);
    console.log("Número de productos cargados:", data.length);
    
    productsData = data;
    filteredProducts = [...productsData];
    console.log("Renderizando productos...");
    renderProducts();
    console.log("Productos renderizados exitosamente");
    
  // Actualizar filtros después de cargar productos
  updateBrandFilter();
  
  // También actualizar el select de marcas en el formulario de nuevo producto
  updateNewProductBrandSelect();
  } catch (err) {
    console.error("Error al cargar productos:", err);
    showNotification(`Error al cargar productos: ${err.message}`, "error");
    
    // Mostrar datos de ejemplo si la API no está disponible
    if (productsBody) {
      productsBody.innerHTML = `
        <tr>
          <td colspan="10" style="text-align: center; color: red;">
            Error al conectar con el servidor. Verifica que el servidor esté ejecutándose en ${API_BASE}
            <br><br>
            <button onclick="location.reload()" style="padding: 5px 10px;">Reintentar</button>
          </td>
        </tr>
      `;
    }
  }
}

async function updateProduct(id, updates) {
  try {
    console.log(`Actualizando producto ${id}:`, updates);
    console.log(`JSON que se envía al servidor:`, JSON.stringify(updates));
    const res = await fetch(`${API_BASE}/api/products/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    console.log(`Respuesta para producto ${id}:`, res.status, res.statusText);
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`Error detallado para producto ${id}:`, errorText);
      throw new Error(`Error al actualizar: ${res.status} ${res.statusText}`);
    }
    return { success: true, id };
  } catch (err) {
    console.error("Error al actualizar producto:", err);
    return { success: false, id, error: err.message };
  }
}

async function deleteProduct(id) {
  try {
    const res = await fetch(`${API_BASE}/api/products/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Error al eliminar");
    showNotification("Producto eliminado", "success");
    fetchProducts();
  } catch (err) {
    showNotification("Error al eliminar producto", "error");
  }
}

async function createProduct(product) {
  try {
    const res = await fetch(`${API_BASE}/api/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(product),
    });
    if (!res.ok) throw new Error("Error al crear");
    showNotification("Producto creado", "success");
    fetchProducts();
  } catch (err) {
    showNotification("Error al crear producto", "error");
  }
}

// ==================== FUNCIONES DE ESTADÍSTICAS DE PRODUCTOS ====================

async function getProductStats() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    if (!res.ok) throw new Error("Error al obtener productos");
    
    const products = await res.json();
    
    // Calcular estadísticas
    const totalProducts = products.length;
    const activeProducts = products.filter(p => p.stock > 0).length;
    const totalStock = products.reduce((sum, p) => sum + (p.stock || 0), 0);
    const totalValue = products.reduce((sum, p) => sum + ((p.price || 0) * (p.stock || 0)), 0);
    
    // Actualizar estadísticas en el modal
    document.getElementById("total-products").textContent = totalProducts;
    document.getElementById("active-products").textContent = activeProducts;
    document.getElementById("total-stock").textContent = totalStock;
    document.getElementById("total-value").textContent = `$${totalValue.toFixed(2)}`;
    
    // Mostrar modal
    imageStatsModal.style.display = "block";
    
  } catch (err) {
    showNotification(`Error al obtener estadísticas: ${err.message}`, "error");
  }
}

// ==================== GUARDAR TODOS LOS CAMBIOS ====================
async function saveAllChanges() {
  const allInputs = document.querySelectorAll('#products-body input, #products-body select');
  const updates = [];
  
  // Agrupar cambios por producto
  const productUpdates = {};
  
  allInputs.forEach(input => {
    const productId = input.dataset.id;
    const field = input.dataset.field;
    
    if (!productUpdates[productId]) {
      productUpdates[productId] = { id: productId, updates: {} };
    }
    
    if (field === 'sizes') {
      productUpdates[productId].updates[field] = input.value.split(',').map(s => s.trim());
    } else if (field === 'stock') {
      productUpdates[productId].updates[field] = parseInt(input.value) || 0;
    } else if (field === 'porcentaje_descuento') {
      // Manejar porcentaje_descuento: si está vacío, enviar null
      const value = input.value.trim();
      productUpdates[productId].updates[field] = value === '' ? null : parseFloat(value);
    } else {
      productUpdates[productId].updates[field] = input.value;
    }
  });
  
  // Convertir a array
  const updatePromises = Object.values(productUpdates).map(product => 
    updateProduct(product.id, product.updates)
  );
  
  // Mostrar indicador de progreso
  showNotification("Guardando cambios...", "info");
  
  // Ejecutar todas las actualizaciones
  try {
    const results = await Promise.all(updatePromises);
    
    // Contar resultados
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    
    if (failed === 0) {
      showNotification(`Todos los cambios (${successful}) guardados correctamente`, "success");
    } else {
      showNotification(`${successful} cambios guardados, ${failed} errores`, "error");
    }
    
    // Recargar productos para reflejar cambios
    fetchProducts();
  } catch (error) {
    showNotification("Error al guardar cambios: " + error.message, "error");
  }
}

// ==================== EXPORTAR DATOS ====================
function exportData() {
  // Crear contenido CSV
      let csvContent = "Nombre,Marca,Precio Normal,% Descuento,Categoría,Condición,Talles,Stock,Estado,Imagen\n";
  
  productsData.forEach(product => {
    const row = [
      `"${product.name.replace(/"/g, '""')}"`,
      `"${product.brand}"`,
      product.price,
      product.porcentaje_descuento || '',
      `"${product.category}"`,
      `"${product.condition || 'Nuevo'}"`,
      `"${Array.isArray(product.sizes) ? product.sizes.join(',') : product.sizes}"`,
      product.stock || 0,
      `"${product.status}"`,
      `"${product.image}"`
    ];
    csvContent += row.join(',') + '\n';
  });
  
  // Crear blob y descargar
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  
  link.setAttribute("href", url);
  link.setAttribute("download", "productos_whip_helmets.csv");
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  showNotification("Datos exportados correctamente", "success");
}

// ==================== RENDER ====================
function renderProducts() {
  if (!productsBody) {
    console.error("productsBody no encontrado en el DOM");
    return;
  }
  
  productsBody.innerHTML = "";

  const startIndex = (currentPage - 1) * productsPerPage;
  const endIndex = startIndex + productsPerPage;
  const productsToRender = filteredProducts.slice(startIndex, endIndex);

  if (productsToRender.length === 0) {
    productsBody.innerHTML =
      '<tr><td colspan="10" style="text-align: center;">No se encontraron productos</td></tr>';
    return;
  }

  productsToRender.forEach((product) => {
    const row = document.createElement("tr");
    
    // Determinar clase CSS para el stock
    let stockClass = "stock-high";
    if (product.stock <= 5) stockClass = "stock-low";
    else if (product.stock <= 15) stockClass = "stock-medium";

    row.innerHTML = `
      <td class="product-image-cell">
        <img src="${product.image.startsWith('http') ? product.image : '/' + product.image}" alt="${product.name}" class="product-image" onclick="openGallery(${product.id}, '${product.name}')"
          onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+'">
        <button class="product-image-gallery-btn" onclick="openGallery(${product.id}, '${product.name}')" title="Ver galería">📷</button>
      </td>
      <td><input type="text" value="${product.name}" data-field="name" data-id="${product.id}"></td>
      <td><input type="text" value="${product.brand}" data-field="brand" data-id="${product.id}"></td>
      <td><input type="number" value="${product.price}" data-field="price" data-id="${product.id}"></td>
      <td><input type="number" value="${product.porcentaje_descuento || ''}" data-field="porcentaje_descuento" data-id="${product.id}" min="0" max="100" step="0.1" placeholder="Ej: 10.5"></td>
      <td><input type="text" value="${product.category}" data-field="category" data-id="${product.id}"></td>
      <td>
        <select data-field="condition" data-id="${product.id}">
          <option value="Nuevo" ${product.condition === "Nuevo" ? "selected" : ""}>Nuevo</option>
          <option value="Usado" ${product.condition === "Usado" ? "selected" : ""}>Usado</option>
        </select>
      </td>
      <td><input type="text" value="${product.sizes ? product.sizes.join(",") : ""}" data-field="sizes" data-id="${product.id}"></td>
      <td>
        <input type="number" value="${product.stock || 0}" data-field="stock" data-id="${product.id}" class="${stockClass}" min="0">
      </td>
      <td>
        <select data-field="status" data-id="${product.id}">
          <option value="Activo" ${product.status === "Activo" ? "selected" : ""}>Activo</option>
          <option value="Inactivo" ${product.status === "Inactivo" ? "selected" : ""}>Inactivo</option>
        </select>
      </td>
      <td>
        <div class="action-buttons">
          <button class="action-btn save-btn" data-id="${product.id}" title="Guardar cambios">💾</button>
          <button class="action-btn delete-btn" data-id="${product.id}" title="Eliminar producto">🗑</button>
        </div>
      </td>
    `;

    productsBody.appendChild(row);
  });

  renderPagination();
}

function renderPagination() {
  const totalPages = Math.ceil(filteredProducts.length / productsPerPage);
  paginationElement.innerHTML = "";

  if (totalPages <= 1) return;

  for (let i = 1; i <= totalPages; i++) {
    const pageButton = document.createElement("button");
    pageButton.className = `page-btn ${i === currentPage ? "active" : ""}`;
    pageButton.textContent = i;
    pageButton.addEventListener("click", () => {
      currentPage = i;
      renderProducts();
    });
    paginationElement.appendChild(pageButton);
  }
}

// ==================== FILTROS ====================
function updateBrandFilter() {
  console.log('=== ACTUALIZANDO FILTRO DE MARCAS ===');
  console.log('Productos disponibles:', productsData.length);
  
  // Obtener todas las marcas únicas de los productos
  const uniqueBrands = [...new Set(productsData.map(p => p.brand))].filter(brand => brand);
  console.log('Marcas únicas encontradas:', uniqueBrands);
  console.log('Tipos de marcas:', uniqueBrands.map(brand => ({ brand, type: typeof brand })));
  
  // Obtener el select de marcas
  const brandSelect = document.getElementById('brand');
  if (!brandSelect) {
    console.error('No se encontró el select de marcas');
    return;
  }
  
  // Guardar el valor actual
  const currentValue = brandSelect.value;
  console.log('Valor actual del select:', currentValue);
  
  // Limpiar opciones existentes (excepto "Todas las marcas")
  brandSelect.innerHTML = '<option value="all">Todas las marcas</option>';
  
  // Agregar cada marca como opción
  uniqueBrands.sort().forEach(brand => {
    const option = document.createElement('option');
    option.value = brand;
    option.textContent = brand.charAt(0).toUpperCase() + brand.slice(1); // Capitalizar primera letra
    brandSelect.appendChild(option);
    console.log(`Agregada opción: value="${brand}", text="${option.textContent}"`);
  });
  
  // Restaurar el valor seleccionado si aún existe
  if (currentValue && uniqueBrands.includes(currentValue)) {
    brandSelect.value = currentValue;
    console.log('Valor restaurado:', currentValue);
  } else {
    console.log('Valor no restaurado. Actual:', currentValue, 'Disponibles:', uniqueBrands);
  }
  
  console.log('Opciones finales del select:', Array.from(brandSelect.options).map(opt => ({ value: opt.value, text: opt.textContent })));
  console.log('Filtro de marcas actualizado');
}

function updateNewProductBrandSelect() {
  console.log('Actualizando select de marcas en formulario de nuevo producto...');
  
  // Obtener todas las marcas únicas de los productos
  const uniqueBrands = [...new Set(productsData.map(p => p.brand))].filter(brand => brand);
  console.log('Marcas únicas para nuevo producto:', uniqueBrands);
  
  // Obtener el select de marcas del formulario de nuevo producto
  const newBrandSelect = document.getElementById('new-brand');
  if (!newBrandSelect) {
    console.error('No se encontró el select de marcas del formulario de nuevo producto');
    return;
  }
  
  // Guardar el valor actual
  const currentValue = newBrandSelect.value;
  
  // Limpiar opciones existentes (excepto "Seleccione una marca" y "Agregar nueva marca")
  newBrandSelect.innerHTML = `
    <option value="">Seleccione una marca</option>
    <option value="fox">Fox</option>
    <option value="bell">Bell</option>
    <option value="fly">Fly Racing</option>
    <option value="alpinestars">Alpinestars</option>
    <option value="aircraft">Aircraft</option>
    <option value="troylee">Troy Lee Design</option>
  `;
  
  // Agregar marcas dinámicas (que no estén ya en la lista)
  const existingBrands = ['fox', 'bell', 'fly', 'alpinestars', 'aircraft', 'troylee'];
  uniqueBrands.forEach(brand => {
    if (!existingBrands.includes(brand)) {
      const option = document.createElement('option');
      option.value = brand;
      option.textContent = brand.charAt(0).toUpperCase() + brand.slice(1);
      newBrandSelect.appendChild(option);
    }
  });
  
  // Agregar opción "Agregar nueva marca" al final
  const newBrandOption = document.createElement('option');
  newBrandOption.value = 'new';
  newBrandOption.textContent = '+ Agregar nueva marca';
  newBrandSelect.appendChild(newBrandOption);
  
  // Restaurar el valor seleccionado si aún existe
  if (currentValue && (uniqueBrands.includes(currentValue) || existingBrands.includes(currentValue))) {
    newBrandSelect.value = currentValue;
  }
  
  console.log('Select de marcas del formulario actualizado');
}

function applyFilters() {
  const searchElement = document.getElementById("search");
  const searchTerm = searchElement ? searchElement.value.toLowerCase() : '';
  const categoryElement = document.getElementById("category");
  const categoryFilter = categoryElement ? categoryElement.value.toLowerCase() : 'all';
  const brandElement = document.getElementById("brand");
  const brandFilter = brandElement ? brandElement.value.toLowerCase() : 'all';
  console.log('Elemento brand encontrado:', brandElement);
  console.log('Valor original del select brand:', brandElement ? brandElement.value : 'NO ENCONTRADO');
  console.log('Valor procesado brandFilter:', brandFilter);
  const stockElement = document.getElementById("stock-filter");
  const stockFilter = stockElement ? stockElement.value : 'all';
  const priceRangeElement = document.getElementById("price-range");
  const priceFilter = priceRangeElement ? parseInt(priceRangeElement.value) : 0;
  const statusElement = document.getElementById("status-filter");
  const statusFilter = statusElement ? statusElement.value : 'all';
  const conditionElement = document.getElementById("condition-filter");
  const conditionFilter = conditionElement ? conditionElement.value : 'all';

  console.log("=== APLICANDO FILTROS ===");
  console.log("Valores de filtros:", {
    searchTerm,
    categoryFilter,
    brandFilter,
    stockFilter,
    priceFilter,
    statusFilter,
    conditionFilter
  });

  console.log("Productos antes del filtro:", productsData.length);
  console.log("Estados únicos en productos:", [...new Set(productsData.map(p => p.status))]);
  console.log("Condiciones únicas en productos:", [...new Set(productsData.map(p => p.condition))]);
  console.log("Marcas únicas en productos:", [...new Set(productsData.map(p => p.brand))]);
  console.log("Detalles de marcas:", productsData.map(p => ({ name: p.name, brand: p.brand, brandType: typeof p.brand })));

  filteredProducts = productsData.filter((product) => {
    console.log(`\n--- Evaluando producto: ${product.name} ---`);
    
    // Filtro de búsqueda
    if (searchTerm) {
      const productName = product.name ? product.name.toLowerCase() : '';
      const productBrand = product.brand ? product.brand.toLowerCase() : '';
      const productCategory = product.category ? product.category.toLowerCase() : '';
      
      const matchesName = productName.includes(searchTerm);
      const matchesBrand = productBrand.includes(searchTerm);
      const matchesCategory = productCategory.includes(searchTerm);
      
      console.log(`🔍 Búsqueda "${searchTerm}" en:`, {
        name: productName,
        brand: productBrand,
        category: productCategory,
        matchesName,
        matchesBrand,
        matchesCategory
      });
      
      if (!matchesName && !matchesBrand && !matchesCategory) {
        console.log(`❌ Filtrado por búsqueda: no coincide con "${searchTerm}"`);
        return false;
      }
    }
    
    // Filtro de categoría
    if (categoryFilter !== "all") {
      const productCategory = product.category ? product.category.toLowerCase() : '';
      console.log(`🔍 Comparando categoría: "${productCategory}" === "${categoryFilter}"`, productCategory === categoryFilter);
      if (productCategory !== categoryFilter) {
        console.log(`❌ Filtrado por categoría: "${product.category}" !== "${categoryFilter}"`);
        return false;
      }
    }
    
    // Filtro de marca
    if (brandFilter !== "all") {
      const productBrand = product.brand ? product.brand.toLowerCase() : '';
      console.log(`🔍 Comparando marca:`, {
        productBrand: `"${productBrand}"`,
        brandFilter: `"${brandFilter}"`,
        originalBrand: `"${product.brand}"`,
        match: productBrand === brandFilter
      });
      if (productBrand !== brandFilter) {
        console.log(`❌ Filtrado por marca: "${product.brand}" !== "${brandFilter}"`);
        return false;
      }
    }
    
    // Filtrar por estado - con debug
    if (statusFilter !== "all") {
      const productStatus = product.status || 'Activo'; // Default a 'Activo' si no hay estado
      console.log(`🔍 Comparando estado: "${productStatus}" === "${statusFilter}"`, productStatus === statusFilter);
      if (productStatus !== statusFilter) {
        console.log(`❌ Filtrado por estado: "${productStatus}" !== "${statusFilter}"`);
        return false;
      }
    }
    
    // Filtrar por condición
    if (conditionFilter !== "all") {
      const productCondition = product.condition || 'Nuevo'; // Default a 'Nuevo' si no hay condición
      console.log(`🔍 Comparando condición: "${productCondition}" === "${conditionFilter}"`, productCondition === conditionFilter);
      if (productCondition !== conditionFilter) {
        console.log(`❌ Filtrado por condición: "${productCondition}" !== "${conditionFilter}"`);
        return false;
      }
    }
    
    // Filtrar por stock
    if (stockFilter !== "all") {
      const stock = product.stock || 0;
      console.log(`🔍 Evaluando stock: ${stock} para filtro "${stockFilter}"`);
      
      if (stockFilter === "low" && stock > 5) {
        console.log(`❌ Filtrado por stock bajo: ${stock} > 5`);
        return false;
      }
      if (stockFilter === "medium" && (stock <= 5 || stock > 15)) {
        console.log(`❌ Filtrado por stock medio: ${stock} no está entre 6-15`);
        return false;
      }
      if (stockFilter === "high" && stock <= 15) {
        console.log(`❌ Filtrado por stock alto: ${stock} <= 15`);
        return false;
      }
      if (stockFilter === "out" && stock > 0) {
        console.log(`❌ Filtrado por sin stock: ${stock} > 0`);
        return false;
      }
    }
    
    // Filtrar por precio
    if (priceFilter && priceFilter > 0) {
      const productPrice = product.price || 0;
      console.log(`🔍 Evaluando precio: ${productPrice} <= ${priceFilter}`);
      if (productPrice > priceFilter) {
        console.log(`❌ Filtrado por precio: ${productPrice} > ${priceFilter}`);
        return false;
      }
    }
    
    console.log(`✅ Producto "${product.name}" pasa todos los filtros`);
    return true;
  });

  console.log("Productos después del filtro:", filteredProducts.length);
  console.log("Productos filtrados:", filteredProducts.map(p => ({ name: p.name, status: p.status })));

  currentPage = 1;
  renderProducts();
}

function resetFilters() {
  console.log('=== RESETEANDO FILTROS ===');
  
  const searchEl = document.getElementById("search");
  if (searchEl) searchEl.value = "";
  
  const categoryEl = document.getElementById("category");
  if (categoryEl) categoryEl.value = "all";
  
  const brandEl = document.getElementById("brand");
  if (brandEl) brandEl.value = "all";
  
  const stockEl = document.getElementById("stock-filter");
  if (stockEl) stockEl.value = "all";
  
  const statusEl = document.getElementById("status-filter");
  if (statusEl) statusEl.value = "all";
  
  const conditionEl = document.getElementById("condition-filter");
  if (conditionEl) conditionEl.value = "all";
  
  const priceEl = document.getElementById("price-range");
  if (priceEl) priceEl.value = priceEl.max;
  
  filteredProducts = [...productsData];
  currentPage = 1;
  renderProducts();
  
  console.log('Filtros reseteados');
}

// ==================== MODAL ====================
function openAddProductModal() {
  addProductModal.style.display = "block";
}

function closeAddProductModal() {
  addProductModal.style.display = "none";
  newProductForm.reset();
  
  // Limpiar vista previa de imagen
  const preview = document.getElementById("image-preview");
  const previewImg = document.getElementById("preview-img");
  if (previewImg.src) {
    URL.revokeObjectURL(previewImg.src);
  }
  preview.style.display = "none";
  
  // Limpiar el input de nueva marca
  const brandInput = document.getElementById("new-brand-input");
  if (brandInput) {
    brandInput.style.display = "none";
    brandInput.value = "";
    brandInput.required = false;
  }
  
  // Resetear el select de marca
  const brandSelect = document.getElementById("new-brand");
  if (brandSelect) {
    brandSelect.required = true;
  }
  
  // Limpiar múltiples imágenes
  const multiplePreview = document.getElementById("multiple-images-preview");
  const imagesList = document.getElementById("images-list");
  imagesList.innerHTML = "";
  multiplePreview.style.display = "none";
  selectedImages = [];
  
  // Limpiar inputs
  document.getElementById("image-file-input").value = "";
  document.getElementById("multiple-images-input").value = "";
}


// ==================== EVENTOS ====================
function setupEventListeners() {
  // Verificar que los elementos existan antes de agregar event listeners
  const applyFiltersBtn = document.getElementById("apply-filters");
  const resetFiltersBtn = document.getElementById("reset-filters");
  const addProductBtn = document.getElementById("add-product");
  const saveAllBtn = document.getElementById("save-all");
  const exportDataBtn = document.getElementById("export-data");
  const imageStatsBtn = document.getElementById("image-stats");
  

  if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener("click", () => {
      console.log('=== BOTÓN APLICAR FILTROS CLICKEADO ===');
      applyFilters();
    });
  } else {
    console.error('No se encontró el botón apply-filters');
  }
  
  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener("click", resetFilters);
  }
  
  if (addProductBtn) {
    addProductBtn.addEventListener("click", openAddProductModal);
  }
  
  if (saveAllBtn) {
    saveAllBtn.addEventListener("click", saveAllChanges);
  }
  
  if (exportDataBtn) {
    exportDataBtn.addEventListener("click", exportData);
  }
  
  // Manejar select de marca para permitir agregar nuevas
  const brandSelect = document.getElementById("new-brand");
  const brandInput = document.getElementById("new-brand-input");
  
  if (brandSelect && brandInput) {
    brandSelect.addEventListener("change", (e) => {
      if (e.target.value === "new") {
        brandInput.style.display = "block";
        brandInput.required = true;
        brandSelect.required = false;
        brandInput.focus();
      } else {
        brandInput.style.display = "none";
        brandInput.required = false;
        brandSelect.required = true;
        brandInput.value = "";
      }
    });
  }
  
  // Ver estadísticas de productos
  if (imageStatsBtn) {
    imageStatsBtn.addEventListener("click", () => {
      getProductStats();
    });
  }

  // Cerrar modales con botones X
  document.querySelectorAll(".close").forEach(closeBtn => {
    closeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      console.log("Botón cerrar clickeado");
      // Cerrar el modal más cercano
      const modal = closeBtn.closest('.modal');
      if (modal) {
        modal.style.display = "none";
        // Si es el modal de agregar producto, limpiar formulario
        if (modal.id === 'add-product-modal') {
          closeAddProductModal();
        }
      }
    });
  });

  // Cerrar modales al hacer clic fuera
  window.addEventListener("click", (event) => {
    if (event.target === addProductModal) {
      closeAddProductModal();
    }
    if (event.target === imageStatsModal) {
      imageStatsModal.style.display = "none";
    }
  });

  // Logout
  document.getElementById("logout").addEventListener("click", () => {
    if (confirm("¿Estás seguro de que deseas cerrar sesión?")) {
        // Cerrar sesión en el servidor
        const token = localStorage.getItem('authToken');
        if (token) {
            fetch(`${API_BASE}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).catch(() => {
                // Si falla, continuar con el logout local
            });
        }
        
        // Limpiar localStorage
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        
        // Redirigir a la página principal
        window.location.href = '/';
    }
  });

  // Botón de subir imagen
  const uploadImageBtn = document.getElementById("upload-image-btn");
  if (uploadImageBtn) {
    uploadImageBtn.addEventListener("click", () => {
      console.log("Botón de subir imagen clickeado");
      const fileInput = document.getElementById("image-file-input");
      if (fileInput) {
        fileInput.click();
      }
    });
  }

  // Botón de subir múltiples imágenes
  const uploadMultipleBtn = document.getElementById("upload-multiple-btn");
  if (uploadMultipleBtn) {
    uploadMultipleBtn.addEventListener("click", () => {
      console.log("Botón de subir múltiples imágenes clickeado");
      const fileInput = document.getElementById("multiple-images-input");
      if (fileInput) {
        fileInput.click();
      }
    });
  }

  // Event listeners de galería (movidos desde DOMContentLoaded)
  const galleryClose = document.querySelector('.gallery-close');
  const galleryModal = document.getElementById('gallery-modal');
  const setMainImageBtn = document.getElementById('set-main-image');
  const deleteImageBtn = document.getElementById('delete-image');
  const addImagesBtn = document.getElementById('add-images');
  const galleryFileInput = document.getElementById('gallery-file-input');
  const uploadArea = document.getElementById('gallery-upload');

  if (galleryClose) {
    galleryClose.addEventListener('click', closeGallery);
  }
  
  if (galleryModal) {
    galleryModal.addEventListener('click', (e) => {
      if (e.target.id === 'gallery-modal') {
        closeGallery();
      }
    });
  }
  
  if (setMainImageBtn) {
    setMainImageBtn.addEventListener('click', setMainImage);
  }
  
  if (deleteImageBtn) {
    deleteImageBtn.addEventListener('click', deleteImage);
  }
  
  if (addImagesBtn) {
    addImagesBtn.addEventListener('click', addImages);
  }
  
  if (galleryFileInput) {
    galleryFileInput.addEventListener('change', async (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        await uploadImagesToGallery(files);
        e.target.value = '';
      }
    });
  }
  
  if (uploadArea) {
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', async (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await uploadImagesToGallery(files);
      }
    });
  }

  // Manejar selección de archivo individual
  const imageFileInput = document.getElementById("image-file-input");
  if (imageFileInput) {
    imageFileInput.addEventListener("change", async (e) => {
    console.log("Archivo seleccionado:", e.target.files[0]);
    const file = e.target.files[0];
    if (!file) return;

    // Mostrar vista previa
    const preview = document.getElementById("image-preview");
    const previewImg = document.getElementById("preview-img");
    const previewFilename = document.querySelector(".preview-filename");
    
    previewImg.src = URL.createObjectURL(file);
    previewFilename.textContent = file.name;
    preview.style.display = "flex";

    // Subir archivo
    try {
      console.log("Iniciando subida a Cloudinary...");
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });

      console.log("Respuesta del servidor:", response.status);
      const result = await response.json();
      console.log("Resultado:", result);

      if (result.success) {
        // Actualizar el campo de imagen con la ruta del archivo subido
        document.getElementById("new-image").value = result.file_path;
        showNotification("Imagen subida correctamente", "success");
      } else {
        showNotification(`Error al subir imagen: ${result.error}`, "error");
        preview.style.display = "none";
      }
    } catch (error) {
      console.error("Error en subida:", error);
      showNotification(`Error al subir imagen: ${error.message}`, "error");
      preview.style.display = "none";
    }
  });
  }

  // Manejar selección de múltiples archivos
  const multipleImagesInput = document.getElementById("multiple-images-input");
  if (multipleImagesInput) {
    multipleImagesInput.addEventListener("change", async (e) => {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;

      console.log(`${files.length} archivos seleccionados`);
      
      // Mostrar vista previa de múltiples imágenes
      const multiplePreview = document.getElementById("multiple-images-preview");
      const imagesList = document.getElementById("images-list");
      
      multiplePreview.style.display = "block";
      imagesList.innerHTML = "";

      // Subir archivos uno por uno
      selectedImages = [];
      let uploadedCount = 0;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Crear elemento de vista previa
        const imageItem = document.createElement("div");
        imageItem.className = "image-item";
        imageItem.innerHTML = `
          <div class="image-preview-item">
            <img src="${URL.createObjectURL(file)}" alt="${file.name}">
            <div class="image-info">
              <span class="image-name">${file.name}</span>
              <div class="upload-status" id="status-${i}">⏳ Subiendo...</div>
            </div>
          </div>
        `;
        imagesList.appendChild(imageItem);

        // Subir archivo
        try {
          const formData = new FormData();
          formData.append('file', file);

          const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
          });

          const result = await response.json();

          if (result.success) {
            selectedImages.push(result.file_path);
            document.getElementById(`status-${i}`).innerHTML = "✅ Subida";
            uploadedCount++;
          } else {
            document.getElementById(`status-${i}`).innerHTML = `❌ Error: ${result.error}`;
          }
        } catch (error) {
          document.getElementById(`status-${i}`).innerHTML = `❌ Error: ${error.message}`;
        }
      }

      // Actualizar campo de imagen principal con la primera imagen subida
      if (selectedImages.length > 0) {
        document.getElementById("new-image").value = selectedImages[0];
        showNotification(`${uploadedCount} de ${files.length} imágenes subidas correctamente`, "success");
      } else {
        showNotification("Error al subir las imágenes", "error");
      }

      // Limpiar input
      e.target.value = "";
    });
  }

  // Formulario para nuevo producto
  newProductForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const condition = document.getElementById("new-condition").value;
    const brandSelect = document.getElementById("new-brand");
    const brandInput = document.getElementById("new-brand-input");
    
    // Determinar la marca a usar
    let brand;
    if (brandSelect.value === "new" && brandInput.value.trim()) {
      brand = brandInput.value.trim().toLowerCase().replace(/\s+/g, '');
    } else {
      brand = brandSelect.value;
    }
    
    const newProduct = {
      name: document.getElementById("new-name").value,
      brand: brand,
      price: parseFloat(document.getElementById("new-price").value),
      porcentaje_descuento: document.getElementById("new-porcentaje-descuento").value ? parseFloat(document.getElementById("new-porcentaje-descuento").value) : null,
      category: document.getElementById("new-category").value,
      condition: condition,
      sizes: document.getElementById("new-sizes").value.split(",").map(s => s.trim()),
      stock: parseInt(document.getElementById("new-stock").value) || 0,
      image: document.getElementById("new-image").value,
      images: selectedImages.length > 0 ? selectedImages : [document.getElementById("new-image").value], // Incluir múltiples imágenes
      status: "Activo" // Por defecto activo
    };
    
    createProduct(newProduct);
    closeAddProductModal();
  });



  // Guardar cambios individuales
  productsBody.addEventListener("click", (e) => {
    if (e.target.classList.contains("save-btn")) {
      const id = e.target.dataset.id;
      const rowInputs = document.querySelectorAll(`[data-id="${id}"]`);
      const updates = {};
      rowInputs.forEach((input) => {
        if (input.dataset.field === "sizes") {
          updates["sizes"] = input.value.split(",").map((s) => s.trim());
        } else if (input.dataset.field === "stock") {
          updates["stock"] = parseInt(input.value) || 0;
        } else if (input.dataset.field === "condition") {
          console.log(`Campo condition detectado: valor="${input.value}"`);
          updates["condition"] = input.value;
        } else if (input.dataset.field === "porcentaje_descuento") {
          // Convertir cadena vacía a null para evitar errores en PostgreSQL
          updates["porcentaje_descuento"] = input.value === "" ? null : parseFloat(input.value);
        } else {
          updates[input.dataset.field] = input.value;
        }
      });
      console.log("Datos que se van a enviar para actualización:", updates);
      console.log("Campo condition específico:", updates.condition);
      updateProduct(id, updates).then(result => {
        console.log("Resultado de actualización:", result);
        if (result.success) {
          showNotification("Producto actualizado", "success");
          console.log("Recargando productos después de actualización...");
          fetchProducts().then(() => {
            console.log("Productos recargados exitosamente");
          }).catch(err => {
            console.error("Error al recargar productos:", err);
          });
        } else {
          showNotification("Error al actualizar producto", "error");
        }
      });
    }

    if (e.target.classList.contains("delete-btn")) {
      const id = e.target.dataset.id;
      if (confirm("¿Seguro que deseas eliminar este producto?")) {
        deleteProduct(id);
      }
    }
  });

  // Rango de precios
  const priceRange = document.getElementById("price-range");
  const priceOutput = document.getElementById("price-output");
  priceRange.addEventListener("input", () => {
    if (priceRange.value === priceRange.max) {
      priceOutput.textContent = "Todos los precios";
    } else {
      priceOutput.textContent = `Hasta $${parseInt(priceRange.value).toLocaleString()}`;
    }
  });
}

// ==================== NOTIFICACIONES ====================
function showNotification(message, type = "success") {
  if (!notificationElement) {
    console.error("notificationElement no encontrado en el DOM");
    return;
  }
  
  notificationElement.textContent = message;
  notificationElement.className = `notification ${type}`;
  
  // Para notificaciones de información (progreso)
  if (type === "info") {
    notificationElement.style.backgroundColor = "#17a2b8";
  }
  
  if (type !== "info") {
    setTimeout(() => {
      notificationElement.className = "notification";
      notificationElement.textContent = "";
    }, 3000);
  }
}

// ==================== INIT ====================
function init() {
  console.log("Inicializando panel de administración...");
  
  // Verificar que los elementos críticos existan
  if (!productsBody) {
    console.error("productsBody no encontrado - el panel no se puede inicializar");
    return;
  }
  
  if (!notificationElement) {
    console.error("notificationElement no encontrado - las notificaciones no funcionarán");
  }
  
  // Configurar event listeners primero
  setupEventListeners();
  
  // Intentar cargar productos
  fetchProducts();
}

// Función para verificar conectividad
async function checkConnectivity() {
  try {
    const url = `${API_BASE}/api/health`;
    console.log("Verificando conectividad con URL:", url);
    const response = await fetch(url, { 
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.ok;
  } catch (error) {
    console.error("Error de conectividad:", error);
    return false;
  }
}

// ==================== FUNCIONES DE GALERÍA ====================
let currentGalleryProduct = null;
let currentGalleryImages = [];
let selectedImageIndex = 0;

function openGallery(productId, productName) {
  currentGalleryProduct = productId;
  document.getElementById('gallery-title').textContent = `Galería de Imágenes - ${productName}`;
  
  // Simular carga de imágenes (en un caso real, esto vendría de la API)
  loadProductImages(productId);
  
  document.getElementById('gallery-modal').style.display = 'block';
}

function loadProductImages(productId) {
  // Cargar imágenes del producto desde la API
  const product = productsData.find(p => p.id == productId);
  if (product) {
    // Si el producto tiene múltiples imágenes, usarlas; si no, usar solo la principal
    if (product.images && Array.isArray(product.images) && product.images.length > 0) {
      currentGalleryImages = product.images;
    } else {
      currentGalleryImages = [product.image];
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
  const mainImageUrl = currentGalleryImages[selectedImageIndex];
  mainImg.src = mainImageUrl.startsWith('http') ? mainImageUrl : `/${mainImageUrl}`;
  
  // Renderizar miniaturas
  const thumbnailsContainer = document.getElementById('gallery-thumbnails');
  thumbnailsContainer.innerHTML = '';
  
  currentGalleryImages.forEach((image, index) => {
    const thumbnail = document.createElement('img');
    const imageUrl = image.startsWith('http') ? image : `/${image}`;
    thumbnail.src = imageUrl;
    thumbnail.className = `gallery-thumbnail ${index === selectedImageIndex ? 'active' : ''}`;
    thumbnail.onclick = () => selectImage(index);
    thumbnail.onerror = () => {
      thumbnail.style.display = 'none';
    };
    thumbnailsContainer.appendChild(thumbnail);
  });
}

function selectImage(index) {
  selectedImageIndex = index;
  renderGallery();
}

function closeGallery() {
  document.getElementById('gallery-modal').style.display = 'none';
  currentGalleryProduct = null;
  currentGalleryImages = [];
  selectedImageIndex = 0;
}

async function setMainImage() {
  console.log('setMainImage llamado');
  console.log('currentGalleryImages:', currentGalleryImages);
  console.log('currentGalleryProduct:', currentGalleryProduct);
  console.log('selectedImageIndex:', selectedImageIndex);
  
  if (currentGalleryImages.length > 0 && currentGalleryProduct) {
    const newMainImage = currentGalleryImages[selectedImageIndex];
    console.log('Nueva imagen principal:', newMainImage);
    
    try {
      const response = await fetch(`${API_BASE}/api/products/${currentGalleryProduct}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image: newMainImage
        })
      });

      console.log('Respuesta del servidor:', response.status);
      
      if (response.ok) {
        showNotification('Imagen principal actualizada', 'success');
        // Recargar la lista de productos para reflejar los cambios
        fetchProducts();
      } else {
        const error = await response.json();
        console.error('Error del servidor:', error);
        showNotification(`Error: ${error.error}`, 'error');
      }
    } catch (error) {
      console.error('Error en la petición:', error);
      showNotification(`Error al actualizar imagen principal: ${error.message}`, 'error');
    }
  } else {
    console.log('No se puede establecer imagen principal: datos insuficientes');
    showNotification('No hay imagen seleccionada o producto válido', 'error');
  }
}

async function deleteImage() {
  console.log('deleteImage llamado');
  console.log('currentGalleryImages:', currentGalleryImages);
  console.log('selectedImageIndex:', selectedImageIndex);
  console.log('currentGalleryProduct:', currentGalleryProduct);
  
  if (currentGalleryImages.length > 1) {
    if (confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
      const imageToDelete = currentGalleryImages[selectedImageIndex];
      console.log('Imagen a eliminar:', imageToDelete);
      
      // Eliminar del array local
      currentGalleryImages.splice(selectedImageIndex, 1);
      if (selectedImageIndex >= currentGalleryImages.length) {
        selectedImageIndex = currentGalleryImages.length - 1;
      }
      
      try {
        // Actualizar en el backend
        const response = await fetch(`${API_BASE}/api/products/${currentGalleryProduct}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            images: currentGalleryImages
          })
        });
        
        console.log('Respuesta del servidor:', response.status);
        
        if (response.ok) {
          showNotification('Imagen eliminada correctamente', 'success');
          renderGallery();
          // Recargar la lista de productos para reflejar los cambios
          fetchProducts();
        } else {
          const error = await response.json();
          console.error('Error del servidor:', error);
          showNotification(`Error al eliminar imagen: ${error.error}`, 'error');
          // Revertir cambios locales
          currentGalleryImages.splice(selectedImageIndex, 0, imageToDelete);
        }
      } catch (error) {
        console.error('Error en la petición:', error);
        showNotification(`Error al eliminar imagen: ${error.message}`, 'error');
        // Revertir cambios locales
        currentGalleryImages.splice(selectedImageIndex, 0, imageToDelete);
      }
    }
  } else {
    showNotification('No se puede eliminar la única imagen', 'error');
  }
}

function addImages() {
  console.log('addImages llamado');
  const fileInput = document.getElementById('gallery-file-input');
  if (fileInput) {
    console.log('Abriendo selector de archivos');
    fileInput.click();
  } else {
    console.error('No se encontró el input de archivos');
    showNotification('Error: No se encontró el selector de archivos', 'error');
  }
}

async function uploadImagesToGallery(files) {
  console.log('uploadImagesToGallery llamado con archivos:', files);
  console.log('currentGalleryProduct:', currentGalleryProduct);
  
  if (!currentGalleryProduct) {
    showNotification('Error: No hay producto seleccionado', 'error');
    return;
  }

  const progressElement = document.getElementById('upload-progress');
  const progressFill = document.getElementById('progress-fill');
  const progressText = document.getElementById('progress-text');
  
  if (progressElement) {
    progressElement.style.display = 'block';
  }
  if (progressText) {
    progressText.textContent = 'Subiendo imágenes...';
  }
  
  try {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    console.log('Enviando petición a:', `${API_BASE}/api/products/${currentGalleryProduct}/images`);
    const response = await fetch(`${API_BASE}/api/products/${currentGalleryProduct}/images`, {
      method: 'POST',
      body: formData
    });

    console.log('Respuesta del servidor:', response.status);
    const result = await response.json();
    console.log('Resultado:', result);

    if (result.success) {
      showNotification(result.message, 'success');
      // Recargar las imágenes de la galería
      loadProductImages(currentGalleryProduct);
      // Recargar la lista de productos para reflejar los cambios
      fetchProducts();
    } else {
      showNotification(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    showNotification(`Error al subir imágenes: ${error.message}`, 'error');
  } finally {
    progressElement.style.display = 'none';
  }
}

// Eventos de la galería (movidos a setupEventListeners)
// document.addEventListener('DOMContentLoaded', () => {
  // Cerrar galería
  document.querySelector('.gallery-close').addEventListener('click', closeGallery);
  
  // Cerrar al hacer clic fuera
  document.getElementById('gallery-modal').addEventListener('click', (e) => {
    if (e.target.id === 'gallery-modal') {
      closeGallery();
    }
  });
  
  // Botones de acción
  const setMainImageBtn = document.getElementById('set-main-image');
  const deleteImageBtn = document.getElementById('delete-image');
  const addImagesBtn = document.getElementById('add-images');
  
  if (setMainImageBtn) {
    setMainImageBtn.addEventListener('click', setMainImage);
  }
  
  if (deleteImageBtn) {
    deleteImageBtn.addEventListener('click', deleteImage);
  }
  
  if (addImagesBtn) {
    addImagesBtn.addEventListener('click', addImages);
  }
  
  // Subida de archivos
  const galleryFileInput = document.getElementById('gallery-file-input');
  if (galleryFileInput) {
    galleryFileInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        console.log('Archivos seleccionados:', files);
        uploadImagesToGallery(files);
        e.target.value = ''; // Limpiar input
      }
    });
  }
  
  // Drag and drop
  const uploadArea = document.getElementById('gallery-upload');
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });
  
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
  });
  
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      showNotification(`${files.length} imagen(es) agregada(s)`, 'success');
    }
  });
// });

// ==================== GESTIÓN DE USUARIOS ====================

// Variables globales para usuarios
let usersData = [];
let filteredUsers = [];
let currentUserPage = 1;
const usersPerPage = 10;
let editingUserId = null;

// Elementos del DOM para usuarios
const usersPanel = document.getElementById("users-panel");
const productsPanel = document.getElementById("products-panel");
const usersBody = document.getElementById("users-body");
const userModal = document.getElementById("user-modal");
const userForm = document.getElementById("user-form");
const deleteUserModal = document.getElementById("delete-user-modal");
const manageUsersBtn = document.getElementById("manage-users");

// API calls para usuarios
async function fetchUsers() {
  try {
    const authToken = localStorage.getItem('authToken');
    const res = await fetch(`${API_BASE}/api/admin/users`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (!res.ok) {
      throw new Error(`Error HTTP: ${res.status} ${res.statusText}`);
    }
    
    const data = await res.json();
    usersData = data.users;
    filteredUsers = [...usersData];
    renderUsers();
  } catch (err) {
    console.error("Error al cargar usuarios:", err);
    showNotification(`Error al cargar usuarios: ${err.message}`, "error");
  }
}

async function createUser(userData) {
  try {
    const authToken = localStorage.getItem('authToken');
    const res = await fetch(`${API_BASE}/api/admin/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(userData),
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || "Error al crear usuario");
    }
    
    showNotification("Usuario creado correctamente", "success");
    fetchUsers();
    closeUserModal();
  } catch (err) {
    showNotification(`Error al crear usuario: ${err.message}`, "error");
  }
}

async function updateUser(userId, userData) {
  try {
    const authToken = localStorage.getItem('authToken');
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(userData),
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || "Error al actualizar usuario");
    }
    
    showNotification("Usuario actualizado correctamente", "success");
    fetchUsers();
    closeUserModal();
  } catch (err) {
    showNotification(`Error al actualizar usuario: ${err.message}`, "error");
  }
}

async function deleteUser(userId) {
  try {
    const authToken = localStorage.getItem('authToken');
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || "Error al eliminar usuario");
    }
    
    showNotification("Usuario eliminado correctamente", "success");
    fetchUsers();
    closeDeleteUserModal();
  } catch (err) {
    showNotification(`Error al eliminar usuario: ${err.message}`, "error");
  }
}

// Funciones de renderizado de usuarios
function renderUsers() {
  const startIndex = (currentUserPage - 1) * usersPerPage;
  const endIndex = startIndex + usersPerPage;
  const usersToShow = filteredUsers.slice(startIndex, endIndex);
  
  usersBody.innerHTML = usersToShow.map(user => `
    <tr>
      <td>${user.id}</td>
      <td>${user.username}</td>
      <td>${user.nombre || '-'}</td>
      <td>${user.apellido || '-'}</td>
      <td>${user.email || '-'}</td>
      <td><span class="user-role ${user.role}">${user.role}</span></td>
      <td>${formatDate(user.created_at)}</td>
      <td class="user-actions">
        <button class="btn btn-primary" onclick="editUser(${user.id})">✏️ Editar</button>
        <button class="btn btn-danger" onclick="confirmDeleteUser(${user.id}, '${user.username}')">🗑️ Eliminar</button>
      </td>
    </tr>
  `).join('');
  
  renderUsersPagination();
}

function renderUsersPagination() {
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
  const paginationElement = document.getElementById("users-pagination");
  
  if (totalPages <= 1) {
    paginationElement.innerHTML = '';
    return;
  }
  
  let paginationHTML = '<div class="pagination-controls">';
  
  // Botón anterior
  if (currentUserPage > 1) {
    paginationHTML += `<button class="btn btn-secondary" onclick="changeUserPage(${currentUserPage - 1})">Anterior</button>`;
  }
  
  // Números de página
  for (let i = 1; i <= totalPages; i++) {
    if (i === currentUserPage) {
      paginationHTML += `<button class="btn btn-primary" disabled>${i}</button>`;
    } else {
      paginationHTML += `<button class="btn btn-secondary" onclick="changeUserPage(${i})">${i}</button>`;
    }
  }
  
  // Botón siguiente
  if (currentUserPage < totalPages) {
    paginationHTML += `<button class="btn btn-secondary" onclick="changeUserPage(${currentUserPage + 1})">Siguiente</button>`;
  }
  
  paginationHTML += '</div>';
  paginationElement.innerHTML = paginationHTML;
}

function changeUserPage(page) {
  currentUserPage = page;
  renderUsers();
}

// Funciones de modal de usuario
function openUserModal(userId = null) {
  editingUserId = userId;
  const modalTitle = document.getElementById("user-modal-title");
  const passwordField = document.getElementById("user-password");
  
  if (userId) {
    modalTitle.textContent = "Editar Usuario";
    passwordField.required = false;
    passwordField.placeholder = "Dejar vacío para mantener la actual";
    loadUserData(userId);
  } else {
    modalTitle.textContent = "Agregar Nuevo Usuario";
    passwordField.required = true;
    passwordField.placeholder = "Contraseña";
    userForm.reset();
  }
  
  userModal.style.display = "block";
}

function closeUserModal() {
  userModal.style.display = "none";
  editingUserId = null;
  userForm.reset();
}

async function loadUserData(userId) {
  try {
    const authToken = localStorage.getItem('authToken');
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (!res.ok) throw new Error("Error al cargar datos del usuario");
    
    const data = await res.json();
    const user = data.user;
    
    // Llenar el formulario con los datos del usuario
    document.getElementById("user-username").value = user.username || '';
    document.getElementById("user-nombre").value = user.nombre || '';
    document.getElementById("user-apellido").value = user.apellido || '';
    document.getElementById("user-email").value = user.email || '';
    document.getElementById("user-role").value = user.role || 'user';
    document.getElementById("user-dni").value = user.dni || '';
    document.getElementById("user-telefono").value = user.telefono || '';
    document.getElementById("user-direccion").value = user.direccion || '';
    document.getElementById("user-codigo-postal").value = user.codigo_postal || '';
    
  } catch (err) {
    showNotification(`Error al cargar datos del usuario: ${err.message}`, "error");
  }
}

function confirmDeleteUser(userId, username) {
  document.getElementById("delete-user-name").textContent = username;
  document.getElementById("confirm-delete-user").onclick = () => deleteUser(userId);
  deleteUserModal.style.display = "block";
}

function closeDeleteUserModal() {
  deleteUserModal.style.display = "none";
}

function editUser(userId) {
  openUserModal(userId);
}

// Funciones de filtrado de usuarios
function filterUsers() {
  const searchTerm = document.getElementById("user-search").value.toLowerCase();
  const roleFilter = document.getElementById("role-filter").value;
  
  filteredUsers = usersData.filter(user => {
    const matchesSearch = !searchTerm || 
      user.username.toLowerCase().includes(searchTerm) ||
      (user.nombre && user.nombre.toLowerCase().includes(searchTerm)) ||
      (user.apellido && user.apellido.toLowerCase().includes(searchTerm)) ||
      (user.email && user.email.toLowerCase().includes(searchTerm));
    
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    
    return matchesSearch && matchesRole;
  });
  
  currentUserPage = 1;
  renderUsers();
}

// Funciones auxiliares
function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Event listeners para gestión de usuarios (movidos a setupEventListeners)
// document.addEventListener("DOMContentLoaded", () => {
  // Botón para cambiar entre paneles
  manageUsersBtn.addEventListener("click", () => {
    if (usersPanel.style.display === "none") {
      usersPanel.style.display = "block";
      productsPanel.style.display = "none";
      fetchUsers();
    } else {
      usersPanel.style.display = "none";
      productsPanel.style.display = "block";
    }
  });
  
  // Botón para volver a productos
  document.getElementById("back-to-products").addEventListener("click", () => {
    usersPanel.style.display = "none";
    productsPanel.style.display = "block";
  });
  
  // Botón para agregar usuario
  document.getElementById("add-user").addEventListener("click", () => {
    openUserModal();
  });
  
  // Formulario de usuario
  userForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const userData = {
      username: document.getElementById("user-username").value,
      password: document.getElementById("user-password").value,
      nombre: document.getElementById("user-nombre").value,
      apellido: document.getElementById("user-apellido").value,
      email: document.getElementById("user-email").value,
      role: document.getElementById("user-role").value,
      dni: document.getElementById("user-dni").value,
      telefono: document.getElementById("user-telefono").value,
      direccion: document.getElementById("user-direccion").value,
      codigo_postal: document.getElementById("user-codigo-postal").value
    };
    
    if (editingUserId) {
      // Si no se proporcionó contraseña, no incluirla en la actualización
      if (!userData.password) {
        delete userData.password;
      }
      updateUser(editingUserId, userData);
    } else {
      createUser(userData);
    }
  });
  
  // Cerrar modales
  document.getElementById("cancel-user").addEventListener("click", closeUserModal);
  document.getElementById("cancel-delete-user").addEventListener("click", closeDeleteUserModal);
  
  // Filtros de usuarios
  document.getElementById("apply-user-filters").addEventListener("click", filterUsers);
  document.getElementById("reset-user-filters").addEventListener("click", () => {
    document.getElementById("user-search").value = "";
    document.getElementById("role-filter").value = "all";
    filteredUsers = [...usersData];
    currentUserPage = 1;
    renderUsers();
  });
  
  // Cerrar modales al hacer clic fuera
  window.addEventListener("click", (e) => {
    if (e.target === userModal) {
      closeUserModal();
    }
    if (e.target === deleteUserModal) {
      closeDeleteUserModal();
    }
  });
// });

document.addEventListener("DOMContentLoaded", init);