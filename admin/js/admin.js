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
async function exportData() {
  try {
    // Obtener usuarios si no están cargados
    if (usersData.length === 0) {
      await fetchUsers();
    }
    
    // Crear contenido CSV con mejor organización
    const timestamp = new Date().toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
    
    let csvContent = `# EXPORTACIÓN COMPLETA - WHIP HELMETS\n`;
    csvContent += `# Fecha de exportación: ${timestamp}\n`;
    csvContent += `# Total de productos: ${productsData.length}\n`;
    csvContent += `# Total de usuarios: ${usersData.length}\n`;
    csvContent += `#\n`;
    
    // ========== SECCIÓN DE PRODUCTOS ==========
    csvContent += `# ===========================================\n`;
    csvContent += `# SECCIÓN: PRODUCTOS\n`;
    csvContent += `# ===========================================\n`;
    csvContent += `#\n`;
    csvContent += `# INFORMACIÓN DEL PRODUCTO\n`;
    csvContent += `# ID,Nombre,Marca,Categoría,Condición,Descripción\n`;
    csvContent += `#\n`;
    csvContent += `# PRECIOS Y DESCUENTOS\n`;
    csvContent += `# Precio Normal,Precio con Descuento,% Descuento\n`;
    csvContent += `#\n`;
    csvContent += `# INVENTARIO Y DISPONIBILIDAD\n`;
    csvContent += `# Stock,Estado,Talles Disponibles\n`;
    csvContent += `#\n`;
    csvContent += `# MEDIOS\n`;
    csvContent += `# Imagen Principal,Imágenes Adicionales\n`;
    csvContent += `#\n`;
    csvContent += `# DATOS COMPLETOS DE PRODUCTOS\n`;
    csvContent += `ID,Nombre,Marca,Categoría,Condición,Descripción,Precio Normal,Precio Descuento,% Descuento,Stock,Estado,Talles,Imagen Principal,Imágenes Adicionales,Fecha Creación\n`;
    
    // Agregar datos de productos organizados
    productsData.forEach((product, index) => {
      const precioDescuento = product.porcentaje_descuento 
        ? (product.price * (1 - product.porcentaje_descuento / 100)).toFixed(2)
        : product.price;
      
      const talles = Array.isArray(product.sizes) 
        ? product.sizes.join('; ') 
        : (product.sizes || 'No especificado');
      
      const imagenesAdicionales = Array.isArray(product.images) && product.images.length > 1
        ? product.images.slice(1).join('; ')
        : 'Sin imágenes adicionales';
      
      const fechaCreacion = product.created_at 
        ? new Date(product.created_at).toLocaleDateString('es-ES')
        : 'No disponible';
      
    const row = [
        product.id || (index + 1),
        `"${(product.name || 'Sin nombre').replace(/"/g, '""')}"`,
        `"${product.brand || 'Sin marca'}"`,
        `"${product.category || 'Sin categoría'}"`,
        `"${product.condition || 'Nuevo'}"`,
        `"${(product.description || 'Sin descripción').replace(/"/g, '""')}"`,
        product.price || 0,
        precioDescuento,
        product.porcentaje_descuento || 0,
      product.stock || 0,
        `"${product.status || 'Activo'}"`,
        `"${talles}"`,
        `"${product.image || 'Sin imagen'}"`,
        `"${imagenesAdicionales}"`,
        `"${fechaCreacion}"`
    ];
    csvContent += row.join(',') + '\n';
  });
    
    // ========== SECCIÓN DE USUARIOS ==========
    csvContent += `#\n`;
    csvContent += `# ===========================================\n`;
    csvContent += `# SECCIÓN: USUARIOS\n`;
    csvContent += `# ===========================================\n`;
    csvContent += `#\n`;
    csvContent += `# INFORMACIÓN PERSONAL\n`;
    csvContent += `# ID,Usuario,Nombre,Apellido,Email\n`;
    csvContent += `#\n`;
    csvContent += `# INFORMACIÓN DE CONTACTO\n`;
    csvContent += `# Teléfono,DNI,Código Postal\n`;
    csvContent += `#\n`;
    csvContent += `# INFORMACIÓN DE CUENTA\n`;
    csvContent += `# Rol,Fecha de Registro,Estado\n`;
    csvContent += `#\n`;
    csvContent += `# DATOS COMPLETOS DE USUARIOS\n`;
    csvContent += `ID,Usuario,Nombre,Apellido,Email,Teléfono,DNI,Código Postal,Rol,Fecha Registro,Estado\n`;
    
    // Agregar datos de usuarios organizados
    usersData.forEach((user, index) => {
      const fechaRegistro = user.created_at 
        ? new Date(user.created_at).toLocaleDateString('es-ES')
        : 'No disponible';
      
      const row = [
        user.id || (index + 1),
        `"${user.username || 'Sin usuario'}"`,
        `"${user.nombre || 'Sin nombre'}"`,
        `"${user.apellido || 'Sin apellido'}"`,
        `"${user.email || 'Sin email'}"`,
        `"${user.telefono || 'Sin teléfono'}"`,
        `"${user.dni || 'Sin DNI'}"`,
        `"${user.codigo_postal || 'Sin código postal'}"`,
        `"${user.role || 'Usuario'}"`,
        `"${fechaRegistro}"`,
        `"${user.status || 'Activo'}"`
      ];
      csvContent += row.join(',') + '\n';
    });
    
    // ========== RESUMEN FINAL ==========
    csvContent += `#\n`;
    csvContent += `# ===========================================\n`;
    csvContent += `# RESUMEN DE EXPORTACIÓN\n`;
    csvContent += `# ===========================================\n`;
    csvContent += `#\n`;
    csvContent += `# PRODUCTOS:\n`;
    csvContent += `# Total productos: ${productsData.length}\n`;
    csvContent += `# Productos activos: ${productsData.filter(p => p.status === 'Activo').length}\n`;
    csvContent += `# Productos inactivos: ${productsData.filter(p => p.status === 'Inactivo').length}\n`;
    csvContent += `# Con descuento: ${productsData.filter(p => p.porcentaje_descuento > 0).length}\n`;
    csvContent += `# Sin stock: ${productsData.filter(p => (p.stock || 0) === 0).length}\n`;
    csvContent += `#\n`;
    csvContent += `# USUARIOS:\n`;
    csvContent += `# Total usuarios: ${usersData.length}\n`;
    csvContent += `# Administradores: ${usersData.filter(u => u.role === 'admin').length}\n`;
    csvContent += `# Usuarios normales: ${usersData.filter(u => u.role === 'user').length}\n`;
    csvContent += `# Con email: ${usersData.filter(u => u.email).length}\n`;
    csvContent += `# Con teléfono: ${usersData.filter(u => u.telefono).length}\n`;
  
  // Crear blob y descargar
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
    
    const fileName = `datos_completos_whip_helmets_${new Date().toISOString().split('T')[0]}.csv`;
  
  link.setAttribute("href", url);
    link.setAttribute("download", fileName);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
    showNotification(`Datos exportados correctamente: ${productsData.length} productos y ${usersData.length} usuarios`, "success");
    
  } catch (error) {
    console.error("Error al exportar datos:", error);
    showNotification(`Error al exportar datos: ${error.message}`, "error");
  }
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
      <td><input type="number" value="${product.precio_efectivo || ''}" data-field="precio_efectivo" data-id="${product.id}" min="0" step="0.01" placeholder="Ej: 250000"></td>
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
          <button class="action-btn save-btn" data-id="${product.id}" title="Guardar cambios">Guardar</button>
          <button class="action-btn delete-btn" data-id="${product.id}" title="Eliminar producto">Eliminar</button>
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
      
      console.log(`Búsqueda "${searchTerm}" en:`, {
        name: productName,
        brand: productBrand,
        category: productCategory,
        matchesName,
        matchesBrand,
        matchesCategory
      });
      
      if (!matchesName && !matchesBrand && !matchesCategory) {
        console.log(`Filtrado por búsqueda: no coincide con "${searchTerm}"`);
        return false;
      }
    }
    
    // Filtro de categoría
    if (categoryFilter !== "all") {
      const productCategory = product.category ? product.category.toLowerCase() : '';
      console.log(`Comparando categoría: "${productCategory}" === "${categoryFilter}"`, productCategory === categoryFilter);
      if (productCategory !== categoryFilter) {
        console.log(`Filtrado por categoría: "${product.category}" !== "${categoryFilter}"`);
        return false;
      }
    }
    
    // Filtro de marca
    if (brandFilter !== "all") {
      const productBrand = product.brand ? product.brand.toLowerCase() : '';
      console.log(`Comparando marca:`, {
        productBrand: `"${productBrand}"`,
        brandFilter: `"${brandFilter}"`,
        originalBrand: `"${product.brand}"`,
        match: productBrand === brandFilter
      });
      if (productBrand !== brandFilter) {
        console.log(`Filtrado por marca: "${product.brand}" !== "${brandFilter}"`);
        return false;
      }
    }
    
    // Filtrar por estado - con debug
    if (statusFilter !== "all") {
      const productStatus = product.status || 'Activo'; // Default a 'Activo' si no hay estado
      console.log(`Comparando estado: "${productStatus}" === "${statusFilter}"`, productStatus === statusFilter);
      if (productStatus !== statusFilter) {
        console.log(`Filtrado por estado: "${productStatus}" !== "${statusFilter}"`);
        return false;
      }
    }
    
    // Filtrar por condición
    if (conditionFilter !== "all") {
      const productCondition = product.condition || 'Nuevo'; // Default a 'Nuevo' si no hay condición
      console.log(`Comparando condición: "${productCondition}" === "${conditionFilter}"`, productCondition === conditionFilter);
      if (productCondition !== conditionFilter) {
        console.log(`Filtrado por condición: "${productCondition}" !== "${conditionFilter}"`);
        return false;
      }
    }
    
    // Filtrar por stock
    if (stockFilter !== "all") {
      const stock = product.stock || 0;
      console.log(`Evaluando stock: ${stock} para filtro "${stockFilter}"`);
      
      if (stockFilter === "low" && stock > 5) {
        console.log(`Filtrado por stock bajo: ${stock} > 5`);
        return false;
      }
      if (stockFilter === "medium" && (stock <= 5 || stock > 15)) {
        console.log(`Filtrado por stock medio: ${stock} no está entre 6-15`);
        return false;
      }
      if (stockFilter === "high" && stock <= 15) {
        console.log(`Filtrado por stock alto: ${stock} <= 15`);
        return false;
      }
      if (stockFilter === "out" && stock > 0) {
        console.log(`Filtrado por sin stock: ${stock} > 0`);
        return false;
      }
    }
    
    // Filtrar por precio
    if (priceFilter && priceFilter > 0) {
      const productPrice = product.price || 0;
      console.log(`Evaluando precio: ${productPrice} <= ${priceFilter}`);
      if (productPrice > priceFilter) {
        console.log(`Filtrado por precio: ${productPrice} > ${priceFilter}`);
        return false;
      }
    }
    
    console.log(`Producto "${product.name}" pasa todos los filtros`);
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

  // Calcular porcentaje de descuento automáticamente en formulario de nuevo producto
  const precioEfectivoInput = document.getElementById("new-precio-efectivo");
  const precioNormalInput = document.getElementById("new-price");
  const porcentajeInput = document.getElementById("new-porcentaje-descuento");
  
  if (precioEfectivoInput && precioNormalInput && porcentajeInput) {
    precioEfectivoInput.addEventListener("input", () => {
      const precioEfectivo = parseFloat(precioEfectivoInput.value);
      const precioNormal = parseFloat(precioNormalInput.value);
      
      if (precioEfectivo > 0 && precioNormal > 0) {
        const porcentaje = ((precioNormal - precioEfectivo) / precioNormal) * 100;
        porcentajeInput.value = porcentaje.toFixed(1);
      }
    });
    
    porcentajeInput.addEventListener("input", () => {
      const porcentaje = parseFloat(porcentajeInput.value);
      const precioNormal = parseFloat(precioNormalInput.value);
      
      if (porcentaje >= 0 && precioNormal > 0) {
        const descuento = precioNormal * (porcentaje / 100);
        const precioEfectivo = precioNormal - descuento;
        precioEfectivoInput.value = precioEfectivo.toFixed(2);
      }
    });
    
    precioNormalInput.addEventListener("input", () => {
      const precioNormal = parseFloat(precioNormalInput.value);
      const porcentaje = parseFloat(porcentajeInput.value);
      
      if (precioNormal > 0 && porcentaje > 0) {
        const descuento = precioNormal * (porcentaje / 100);
        const precioEfectivo = precioNormal - descuento;
        precioEfectivoInput.value = precioEfectivo.toFixed(2);
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
      
      // Obtener token CSRF
      const csrfResponse = await fetch(`${API_BASE}/api/csrf-token`);
      const csrfData = await csrfResponse.json();
      const csrfToken = csrfData.csrf_token;
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('csrf_token', csrfToken);

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

      // Obtener token CSRF
      const csrfResponse = await fetch(`${API_BASE}/api/csrf-token`);
      const csrfData = await csrfResponse.json();
      const csrfToken = csrfData.csrf_token;

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
          formData.append('csrf_token', csrfToken);

          const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
          });

          const result = await response.json();

          if (result.success) {
            selectedImages.push(result.file_path);
            document.getElementById(`status-${i}`).innerHTML = "Subida";
            uploadedCount++;
          } else {
            document.getElementById(`status-${i}`).innerHTML = `Error: ${result.error}`;
          }
        } catch (error) {
          document.getElementById(`status-${i}`).innerHTML = `Error: ${error.message}`;
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
      precio_efectivo: document.getElementById("new-precio-efectivo").value ? parseFloat(document.getElementById("new-precio-efectivo").value) : null,
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



  // Calcular porcentaje de descuento automáticamente
  productsBody.addEventListener("input", (e) => {
    if (e.target.dataset.field === "precio_efectivo") {
      const id = e.target.dataset.id;
      const precioEfectivo = parseFloat(e.target.value);
      const precioNormalInput = document.querySelector(`[data-field="price"][data-id="${id}"]`);
      const porcentajeInput = document.querySelector(`[data-field="porcentaje_descuento"][data-id="${id}"]`);
      
      if (precioNormalInput && porcentajeInput && precioEfectivo > 0) {
        const precioNormal = parseFloat(precioNormalInput.value);
        if (precioNormal > 0) {
          const porcentaje = ((precioNormal - precioEfectivo) / precioNormal) * 100;
          porcentajeInput.value = porcentaje.toFixed(1);
        }
      }
    } else if (e.target.dataset.field === "porcentaje_descuento") {
      const id = e.target.dataset.id;
      const porcentaje = parseFloat(e.target.value);
      const precioNormalInput = document.querySelector(`[data-field="price"][data-id="${id}"]`);
      const precioEfectivoInput = document.querySelector(`[data-field="precio_efectivo"][data-id="${id}"]`);
      
      if (precioNormalInput && precioEfectivoInput && porcentaje >= 0) {
        const precioNormal = parseFloat(precioNormalInput.value);
        if (precioNormal > 0) {
          const descuento = precioNormal * (porcentaje / 100);
          const precioEfectivo = precioNormal - descuento;
          precioEfectivoInput.value = precioEfectivo.toFixed(2);
        }
      }
    } else if (e.target.dataset.field === "price") {
      const id = e.target.dataset.id;
      const precioNormal = parseFloat(e.target.value);
      const porcentajeInput = document.querySelector(`[data-field="porcentaje_descuento"][data-id="${id}"]`);
      const precioEfectivoInput = document.querySelector(`[data-field="precio_efectivo"][data-id="${id}"]`);
      
      if (porcentajeInput && precioEfectivoInput && precioNormal > 0) {
        const porcentaje = parseFloat(porcentajeInput.value);
        if (porcentaje > 0) {
          const descuento = precioNormal * (porcentaje / 100);
          const precioEfectivo = precioNormal - descuento;
          precioEfectivoInput.value = precioEfectivo.toFixed(2);
        }
      }
    }
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
        } else if (input.dataset.field === "precio_efectivo") {
          // Solo enviar precio_efectivo si tiene valor
          if (input.value && input.value.trim() !== "") {
            updates["precio_efectivo"] = parseFloat(input.value);
          }
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
  
  // Verificar autenticación primero
  const authToken = localStorage.getItem('authToken');
  if (!authToken) {
    console.log("No hay token de autenticación, redirigiendo al login...");
    showNotification('No hay sesión activa. Redirigiendo al login...', "error");
    setTimeout(() => {
      window.location.href = '/admin';
    }, 2000);
    return;
  }
  
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

async function openGallery(productId, productName) {
  console.log('=== ABRIENDO GALERÍA ===');
  console.log('openGallery llamado para producto:', productId, 'nombre:', productName);
  
  // Validar parámetros
  if (!productId) {
    console.error('ID de producto no proporcionado');
    showNotification('Error: ID de producto no válido', 'error');
    return;
  }
  
  if (!productName) {
    productName = 'Producto';
    console.warn('Nombre de producto no proporcionado, usando valor por defecto');
  }
  
  // Verificar que los elementos del modal existan
  const galleryModal = document.getElementById('gallery-modal');
  const galleryTitle = document.getElementById('gallery-title');
  
  if (!galleryModal) {
    console.error('Modal de galería no encontrado');
    showNotification('Error: Modal de galería no encontrado', 'error');
    return;
  }
  
  if (!galleryTitle) {
    console.error('Título de galería no encontrado');
    showNotification('Error: Título de galería no encontrado', 'error');
    return;
  }
  
  try {
  currentGalleryProduct = productId;
    galleryTitle.textContent = `Galería de Imágenes - ${productName}`;
    
    console.log('Cargando imágenes para producto:', productId);
    // Cargar imágenes desde la API
    await loadProductImages(productId);
    
    console.log('Mostrando modal de galería');
    galleryModal.style.display = 'block';
    
    console.log('Galería abierta exitosamente');
  } catch (error) {
    console.error('Error al abrir galería:', error);
    showNotification(`Error al abrir galería: ${error.message}`, 'error');
  }
}

async function loadProductImages(productId) {
  console.log('=== CARGANDO IMÁGENES DEL PRODUCTO ===');
  console.log('loadProductImages llamado para producto:', productId);
  console.log('API_BASE:', API_BASE);
  
  try {
    // Primero intentar cargar desde la API para obtener datos actualizados
    const url = `${API_BASE}/api/products/${productId}`;
    console.log('Intentando cargar desde URL:', url);
    
    const response = await fetch(url);
    console.log('Respuesta de la API:', response.status, response.statusText);
    
    if (response.ok) {
      const product = await response.json();
      console.log('Producto cargado desde API:', product);
      console.log('Imagen principal:', product.image);
      console.log('Imágenes adicionales:', product.images);
      
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
      console.log('Total de imágenes en galería:', currentGalleryImages.length);
    } else {
      console.log('No se pudo cargar desde API, usando datos locales');
      // Fallback: usar datos locales
  const product = productsData.find(p => p.id == productId);
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
        console.error('Producto no encontrado en datos locales');
        currentGalleryImages = [];
      }
    }
    
    // Asegurar que selectedImageIndex esté dentro del rango
    if (currentGalleryImages.length > 0) {
      selectedImageIndex = Math.min(selectedImageIndex, currentGalleryImages.length - 1);
    } else {
      selectedImageIndex = 0;
    }
    
    console.log('Índice seleccionado ajustado:', selectedImageIndex);
    renderGallery();
  } catch (error) {
    console.error('Error al cargar imágenes del producto:', error);
    console.error('Detalles del error:', error.message);
    
    // Fallback: usar datos locales
    const product = productsData.find(p => p.id == productId);
    console.log('Producto encontrado en fallback:', product);
    
    if (product) {
      currentGalleryImages = [];
      
      // Agregar imagen principal
      if (product.image && product.image.trim() !== '') {
        currentGalleryImages.push(product.image);
        console.log('Imagen principal (fallback) agregada:', product.image);
      }
      
      // Agregar imágenes adicionales
      if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        product.images.forEach((img, index) => {
          if (img && img.trim() !== '' && img !== product.image) {
            currentGalleryImages.push(img);
            console.log(`Imagen adicional ${index} (fallback) agregada:`, img);
          }
        });
      }
      
      console.log('Galería final (fallback):', currentGalleryImages);
    } else {
      console.error('Producto no encontrado en fallback');
      currentGalleryImages = [];
    }
    
    // Asegurar que selectedImageIndex esté dentro del rango
    if (currentGalleryImages.length > 0) {
      selectedImageIndex = Math.min(selectedImageIndex, currentGalleryImages.length - 1);
    } else {
      selectedImageIndex = 0;
    }
    
    renderGallery();
  }
}

function renderGallery() {
  console.log('=== RENDERIZANDO GALERÍA ===');
  console.log('currentGalleryImages:', currentGalleryImages);
  console.log('selectedImageIndex:', selectedImageIndex);
  console.log('Total de imágenes:', currentGalleryImages.length);
  
  const mainImg = document.getElementById('gallery-main-img');
  const thumbnailsContainer = document.getElementById('gallery-thumbnails');
  
  if (!mainImg || !thumbnailsContainer) {
    console.error('Elementos de la galería no encontrados');
    return;
  }
  
  if (currentGalleryImages.length === 0) {
    console.log('No hay imágenes, mostrando placeholder');
    mainImg.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgdmlld0JveD0iMCAwIDQwMCA0MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUwIDIwMEg0MDBWMzAwSDI1MFYyMEgyMDBWMjAwSDE1MFoiIGZpbGw9IiM5OTkiLz48L3N2Zz4=';
    thumbnailsContainer.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No hay imágenes disponibles para este producto</p>';
    return;
  }
  
  // Asegurar que selectedImageIndex esté dentro del rango
  if (selectedImageIndex >= currentGalleryImages.length) {
    selectedImageIndex = 0;
    console.log('Índice seleccionado ajustado a 0');
  }
  
  // Mostrar/ocultar mensaje informativo
  const galleryInfo = document.getElementById('gallery-info');
  if (currentGalleryImages.length > 1) {
    galleryInfo.style.display = 'block';
  } else {
    galleryInfo.style.display = 'none';
  }
  
  // Mostrar imagen principal
  const mainImageUrl = currentGalleryImages[selectedImageIndex];
  console.log('Mostrando imagen principal:', mainImageUrl);
  
  if (mainImageUrl && mainImageUrl.trim() !== '') {
    const fullImageUrl = mainImageUrl.startsWith('http') ? mainImageUrl : `/${mainImageUrl}`;
    mainImg.src = fullImageUrl;
    mainImg.onerror = () => {
      console.error('Error al cargar imagen principal:', fullImageUrl);
      mainImg.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgdmlld0JveD0iMCAwIDQwMCA0MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUwIDIwMEg0MDBWMzAwSDI1MFYyMEgyMDBWMjAwSDE1MFoiIGZpbGw9IiM5OTkiLz48L3N2Zz4=';
    };
  } else {
    console.error('Imagen principal vacía o inválida');
    mainImg.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgdmlld0JveD0iMCAwIDQwMCA0MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUwIDIwMEg0MDBWMzAwSDI1MFYyMEgyMDBWMjAwSDE1MFoiIGZpbGw9IiM5OTkiLz48L3N2Zz4=';
  }
  
  // Renderizar miniaturas con controles de orden
  thumbnailsContainer.innerHTML = '';
  console.log('Renderizando', currentGalleryImages.length, 'miniaturas');
  
  currentGalleryImages.forEach((image, index) => {
    if (image && image.trim() !== '') {
      // Crear contenedor para cada miniatura con controles
      const thumbnailContainer = document.createElement('div');
      thumbnailContainer.className = 'gallery-thumbnail-container';
      
      // Crear la imagen
    const thumbnail = document.createElement('img');
    const imageUrl = image.startsWith('http') ? image : `/${image}`;
    thumbnail.src = imageUrl;
    thumbnail.className = `gallery-thumbnail ${index === selectedImageIndex ? 'active' : ''}`;
      thumbnail.onclick = () => {
        console.log('Seleccionando imagen:', index);
        selectImage(index);
      };
    thumbnail.onerror = () => {
        console.error('Error al cargar miniatura:', imageUrl);
      thumbnail.style.display = 'none';
    };
      
      // Crear controles de orden
      const orderControls = document.createElement('div');
      orderControls.className = 'order-controls';
      
      // Botón para subir (mover hacia arriba)
      const moveUpBtn = document.createElement('button');
      moveUpBtn.className = 'order-btn move-up-btn';
      moveUpBtn.innerHTML = '↑';
      moveUpBtn.title = 'Mover hacia arriba';
      moveUpBtn.disabled = index === 0; // Deshabilitar si es la primera imagen
      moveUpBtn.onclick = (e) => {
        e.stopPropagation();
        moveImageUp(index);
      };
      
      // Botón para bajar (mover hacia abajo)
      const moveDownBtn = document.createElement('button');
      moveDownBtn.className = 'order-btn move-down-btn';
      moveDownBtn.innerHTML = '↓';
      moveDownBtn.title = 'Mover hacia abajo';
      moveDownBtn.disabled = index === currentGalleryImages.length - 1; // Deshabilitar si es la última imagen
      moveDownBtn.onclick = (e) => {
        e.stopPropagation();
        moveImageDown(index);
      };
      
      // Indicador de posición
      const positionIndicator = document.createElement('div');
      positionIndicator.className = 'position-indicator';
      positionIndicator.textContent = `${index + 1}`;
      
      // Agregar elementos al contenedor
      orderControls.appendChild(moveUpBtn);
      orderControls.appendChild(positionIndicator);
      orderControls.appendChild(moveDownBtn);
      
      thumbnailContainer.appendChild(thumbnail);
      thumbnailContainer.appendChild(orderControls);
      thumbnailsContainer.appendChild(thumbnailContainer);
      
      console.log(`Miniatura ${index} agregada con controles:`, imageUrl);
    } else {
      console.warn(`Imagen ${index} vacía o inválida, omitiendo`);
    }
  });
  
  console.log('Galería renderizada exitosamente');
}

function selectImage(index) {
  selectedImageIndex = index;
  renderGallery();
}

// Funciones para reordenar imágenes
function moveImageUp(index) {
  console.log('Moviendo imagen hacia arriba:', index);
  
  if (index > 0) {
    // Intercambiar con la imagen anterior
    const temp = currentGalleryImages[index];
    currentGalleryImages[index] = currentGalleryImages[index - 1];
    currentGalleryImages[index - 1] = temp;
    
    // Actualizar el índice seleccionado si es necesario
    if (selectedImageIndex === index) {
      selectedImageIndex = index - 1;
    } else if (selectedImageIndex === index - 1) {
      selectedImageIndex = index;
    }
    
    console.log('Imagen movida hacia arriba. Nuevo orden:', currentGalleryImages);
    
    // Guardar el nuevo orden en el backend
    saveImageOrder();
    
    // Re-renderizar la galería
    renderGallery();
  }
}

function moveImageDown(index) {
  console.log('Moviendo imagen hacia abajo:', index);
  
  if (index < currentGalleryImages.length - 1) {
    // Intercambiar con la imagen siguiente
    const temp = currentGalleryImages[index];
    currentGalleryImages[index] = currentGalleryImages[index + 1];
    currentGalleryImages[index + 1] = temp;
    
    // Actualizar el índice seleccionado si es necesario
    if (selectedImageIndex === index) {
      selectedImageIndex = index + 1;
    } else if (selectedImageIndex === index + 1) {
      selectedImageIndex = index;
    }
    
    console.log('Imagen movida hacia abajo. Nuevo orden:', currentGalleryImages);
    
    // Guardar el nuevo orden en el backend
    saveImageOrder();
    
    // Re-renderizar la galería
    renderGallery();
  }
}

async function saveImageOrder() {
  if (!currentGalleryProduct) {
    console.error('No hay producto seleccionado para guardar orden');
    return;
  }
  
  try {
    console.log('Guardando nuevo orden de imágenes:', currentGalleryImages);
    
    const response = await fetch(`${API_BASE}/api/products/${currentGalleryProduct}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        images: currentGalleryImages
      })
    });
    
    if (response.ok) {
      console.log('Orden de imágenes guardado exitosamente');
      showNotification('Orden de imágenes actualizado', 'success');
      // Recargar la lista de productos para reflejar los cambios
      fetchProducts();
    } else {
      const error = await response.json();
      console.error('Error al guardar orden:', error);
      showNotification(`Error al guardar orden: ${error.error}`, 'error');
    }
  } catch (error) {
    console.error('Error al guardar orden de imágenes:', error);
    showNotification(`Error al guardar orden: ${error.message}`, 'error');
  }
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
  console.log('=== SUBIENDO IMÁGENES ===');
  console.log('uploadImagesToGallery llamado con archivos:', files);
  console.log('currentGalleryProduct:', currentGalleryProduct);
  console.log('API_BASE:', API_BASE);
  
  if (!currentGalleryProduct) {
    console.error('No hay producto seleccionado');
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
    // Obtener token CSRF
    const csrfResponse = await fetch(`${API_BASE}/api/csrf-token`);
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.csrf_token;

    const formData = new FormData();
    files.forEach((file, index) => {
      console.log(`Agregando archivo ${index}:`, {
        name: file.name,
        size: file.size,
        type: file.type
      });
      formData.append('files', file);
    });
    
    // Agregar token CSRF al FormData
    formData.append('csrf_token', csrfToken);

    const url = `${API_BASE}/api/products/${currentGalleryProduct}/images`;
    console.log('Enviando petición a:', url);
    console.log('FormData entries:', Array.from(formData.entries()));
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    });

    console.log('Respuesta del servidor:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error del servidor:', errorText);
      throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Resultado:', result);

    if (result.success) {
      showNotification(result.message, 'success');
      console.log('Recargando imágenes de la galería...');
      // Recargar las imágenes de la galería
      await loadProductImages(currentGalleryProduct);
      console.log('Recargando lista de productos...');
      // Recargar la lista de productos para reflejar los cambios
      fetchProducts();
    } else {
      console.error('Error en la respuesta:', result.error);
      showNotification(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    console.error('Error al subir imágenes:', error);
    showNotification(`Error al subir imágenes: ${error.message}`, 'error');
  } finally {
    if (progressElement) {
    progressElement.style.display = 'none';
    }
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

// Función para verificar si el token es válido
async function validateAuthToken() {
  try {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      return false;
    }
    
    const res = await fetch(`${API_BASE}/api/auth/validate`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    return res.ok;
  } catch (error) {
    console.error('Error validando token:', error);
    return false;
  }
}

// API calls para usuarios
async function fetchUsers() {
  try {
    const authToken = localStorage.getItem('authToken');
    console.log('Auth token:', authToken ? 'Presente' : 'Ausente');
    
    if (!authToken) {
      showNotification('No hay sesión activa. Por favor, inicia sesión nuevamente.', "error");
      // Redirigir al login
      window.location.href = '/admin';
      return;
    }
    
    const res = await fetch(`${API_BASE}/api/admin/users`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      if (res.status === 401) {
        showNotification('Sesión expirada. Por favor, inicia sesión nuevamente.', "error");
        // Limpiar token y redirigir
        localStorage.removeItem('authToken');
        window.location.href = '/admin';
        return;
      }
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
        <button class="btn btn-primary" onclick="editUser(${user.id})">Editar</button>
        <button class="btn btn-danger" onclick="confirmDeleteUser(${user.id}, '${user.username}')">Eliminar</button>
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
  manageUsersBtn.addEventListener("click", async () => {
    if (usersPanel.style.display === "none") {
      // Verificar autenticación antes de cargar usuarios
      const isValidToken = await validateAuthToken();
      if (!isValidToken) {
        showNotification('Sesión expirada. Por favor, inicia sesión nuevamente.', "error");
        localStorage.removeItem('authToken');
        setTimeout(() => {
          window.location.href = '/admin';
        }, 2000);
        return;
      }
      
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
  
  // Función de validación del formulario de usuario
  function validateUserForm() {
    const username = document.getElementById("user-username").value;
    const password = document.getElementById("user-password").value;
    const email = document.getElementById("user-email").value;
    const dni = document.getElementById("user-dni").value;
    const telefono = document.getElementById("user-telefono").value;
    const codigoPostal = document.getElementById("user-codigo-postal").value;
    
    // Validar contraseña (solo si se está creando un nuevo usuario o se cambió)
    if (!editingUserId && password.length < 8) {
      showNotification("La contraseña debe tener al menos 8 caracteres", "error");
      return false;
    }
    
    if (!editingUserId && password) {
      const hasLetter = /[a-zA-Z]/.test(password);
      const hasNumber = /[0-9]/.test(password);
      if (!hasLetter || !hasNumber) {
        showNotification("La contraseña debe contener al menos una letra y un número", "error");
        return false;
      }
    }
    
    // Validar DNI
    if (dni && !/^[0-9]{8}$/.test(dni)) {
      showNotification("El DNI debe tener exactamente 8 dígitos numéricos", "error");
      return false;
    }
    
    // Validar teléfono
    if (telefono && !/^[0-9]+$/.test(telefono)) {
      showNotification("El teléfono debe contener solo números", "error");
      return false;
    }
    
    // Validar email
    if (email) {
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailPattern.test(email)) {
        showNotification("El formato del email no es válido", "error");
        return false;
      }
    }
    
    // Validar código postal
    if (codigoPostal && !/^[0-9]{4,5}$/.test(codigoPostal)) {
      showNotification("El código postal debe tener entre 4 y 5 dígitos numéricos", "error");
      return false;
    }
    
    return true;
  }
  
  // Formulario de usuario
  userForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    // Validaciones del formulario
    if (!validateUserForm()) {
      return;
    }
    
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

// ==================== GESTIÓN DE PEDIDOS ====================

let ordersData = [];
let filteredOrders = [];
let currentOrderPage = 1;
const ordersPerPage = 10;
let currentOrderId = null;

// Elementos del DOM para pedidos
const ordersBody = document.getElementById("orders-body");
const ordersPagination = document.getElementById("orders-pagination");
const orderDetailsModal = document.getElementById("order-details-modal");

// Función para cargar pedidos
async function fetchOrders() {
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            showNotification('Error: No hay token de autenticación', 'error');
            return;
        }

        const response = await fetch(`${API_BASE}/api/admin/orders`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            ordersData = data.orders;
            filteredOrders = [...ordersData];
            renderOrders();
            showNotification(`Cargados ${ordersData.length} pedidos`, 'success');
        } else {
            throw new Error(data.error || 'Error al cargar pedidos');
        }
    } catch (error) {
        console.error('Error al cargar pedidos:', error);
        showNotification(`Error al cargar pedidos: ${error.message}`, 'error');
    }
}

// Función para renderizar pedidos
function renderOrders() {
    if (!ordersBody) return;

    const startIndex = (currentOrderPage - 1) * ordersPerPage;
    const endIndex = startIndex + ordersPerPage;
    const ordersToShow = filteredOrders.slice(startIndex, endIndex);

    ordersBody.innerHTML = '';

    if (ordersToShow.length === 0) {
        ordersBody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 20px; color: #666;">
                    No se encontraron pedidos
                </td>
            </tr>
        `;
        return;
    }

    ordersToShow.forEach(order => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${order.id}</td>
            <td>${order.order_number}</td>
            <td>${order.customer_name}</td>
            <td>${order.customer_email}</td>
            <td>$${order.total_amount.toLocaleString()}</td>
            <td>
                <span class="payment-method payment-${order.payment_method}">
                    ${order.payment_method === 'transfer' ? 'Transferencia' : 'MercadoPago'}
                </span>
            </td>
            <td>
                <span class="status-badge status-${order.status}">
                    ${getStatusText(order.status)}
                </span>
            </td>
            <td>${formatDate(order.created_at)}</td>
            <td>
                <span class="verification-code" title="Código de verificación del comprobante">
                    ${order.verification_code || 'N/A'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewOrderDetails(${order.id})">
                    Ver Detalles
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteOrder(${order.id})" style="margin-left: 5px;">
                    Eliminar
                </button>
            </td>
        `;
        ordersBody.appendChild(row);
    });

    renderOrdersPagination();
}

// Función para renderizar paginación de pedidos
function renderOrdersPagination() {
    if (!ordersPagination) return;

    const totalPages = Math.ceil(filteredOrders.length / ordersPerPage);
    
    if (totalPages <= 1) {
        ordersPagination.innerHTML = '';
        return;
    }

    let paginationHTML = '<div class="pagination-controls">';
    
    // Botón anterior
    if (currentOrderPage > 1) {
        paginationHTML += `<button class="btn btn-sm" onclick="changeOrderPage(${currentOrderPage - 1})">« Anterior</button>`;
    }
    
    // Números de página
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentOrderPage) {
            paginationHTML += `<button class="btn btn-sm btn-primary">${i}</button>`;
        } else {
            paginationHTML += `<button class="btn btn-sm" onclick="changeOrderPage(${i})">${i}</button>`;
        }
    }
    
    // Botón siguiente
    if (currentOrderPage < totalPages) {
        paginationHTML += `<button class="btn btn-sm" onclick="changeOrderPage(${currentOrderPage + 1})">Siguiente »</button>`;
    }
    
    paginationHTML += '</div>';
    ordersPagination.innerHTML = paginationHTML;
}

// Función para cambiar página de pedidos
function changeOrderPage(page) {
    currentOrderPage = page;
    renderOrders();
}

// Función para ver detalles de un pedido
async function viewOrderDetails(orderId) {
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            showNotification('Error: No hay token de autenticación', 'error');
            return;
        }

        const response = await fetch(`${API_BASE}/api/admin/orders/${orderId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            currentOrderId = orderId;
            displayOrderDetails(data.order);
            orderDetailsModal.style.display = 'block';
        } else {
            throw new Error(data.error || 'Error al cargar detalles del pedido');
        }
    } catch (error) {
        console.error('Error al cargar detalles del pedido:', error);
        showNotification(`Error al cargar detalles: ${error.message}`, 'error');
    }
}

// Función para mostrar detalles del pedido en el modal
function displayOrderDetails(order) {
    // Información básica
    document.getElementById('order-number').textContent = `Pedido #${order.order_number}`;
    document.getElementById('customer-name').textContent = order.customer_name;
    document.getElementById('customer-email').textContent = order.customer_email;
    document.getElementById('customer-phone').textContent = order.customer_phone || '-';
    document.getElementById('customer-address').textContent = order.customer_address || '-';
    document.getElementById('customer-city').textContent = order.customer_city || '-';
    document.getElementById('customer-zip').textContent = order.customer_zip || '-';
    
    // Información del pedido
    document.getElementById('order-date').textContent = formatDate(order.created_at);
    document.getElementById('payment-method').textContent = order.payment_method === 'transfer' ? 'Transferencia' : 'MercadoPago';
    document.getElementById('order-total').textContent = `$${order.total_amount.toLocaleString()}`;
    document.getElementById('order-status').textContent = getStatusText(order.status);
    
    // Estado actual
    const statusBadge = document.getElementById('order-status-badge');
    statusBadge.textContent = getStatusText(order.status);
    statusBadge.className = `status-badge status-${order.status}`;
    
    // Selector de estado
    document.getElementById('new-order-status').value = order.status;
    
    // Items del pedido
    const itemsList = document.getElementById('order-items-list');
    itemsList.innerHTML = '';
    
    order.items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'order-item';
        itemDiv.innerHTML = `
            <img src="${item.image || '/assets/images/placeholder.jpg'}" alt="${item.name}" class="order-item-image" onerror="this.src='/assets/images/placeholder.jpg'">
            <div class="order-item-info">
                <div class="order-item-name">${item.name}</div>
                <div class="order-item-details">
                    Marca: ${item.brand} | Cantidad: ${item.quantity} | Precio unitario: $${item.price.toLocaleString()}
                </div>
            </div>
            <div class="order-item-price">
                $${(item.price * item.quantity).toLocaleString()}
            </div>
        `;
        itemsList.appendChild(itemDiv);
    });
}

// Función para actualizar estado del pedido
async function updateOrderStatus() {
    if (!currentOrderId) return;
    
    const newStatus = document.getElementById('new-order-status').value;
    
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            showNotification('Error: No hay token de autenticación', 'error');
            return;
        }

        const response = await fetch(`${API_BASE}/api/admin/orders/${currentOrderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            showNotification(data.message, 'success');
            orderDetailsModal.style.display = 'none';
            fetchOrders(); // Recargar lista de pedidos
        } else {
            throw new Error(data.error || 'Error al actualizar estado');
        }
    } catch (error) {
        console.error('Error al actualizar estado del pedido:', error);
        showNotification(`Error al actualizar estado: ${error.message}`, 'error');
    }
}

// Función para aplicar filtros de pedidos
function applyOrderFilters() {
    const searchTerm = document.getElementById('order-search').value.toLowerCase();
    const statusFilter = document.getElementById('order-status-filter').value;
    const paymentFilter = document.getElementById('payment-method-filter').value;

    filteredOrders = ordersData.filter(order => {
        const matchesSearch = !searchTerm || 
            order.order_number.toLowerCase().includes(searchTerm) ||
            order.customer_name.toLowerCase().includes(searchTerm) ||
            order.customer_email.toLowerCase().includes(searchTerm);
        
        const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
        const matchesPayment = paymentFilter === 'all' || order.payment_method === paymentFilter;
        
        return matchesSearch && matchesStatus && matchesPayment;
    });

    currentOrderPage = 1;
    renderOrders();
}

// Función para resetear filtros de pedidos
function resetOrderFilters() {
    document.getElementById('order-search').value = '';
    document.getElementById('order-status-filter').value = 'all';
    document.getElementById('payment-method-filter').value = 'all';
    
    filteredOrders = [...ordersData];
    currentOrderPage = 1;
    renderOrders();
}

// Función auxiliar para obtener texto del estado
function getStatusText(status) {
    const statusMap = {
        'pending': 'Pendiente',
        'pending_transfer': 'Pendiente Transferencia',
        'paid': 'Pagado',
        'shipped': 'Enviado',
        'delivered': 'Entregado',
        'cancelled': 'Cancelado'
    };
    return statusMap[status] || status;
}

// Función para eliminar un pedido
async function deleteOrder(orderId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este pedido? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            showNotification('Error: No hay token de autenticación', 'error');
            return;
        }

        const response = await fetch(`${API_BASE}/api/admin/orders/${orderId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            showNotification('Pedido eliminado exitosamente', 'success');
            fetchOrders(); // Recargar lista de pedidos
        } else {
            throw new Error(data.error || 'Error al eliminar pedido');
        }
    } catch (error) {
        console.error('Error al eliminar pedido:', error);
        showNotification(`Error al eliminar pedido: ${error.message}`, 'error');
    }
}

// Función auxiliar para formatear fecha
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Event listeners para pedidos
document.addEventListener('DOMContentLoaded', function() {
    // Botón para gestionar pedidos
    const manageOrdersBtn = document.getElementById('manage-orders');
    if (manageOrdersBtn) {
        manageOrdersBtn.addEventListener('click', function() {
            document.getElementById('products-panel').style.display = 'none';
            document.getElementById('users-panel').style.display = 'none';
            document.getElementById('orders-panel').style.display = 'block';
            fetchOrders();
        });
    }

    // Botón para volver a productos desde pedidos
    const backToProductsFromOrdersBtn = document.getElementById('back-to-products-from-orders');
    if (backToProductsFromOrdersBtn) {
        backToProductsFromOrdersBtn.addEventListener('click', function() {
            document.getElementById('orders-panel').style.display = 'none';
            document.getElementById('products-panel').style.display = 'block';
        });
    }

    // Botón para actualizar pedidos
    const refreshOrdersBtn = document.getElementById('refresh-orders');
    if (refreshOrdersBtn) {
        refreshOrdersBtn.addEventListener('click', fetchOrders);
    }

    // Filtros de pedidos
    const applyOrderFiltersBtn = document.getElementById('apply-order-filters');
    if (applyOrderFiltersBtn) {
        applyOrderFiltersBtn.addEventListener('click', applyOrderFilters);
    }

    const resetOrderFiltersBtn = document.getElementById('reset-order-filters');
    if (resetOrderFiltersBtn) {
        resetOrderFiltersBtn.addEventListener('click', resetOrderFilters);
    }

    // Actualizar estado del pedido
    const updateOrderStatusBtn = document.getElementById('update-order-status');
    if (updateOrderStatusBtn) {
        updateOrderStatusBtn.addEventListener('click', updateOrderStatus);
    }

    // Cerrar modal de detalles de pedido
    const orderDetailsModalClose = orderDetailsModal?.querySelector('.close');
    if (orderDetailsModalClose) {
        orderDetailsModalClose.addEventListener('click', function() {
            orderDetailsModal.style.display = 'none';
        });
    }

    // Cerrar modal al hacer clic fuera
    if (orderDetailsModal) {
        window.addEventListener('click', function(e) {
            if (e.target === orderDetailsModal) {
                orderDetailsModal.style.display = 'none';
            }
        });
    }
});

document.addEventListener("DOMContentLoaded", init);