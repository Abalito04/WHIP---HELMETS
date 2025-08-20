document.addEventListener("DOMContentLoaded", () => {
  // ==================== VARIABLES ====================
  const cartCountEl = document.querySelector(".cart");
  const productCards = document.querySelectorAll(".product-card");
  const cartModal = document.getElementById("cart-modal");
  const cartItemsContainer = document.getElementById("cart-items");
  const cartTotalEl = document.getElementById("cart-total");
  const cartClose = cartModal.querySelector(".close-cart");
  let cart = JSON.parse(localStorage.getItem("cart_v1")) || [];

  // Mini Carrito variables
  const miniCart = document.getElementById("mini-cart");
  const miniCartCount = document.getElementById("mini-cart-count");
  const miniCartDropdown = document.getElementById("mini-cart-dropdown");
  const miniCartItems = document.getElementById("mini-cart-items");
  const miniCartTotal = document.getElementById("mini-cart-total");
  const miniCartClear = document.getElementById("mini-cart-clear");

  // ==================== FUNCIONES ====================
  const updateCartCount = () => {
    cartCountEl.textContent = `🛒 Carrito (${cart.length})`;
    miniCartCount.textContent = cart.length; // Actualizar el mini carrito
  };

  const formatPrice = (price) => {
    return `$${price.toLocaleString('es-ES')}`;
  };

  const renderCartItems = () => {
    cartItemsContainer.innerHTML = "";
    if (!cart.length) {
      cartItemsContainer.innerHTML = "<p style='text-align:center;'>Tu carrito está vacío</p>";
      cartTotalEl.textContent = "Total: $0";
      return;
    }
    
    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.textAlign = "center";
    table.style.borderCollapse = "collapse";
    table.style.marginBottom = "15px";

    const thead = document.createElement("thead");
    thead.innerHTML = `
      <tr>
        <th style="padding:8px;border-bottom:1px solid #f0a946;">Producto</th>
        <th style="padding:8px;border-bottom:1px solid #f0a946;">Talle</th>
        <th style="padding:8px;border-bottom:1px solid #f0a946;">Precio</th>
        <th style="padding:8px;border-bottom:1px solid #f0a946;">Eliminar</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    cart.forEach((item, index) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:8px;border-bottom:1px solid #444;">${item.productName}</td>
        <td style="padding:8px;border-bottom:1px solid #444;">${item.size}</td>
        <td style="padding:8px;border-bottom:1px solid #444;">${formatPrice(item.price)}</td>
        <td style="padding:8px;border-bottom:1px solid #444;">
          <button class="remove-item" data-index="${index}">X</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    cartItemsContainer.appendChild(table);

    // Calcular total
    const total = cart.reduce((sum, item) => sum + item.price, 0);
    cartTotalEl.textContent = `Total: ${formatPrice(total)}`;

    // Botón "Eliminar todo"
    const existingClearBtn = cartModal.querySelector(".clear-cart-btn");
    if (existingClearBtn) existingClearBtn.remove();
    
    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Eliminar todo";
    clearBtn.className = "clear-cart-btn";
    clearBtn.style.cssText = "margin-top:10px;padding:10px 20px;background:#d9534f;border:none;border-radius:5px;cursor:pointer;";
    clearBtn.addEventListener("click", () => {
      cart = [];
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
    });
    cartItemsContainer.appendChild(clearBtn);
  };

  const updateMiniCart = () => {
    // Actualizar el contador
    miniCartCount.textContent = cart.length;
    
    // Actualizar el dropdown
    miniCartItems.innerHTML = "";
    if (!cart.length) {
      miniCartItems.innerHTML = "<p style='text-align:center; padding:10px;'>Carrito vacío</p>";
      miniCartTotal.textContent = "Total: $0";
      return;
    }
    
    let total = 0;
    cart.forEach((item, index) => {
      total += item.price;
      
      const itemEl = document.createElement("div");
      itemEl.className = "mini-cart-item";
      itemEl.innerHTML = `
        <div class="mini-cart-item-details">
          <div class="mini-cart-item-name">${item.productName}</div>
          <div class="mini-cart-item-size">Talle: ${item.size}</div>
          <div class="mini-cart-item-price">${formatPrice(item.price)}</div>
        </div>
        <button class="remove-item" data-index="${index}">X</button>
      `;
      miniCartItems.appendChild(itemEl);
    });
    
    miniCartTotal.textContent = `Total: ${formatPrice(total)}`;
  };

  const showMiniNotification = msg => {
    const notif = document.createElement("div");
    notif.textContent = msg;
    notif.style.cssText = `
      position:fixed; bottom:20px; right:20px;
      background:#f0ad4e; color:#000; padding:10px 20px;
      border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.2);
      z-index:2000; opacity:0; transition:opacity 0.3s ease;
    `;
    document.body.appendChild(notif);
    requestAnimationFrame(() => notif.style.opacity = "1");
    setTimeout(() => { notif.style.opacity = "0"; setTimeout(() => notif.remove(), 300); }, 1500);
  };

  const parsePrice = (priceString) => {
    // Eliminar símbolo $ y puntos de separación de miles
    const cleanString = priceString.replace('$', '').replace(/\./g, '');
    // Convertir a número (reemplazar coma decimal por punto si es necesario)
    return parseFloat(cleanString.replace(',', '.'));
  };

  const addToCart = (productName, priceString, size) => {
    const price = parsePrice(priceString);
    cart.push({ productName, price, size });
    localStorage.setItem("cart_v1", JSON.stringify(cart));
    updateCartCount();
    renderCartItems();
    updateMiniCart();
    showMiniNotification(`${productName} (${size}) agregado al carrito`);
  };

  // ==================== EVENTOS ====================
  cartCountEl.addEventListener("click", () => {
    renderCartItems();
    cartModal.style.display = "flex";
    miniCartDropdown.classList.remove("active"); // Cerrar mini carrito si se abre el modal
  });

  cartClose.addEventListener("click", () => cartModal.style.display = "none");
  cartModal.addEventListener("click", e => { 
    if (e.target === cartModal) cartModal.style.display = "none"; 
  });

  // Eventos para el mini carrito
  miniCart.addEventListener("click", (e) => {
    e.stopPropagation();
    miniCartDropdown.classList.toggle("active");
  });

  // Cerrar el mini carrito al hacer clic fuera
  document.addEventListener("click", (e) => {
    if (!miniCart.contains(e.target) && !miniCartDropdown.contains(e.target)) {
      miniCartDropdown.classList.remove("active");
    }
  });

  // Eliminar items desde el mini carrito
  miniCartItems.addEventListener("click", e => {
    if (e.target.classList.contains("remove-item")) {
      const index = e.target.dataset.index;
      cart.splice(index, 1);
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
    }
  });

  // Vaciar carrito desde el mini carrito
  miniCartClear.addEventListener("click", () => {
    cart = [];
    localStorage.setItem("cart_v1", JSON.stringify(cart));
    updateCartCount();
    renderCartItems();
    updateMiniCart();
  });

  // Eliminar items desde el modal del carrito
  cartItemsContainer.addEventListener("click", e => {
    if (e.target.classList.contains("remove-item")) {
      const index = e.target.dataset.index;
      cart.splice(index, 1);
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
    }
  });

  // ==================== PRODUCTOS ====================
  productCards.forEach(card => {
    const button = card.querySelector("button");
    const productName = card.querySelector("h3").textContent;
    const priceEl = card.querySelector(".price");
    const priceString = priceEl.textContent;
    const select = card.querySelector("select.size-selector");

    button.addEventListener("click", e => {
      e.stopPropagation();
      const size = select ? select.value : "";
      addToCart(productName, priceString, size);
    });
  });

  // ==================== FILTRO DE MARCAS ====================
  const brands = Array.from(new Set([...productCards].map(c => c.dataset.brand))).filter(b => b);
  if (brands.length) {
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
    document.querySelector("main").insertBefore(filterContainer, document.querySelector("#destacados"));

    selectFilter.addEventListener("change", () => {
      const selected = selectFilter.value;
      productCards.forEach(card => {
        card.style.display = (selected === "Todas" || card.dataset.brand === selected) ? "block" : "none";
      });
    });
  }

  // ==================== MODAL DE PRODUCTO ====================
  const productModal = document.createElement("div");
  productModal.id = "product-modal";
  productModal.style.cssText = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);justify-content:center;align-items:center;z-index:1000;";
  productModal.innerHTML = `
    <div id="modal-content" style="position:relative; max-width:700px; width:90%; background:#fff; border-radius:10px; padding:20px; display:flex; flex-direction:column; align-items:center;">
      <span id="modal-close" style="position:absolute; top:10px; right:20px; cursor:pointer; font-size:24px;">&times;</span>
      <img id="modal-main-image" src="" style="width:100%; max-height:500px; object-fit:contain; border-radius:10px;">
      <div id="modal-thumbnails" style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center;"></div>
    </div>
  `;
  document.body.appendChild(productModal);

  const modalClose = document.getElementById("modal-close");
  const modalMainImage = document.getElementById("modal-main-image");
  const modalThumbnails = document.getElementById("modal-thumbnails");

  let currentImages = [];
  let currentIndex = 0;

  const updateThumbnails = () => {
    Array.from(modalThumbnails.children).forEach((thumb, idx) => {
      thumb.style.border = idx === currentIndex ? "2px solid #f0ad4e" : "1px solid #ccc";
    });
  };

  const openProductModal = card => {
    currentImages = Array.from(card.querySelectorAll(".product-image")).map(img => img.src);
    currentIndex = 0;
    modalMainImage.src = currentImages[currentIndex];
    modalThumbnails.innerHTML = "";
    currentImages.forEach((src, idx) => {
      const thumb = document.createElement("img");
      thumb.src = src;
      thumb.style.cssText = `width:80px; cursor:pointer; border:${idx === currentIndex ? "2px solid #f0ad4e" : "1px solid #ccc"}; border-radius:5px;`;
      thumb.addEventListener("click", () => {
        currentIndex = idx;
        modalMainImage.src = currentImages[currentIndex];
        updateThumbnails();
      });
      modalThumbnails.appendChild(thumb);
    });
    productModal.style.display = "flex";
  };

  modalClose.addEventListener("click", () => productModal.style.display = "none");
  productModal.addEventListener("click", e => { if (e.target === productModal) productModal.style.display = "none"; });

  productCards.forEach(card => {
    card.addEventListener("click", e => {
      if (e.target.classList.contains("product-image")) openProductModal(card);
    });
  });

  // ==================== MODAL LOGIN ====================
  const loginLink = document.querySelector(".login");

  // Crear modal
  const loginModal = document.createElement("div");
  loginModal.id = "login-modal";
  loginModal.style.display = "none"; // aseguramos que esté oculto
  loginModal.innerHTML = `
    <div class="login-content">
      <span class="close-login">&times;</span>
      <h2>Iniciar Sesión</h2>
      <form id="login-form" style="width:100%; display:flex; flex-direction:column; gap:10px;">
        <input type="text" placeholder="Usuario" required>
        <input type="password" placeholder="Contraseña" required>
        <button type="submit" id="login-submit">Entrar</button>
        <button type="button" id="register-btn">Registrarse</button>
      </form>
    </div>
  `;
  document.body.appendChild(loginModal);

  // Abrir modal solo al hacer click
  if (loginLink) {
    loginLink.addEventListener("click", e => {
      e.preventDefault();
      loginModal.style.display = "flex";
    });
  }

  // Cerrar modal al hacer click en la X
  const closeLogin = loginModal.querySelector(".close-login");
  closeLogin.addEventListener("click", () => {
    loginModal.style.display = "none";
  });

  // Cerrar modal al hacer click fuera del contenido
  loginModal.addEventListener("click", e => {
    if (e.target === loginModal) {
      loginModal.style.display = "none";
    }
  });

  // Evento login (solo simulación)
  const loginForm = document.getElementById("login-form");
  loginForm.addEventListener("submit", e => {
    e.preventDefault();
    alert("¡Login exitoso!");
    loginModal.style.display = "none";
  });

  // Botón registrarse
  const registerBtn = document.getElementById("register-btn");
  registerBtn.addEventListener("click", () => {
    alert("Redirigiendo al formulario de registro...");
  });
// Agregar al final del archivo script.js

// ==================== SISTEMA DE ACCESO AL ADMIN ====================
function setupAdminAccess() {
    // Verificar si ya está logueado
    if (localStorage.getItem('admin_logged_in') === 'true') {
        // Si ya está logueado, redirigir al admin
        window.location.href = '../backend/admin.html';
        return;
    }
    
    // Crear modal de acceso admin
    const adminAccessModal = document.createElement('div');
    adminAccessModal.id = 'admin-access-modal';
    adminAccessModal.style.cssText = `
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.7);
        justify-content: center;
        align-items: center;
        z-index: 2000;
    `;
    
    adminAccessModal.innerHTML = `
        <div style="background: #222; padding: 20px; border-radius: 10px; width: 300px; text-align: center;">
            <h2 style="color: #f0ad4e; margin-top: 0;">Acceso Administrador</h2>
            <input type="password" id="admin-password" placeholder="Contraseña de administrador" 
                   style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none;">
            <div style="display: flex; justify-content: space-between;">
                <button id="admin-login-btn" style="background: #f0ad4e; color: #000; border: none; padding: 10px 20px; 
                        border-radius: 5px; cursor: pointer;">Acceder</button>
                <button id="admin-cancel-btn" style="background: #666; color: #fff; border: none; padding: 10px 20px; 
                        border-radius: 5px; cursor: pointer;">Cancelar</button>
            </div>
            <p id="admin-login-message" style="color: #ff4444; margin: 10px 0 0; font-size: 14px;"></p>
        </div>
    `;
    
    document.body.appendChild(adminAccessModal);
    
    // Mostrar modal al hacer clic en el logo 5 veces
    let clickCount = 0;
    let clickTimeout;
    
    document.querySelector('.logo').addEventListener('click', function() {
        clearTimeout(clickTimeout);
        clickCount++;
        
        if (clickCount === 5) {
            adminAccessModal.style.display = 'flex';
            clickCount = 0;
        }
        
        clickTimeout = setTimeout(() => {
            clickCount = 0;
        }, 2000);
    });
    
    // Eventos para los botones del modal
    document.getElementById('admin-login-btn').addEventListener('click', function() {
        const password = document.getElementById('admin-password').value;
        
        // Verificar contraseña (en producción esto debería ser más seguro)
        if (password === 'admin123') {
            localStorage.setItem('admin_logged_in', 'true');
            window.location.href = '../backend/admin.html';
        } else {
            document.getElementById('admin-login-message').textContent = 'Contraseña incorrecta';
        }
    });
    
    document.getElementById('admin-cancel-btn').addEventListener('click', function() {
        adminAccessModal.style.display = 'none';
        document.getElementById('admin-password').value = '';
        document.getElementById('admin-login-message').textContent = '';
    });
}

// Inicializar el sistema de acceso al admin
document.addEventListener('DOMContentLoaded', function() {
    // Tu código existente aquí...

  // ==================== INICIALIZAR ====================
  cartModal.style.display = "none";
  updateCartCount();
  renderCartItems();
  updateMiniCart(); // Inicializar el mini carrito
  setupAdminAccess();
});
});