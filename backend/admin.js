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
        <td colspan="8" style="text-align: center; color: red;">
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
    showNotification("Producto actualizado", "success");
    fetchProducts();
  } catch (err) {
    showNotification("Error al actualizar producto", "error");
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

// ==================== RENDER ====================
function renderProducts() {
  productsBody.innerHTML = "";

  const startIndex = (currentPage - 1) * productsPerPage;
  const endIndex = startIndex + productsPerPage;
  const productsToRender = filteredProducts.slice(startIndex, endIndex);

  if (productsToRender.length === 0) {
    productsBody.innerHTML =
      '<tr><td colspan="8" style="text-align: center;">No se encontraron productos</td></tr>';
    return;
  }

  productsToRender.forEach((product) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td class="product-image-cell">
        <img src="${product.image}" alt="${product.name}" class="product-image"
          onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiNFRUVFRUUiLz48cGF0aCBkPSJNMTUgMzBINjBWNDBIMzVWMzBIMjVWMTVIMjBWMzBIMTVaIiBmaWxsPSIjOTk5Ii8+PC9zdmc+'">
      </td>
      <td><input type="text" value="${product.name}" data-field="name" data-id="${product.id}"></td>
      <td><input type="text" value="${product.brand}" data-field="brand" data-id="${product.id}"></td>
      <td><input type="number" value="${product.price}" data-field="price" data-id="${product.id}"></td>
      <td><input type="text" value="${product.category}" data-field="category" data-id="${product.id}"></td>
      <td><input type="text" value="${product.sizes ? product.sizes.join(",") : ""}" data-field="sizes" data-id="${product.id}"></td>
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
  const priceFilter = parseInt(document.getElementById("price-range").value);

  filteredProducts = productsData.filter((product) => {
    if (searchTerm && !product.name.toLowerCase().includes(searchTerm)) return false;
    if (categoryFilter !== "all" && product.category.toLowerCase() !== categoryFilter) return false;
    if (brandFilter !== "all" && product.brand.toLowerCase() !== brandFilter) return false;
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
  document.getElementById("price-range").value = document.getElementById("price-range").max;
  filteredProducts = [...productsData];
  currentPage = 1;
  renderProducts();
}

// ==================== EVENTOS ====================
function setupEventListeners() {
  document.getElementById("apply-filters").addEventListener("click", applyFilters);
  document.getElementById("reset-filters").addEventListener("click", resetFilters);

  // Guardar cambios individuales
  productsBody.addEventListener("click", (e) => {
    if (e.target.classList.contains("save-btn")) {
      const id = e.target.dataset.id;
      const rowInputs = document.querySelectorAll(`[data-id="${id}"]`);
      const updates = {};
      rowInputs.forEach((input) => {
        if (input.dataset.field === "sizes") {
          updates["sizes"] = input.value.split(",").map((s) => s.trim());
        } else {
          updates[input.dataset.field] = input.value;
        }
      });
      updateProduct(id, updates);
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
  setTimeout(() => {
    notificationElement.className = "notification";
    notificationElement.textContent = "";
  }, 2500);
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

document.addEventListener("DOMContentLoaded", init);