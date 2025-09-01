// ==================== CONFIG ====================
const API_BASE = "http://127.0.0.1:5000";

// ==================== VARIABLES GLOBALES ====================
let productsData = [];
let filteredProducts = [];
let currentPage = 1;
const productsPerPage = 5;

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
    const res = await fetch(`${API_BASE}/api/products`);
    
    if (!res.ok) {
      throw new Error(`Error HTTP: ${res.status} ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log("Datos recibidos:", data);
    
    productsData = data;
    filteredProducts = [...productsData];
    renderProducts();
  } catch (err) {
    console.error("Error al cargar productos:", err);
    showNotification(`Error al cargar productos: ${err.message}`, "error");
    
    // Mostrar datos de ejemplo si la API no está disponible
    productsBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; color: red;">
          Error al conectar con el servidor. Verifica que el servidor esté ejecutándose en ${API_BASE}
          <br><br>
          <button onclick="location.reload()" style="padding: 5px 10px;">Reintentar</button>
        </td>
      </tr>
    `;
  }
}

async function updateProduct(id, updates) {
  try {
    const res = await fetch(`${API_BASE}/api/products/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error("Error al actualizar");
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

// ==================== FUNCIONES DE OPTIMIZACIÓN DE IMÁGENES ====================

async function optimizeImages() {
  try {
    showNotification("Procesando imágenes nuevas...", "info");
    
    const res = await fetch(`${API_BASE}/api/images/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    
    if (!res.ok) throw new Error("Error al optimizar imágenes");
    
    const result = await res.json();
    showNotification(result.message || "Optimización completada", "success");
    
    // Recargar productos para mostrar imágenes optimizadas
    fetchProducts();
    
  } catch (err) {
    showNotification(`Error al optimizar imágenes: ${err.message}`, "error");
  }
}

async function getImageStats() {
  try {
    const res = await fetch(`${API_BASE}/api/images/stats`);
    
    if (!res.ok) throw new Error("Error al obtener estadísticas");
    
    const stats = await res.json();
    
    // Actualizar estadísticas en el modal
    document.getElementById("original-count").textContent = stats.original_images || 0;
    document.getElementById("optimized-count").textContent = stats.optimized_images || 0;
    document.getElementById("original-size").textContent = `${stats.original_size_mb || 0} MB`;
    document.getElementById("optimized-size").textContent = `${stats.optimized_size_mb || 0} MB`;
    document.getElementById("reduction-percent").textContent = `${stats.size_reduction_percent || 0}%`;
    
    // Mostrar modal
    imageStatsModal.style.display = "block";
    
  } catch (err) {
    showNotification(`Error al obtener estadísticas: ${err.message}`, "error");
  }
}

async function cleanupImages() {
  try {
    showNotification("Limpiando optimizaciones obsoletas...", "info");
    
    const res = await fetch(`${API_BASE}/api/images/cleanup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    
    if (!res.ok) throw new Error("Error al limpiar optimizaciones");
    
    const result = await res.json();
    showNotification(result.message || "Limpieza completada", "success");
    
    // Actualizar estadísticas
    getImageStats();
    
  } catch (err) {
    showNotification(`Error al limpiar optimizaciones: ${err.message}`, "error");
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
  let csvContent = "Nombre,Marca,Precio,Categoría,Talles,Stock,Estado,Imagen\n";
  
  productsData.forEach(product => {
    const row = [
      `"${product.name.replace(/"/g, '""')}"`,
      `"${product.brand}"`,
      product.price,
      `"${product.category}"`,
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
  productsBody.innerHTML = "";

  const startIndex = (currentPage - 1) * productsPerPage;
  const endIndex = startIndex + productsPerPage;
  const productsToRender = filteredProducts.slice(startIndex, endIndex);

  if (productsToRender.length === 0) {
    productsBody.innerHTML =
      '<tr><td colspan="9" style="text-align: center;">No se encontraron productos</td></tr>';
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
        <img src="/${product.image}" alt="${product.name}" class="product-image" onclick="openGallery(${product.id}, '${product.name}')"
          onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+'">
        <button class="product-image-gallery-btn" onclick="openGallery(${product.id}, '${product.name}')" title="Ver galería">📷</button>
      </td>
      <td><input type="text" value="${product.name}" data-field="name" data-id="${product.id}"></td>
      <td><input type="text" value="${product.brand}" data-field="brand" data-id="${product.id}"></td>
      <td><input type="number" value="${product.price}" data-field="price" data-id="${product.id}"></td>
      <td><input type="text" value="${product.category}" data-field="category" data-id="${product.id}"></td>
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
          <button class="action-btn save-btn" data-id="${product.id}">💾</button>
          <button class="action-btn delete-btn" data-id="${product.id}">🗑</button>
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
function applyFilters() {
  const searchTerm = document.getElementById("search").value.toLowerCase();
  const categoryFilter = document.getElementById("category").value.toLowerCase();
  const brandFilter = document.getElementById("brand").value.toLowerCase();
  const stockFilter = document.getElementById("stock-filter").value;
  const priceFilter = parseInt(document.getElementById("price-range").value);

  filteredProducts = productsData.filter((product) => {
    if (searchTerm && !product.name.toLowerCase().includes(searchTerm)) return false;
    if (categoryFilter !== "all" && product.category.toLowerCase() !== categoryFilter) return false;
    if (brandFilter !== "all" && product.brand.toLowerCase() !== brandFilter) return false;
    
    // Filtrar por stock
    if (stockFilter !== "all") {
      const stock = product.stock || 0;
      if (stockFilter === "low" && stock > 5) return false;
      if (stockFilter === "medium" && (stock <= 5 || stock > 15)) return false;
      if (stockFilter === "high" && stock <= 15) return false;
      if (stockFilter === "out" && stock > 0) return false;
    }
    
    if (priceFilter && product.price > priceFilter) return false;
    return true;
  });

  currentPage = 1;
  renderProducts();
}

function resetFilters() {
  document.getElementById("search").value = "";
  document.getElementById("category").value = "all";
  document.getElementById("brand").value = "all";
  document.getElementById("stock-filter").value = "all";
  document.getElementById("price-range").value = document.getElementById("price-range").max;
  filteredProducts = [...productsData];
  currentPage = 1;
  renderProducts();
}

// ==================== MODAL ====================
function openAddProductModal() {
  addProductModal.style.display = "block";
}

function closeAddProductModal() {
  addProductModal.style.display = "none";
  newProductForm.reset();
}

// ==================== EVENTOS ====================
function setupEventListeners() {
  document.getElementById("apply-filters").addEventListener("click", applyFilters);
  document.getElementById("reset-filters").addEventListener("click", resetFilters);
  document.getElementById("add-product").addEventListener("click", openAddProductModal);
  document.getElementById("save-all").addEventListener("click", saveAllChanges);
  document.getElementById("export-data").addEventListener("click", exportData);
  
  // Optimizar imágenes
  document.getElementById("optimize-images").addEventListener("click", () => {
    optimizeImages();
  });

  // Ver estadísticas de imágenes
  document.getElementById("image-stats").addEventListener("click", () => {
    getImageStats();
  });

  // Procesar nuevas imágenes desde el modal
  document.getElementById("process-new-images").addEventListener("click", () => {
    optimizeImages();
  });

  // Limpiar optimizaciones desde el modal
  document.getElementById("cleanup-images").addEventListener("click", () => {
    cleanupImages();
  });

  // Cerrar modal de estadísticas
  document.querySelectorAll(".close").forEach(closeBtn => {
    closeBtn.addEventListener("click", () => {
      addProductModal.style.display = "none";
      imageStatsModal.style.display = "none";
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

  document.querySelector(".close").addEventListener("click", closeAddProductModal);

  // Cerrar modal al hacer clic fuera
  window.addEventListener("click", (event) => {
    if (event.target === addProductModal) {
      closeAddProductModal();
    }
  });

  // Formulario para nuevo producto
  newProductForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const newProduct = {
      name: document.getElementById("new-name").value,
      brand: document.getElementById("new-brand").value,
      price: parseFloat(document.getElementById("new-price").value),
      category: document.getElementById("new-category").value,
      sizes: document.getElementById("new-sizes").value.split(",").map(s => s.trim()),
      stock: parseInt(document.getElementById("new-stock").value) || 0,
      image: document.getElementById("new-image").value,
      status: document.getElementById("new-status").value
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
        } else {
          updates[input.dataset.field] = input.value;
        }
      });
      updateProduct(id, updates).then(result => {
        if (result.success) {
          showNotification("Producto actualizado", "success");
          fetchProducts();
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
  
  // Verificar conectividad antes de cargar productos
  checkConnectivity().then(isConnected => {
    if (isConnected) {
      fetchProducts();
      setupEventListeners();
    } else {
      showNotification("No se puede conectar al servidor. Verifica que esté ejecutándose.", "error");
    }
  });
}

// Función para verificar conectividad
async function checkConnectivity() {
  try {
    const response = await fetch(`${API_BASE}/api/health`, { 
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
  // Por ahora, simulamos las imágenes. En un caso real, esto vendría de la API
  const product = productsData.find(p => p.id == productId);
  if (product) {
    // Simular múltiples imágenes basadas en la imagen principal
    currentGalleryImages = [
      product.image,
      product.image.replace('_medium.webp', '_small.webp'),
      product.image.replace('_medium.webp', '_large.webp'),
      product.image.replace('_medium.webp', '_thumb.webp')
    ].filter(img => img !== product.image); // Remover duplicados
    
    // Agregar la imagen principal al inicio
    currentGalleryImages.unshift(product.image);
    
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
  mainImg.src = `/${currentGalleryImages[selectedImageIndex]}`;
  
  // Renderizar miniaturas
  const thumbnailsContainer = document.getElementById('gallery-thumbnails');
  thumbnailsContainer.innerHTML = '';
  
  currentGalleryImages.forEach((image, index) => {
    const thumbnail = document.createElement('img');
    thumbnail.src = `/${image}`;
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

function setMainImage() {
  if (currentGalleryImages.length > 0) {
    const newMainImage = currentGalleryImages[selectedImageIndex];
    // Aquí actualizarías la base de datos
    showNotification('Imagen principal actualizada', 'success');
  }
}

function deleteImage() {
  if (currentGalleryImages.length > 1) {
    if (confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
      currentGalleryImages.splice(selectedImageIndex, 1);
      if (selectedImageIndex >= currentGalleryImages.length) {
        selectedImageIndex = currentGalleryImages.length - 1;
      }
      renderGallery();
      showNotification('Imagen eliminada', 'success');
    }
  } else {
    showNotification('No se puede eliminar la única imagen', 'error');
  }
}

function addImages() {
  document.getElementById('gallery-file-input').click();
}

// Eventos de la galería
document.addEventListener('DOMContentLoaded', () => {
  // Cerrar galería
  document.querySelector('.gallery-close').addEventListener('click', closeGallery);
  
  // Cerrar al hacer clic fuera
  document.getElementById('gallery-modal').addEventListener('click', (e) => {
    if (e.target.id === 'gallery-modal') {
      closeGallery();
    }
  });
  
  // Botones de acción
  document.getElementById('set-main-image').addEventListener('click', setMainImage);
  document.getElementById('delete-image').addEventListener('click', deleteImage);
  document.getElementById('add-images').addEventListener('click', addImages);
  
  // Subida de archivos
  document.getElementById('gallery-file-input').addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      // Aquí procesarías la subida de archivos
      showNotification(`${files.length} imagen(es) agregada(s)`, 'success');
      e.target.value = ''; // Limpiar input
    }
  });
  
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
});

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

// Event listeners para gestión de usuarios
document.addEventListener("DOMContentLoaded", () => {
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
});

document.addEventListener("DOMContentLoaded", init);