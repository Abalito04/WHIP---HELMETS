document.addEventListener("DOMContentLoaded", () => {
  // ==================== VARIABLES ====================
  const cartCountEl = document.querySelector(".cart");
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
    if (cartCountEl) {
      cartCountEl.textContent = `🛒 Carrito (${cart.length})`;
    }
    if (miniCartCount) {
      miniCartCount.textContent = cart.length;
    }
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
    if (miniCartCount) {
      miniCartCount.textContent = cart.length;
    }
    
    // Actualizar el dropdown
    if (miniCartItems) {
      miniCartItems.innerHTML = "";
      if (!cart.length) {
        miniCartItems.innerHTML = "<p style='text-align:center; padding:10px;'>Carrito vacío</p>";
        if (miniCartTotal) miniCartTotal.textContent = "Total: $0";
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
      
      if (miniCartTotal) {
        miniCartTotal.textContent = `Total: ${formatPrice(total)}`;
      }
    }
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

  // Función para añadir productos al carrito (ahora será llamada desde shop.js)
  window.addToCart = (productName, price, size) => {
    cart.push({ productName, price, size });
    localStorage.setItem("cart_v1", JSON.stringify(cart));
    updateCartCount();
    renderCartItems();
    updateMiniCart();
    showMiniNotification(`${productName} (${size}) agregado al carrito`);
  };

  // ==================== EVENTOS ====================
  if (cartCountEl) {
    cartCountEl.addEventListener("click", () => {
      renderCartItems();
      cartModal.style.display = "flex";
      if (miniCartDropdown) miniCartDropdown.classList.remove("active");
    });
  }

  if (cartClose) {
    cartClose.addEventListener("click", () => cartModal.style.display = "none");
  }
  
  if (cartModal) {
    cartModal.addEventListener("click", e => { 
      if (e.target === cartModal) cartModal.style.display = "none"; 
    });
  }

  // Eventos para el mini carrito
  if (miniCart) {
    miniCart.addEventListener("click", (e) => {
      e.stopPropagation();
      if (miniCartDropdown) miniCartDropdown.classList.toggle("active");
    });
  }

  // Cerrar el mini carrito al hacer clic fuera
  document.addEventListener("click", (e) => {
    if (miniCart && !miniCart.contains(e.target) && miniCartDropdown && !miniCartDropdown.contains(e.target)) {
      miniCartDropdown.classList.remove("active");
    }
  });

  // Eliminar items desde el mini carrito
  if (miniCartItems) {
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
  }

  // Vaciar carrito desde el mini carrito
  if (miniCartClear) {
    miniCartClear.addEventListener("click", () => {
      cart = [];
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
    });
  }

  // Eliminar items desde el modal del carrito
  if (cartItemsContainer) {
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
  }

  // ==================== MODAL LOGIN ====================
  const loginLink = document.querySelector(".login");

  // Crear modal
  const loginModal = document.createElement("div");
  loginModal.id = "login-modal";
  loginModal.style.display = "none";
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
  if (closeLogin) {
    closeLogin.addEventListener("click", () => {
      loginModal.style.display = "none";
    });
  }

  // Cerrar modal al hacer click fuera del contenido
  loginModal.addEventListener("click", e => {
    if (e.target === loginModal) {
      loginModal.style.display = "none";
    }
  });

  // Evento login (solo simulación)
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", e => {
      e.preventDefault();
      alert("¡Login exitoso!");
      loginModal.style.display = "none";
    });
  }

  // Botón registrarse
  const registerBtn = document.getElementById("register-btn");
  if (registerBtn) {
    registerBtn.addEventListener("click", () => {
      alert("Redirigiendo al formulario de registro...");
    });
  }

  // ==================== INICIALIZAR ====================
  if (cartModal) cartModal.style.display = "none";
  updateCartCount();
  renderCartItems();
  updateMiniCart();
});