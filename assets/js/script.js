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

  // Login variables
  const loginLink = document.querySelector(".login");
  const loginModal = document.getElementById('login-modal');
  let isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
  let userEmail = localStorage.getItem("userEmail") || "";
  const loginForm = document.getElementById('login-form');
  const closeLogin = document.querySelector('.close-login');
  let currentUser = null;
  
  // Verificar sesión al cargar
  checkAuthStatus();

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
    const checkoutBtn = document.getElementById("checkout-btn");
    
    if (!cart.length) {
      cartItemsContainer.innerHTML = "<p style='text-align:center;'>Tu carrito está vacío</p>";
      cartTotalEl.textContent = "Total: $0";
      if (checkoutBtn) checkoutBtn.style.display = "none";
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
    
    // Mostrar botón de checkout
    if (checkoutBtn) checkoutBtn.style.display = "block";

    // Botón "Eliminar todo"
    const existingClearBtn = cartModal.querySelector(".clear-cart-btn");
    if (existingClearBtn) existingClearBtn.remove();
    
    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Eliminar todo";
    clearBtn.className = "clear-cart-btn";
    clearBtn.style.cssText = "margin-top:10px;padding:10px 20px;background:#d9534f;border:none;border-radius:5px;cursor:pointer;";
    clearBtn.addEventListener("click", () => {
      // Guardar información de los productos para actualizar el stock
      const removedItems = [...cart];
      
      cart = [];
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
      
      // Actualizar la UI de stock para todos los productos eliminados
      if (typeof window.updateProductStockUI === 'function') {
        removedItems.forEach(item => {
          window.updateProductStockUI(item.productId, item.size);
        });
      }
      
      // Ocultar botón de checkout si no hay items
      showCheckoutButton();
    });
    cartItemsContainer.appendChild(clearBtn);
    
    // Mostrar botón de checkout
    showCheckoutButton();
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
  
  // Función para mostrar/ocultar botón de checkout
  const showCheckoutButton = () => {
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
      if (cart.length > 0) {
        checkoutBtn.style.display = 'block';
      } else {
        checkoutBtn.style.display = 'none';
      }
    }
  };

  // Función para añadir productos al carrito (modificada para verificar stock)
  window.addToCart = (productName, price, size, productId) => {
    // Primero verificar si hay stock disponible
    const stockDisponible = window.checkStockAvailable(productId, size);
    
    if (stockDisponible) {
      cart.push({ productName, price, size, productId });
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
      showMiniNotification(`${productName} (${size}) agregado al carrito`);
      
      // Actualizar la UI para reflejar el cambio de stock
      if (typeof window.updateProductStockUI === 'function') {
        window.updateProductStockUI(productId, size);
      }
      
      // Mostrar botón de checkout si hay items en el carrito
      showCheckoutButton();
      return true;
    } else {
      showMiniNotification("No hay suficiente stock disponible");
      return false;
    }
  };

  // Función para actualizar la UI de login (DEPRECATED - usar updateLoginButton)
  const updateLoginUI = () => {
    // Esta función está deprecada, usar updateLoginButton en su lugar
    updateLoginButton();
  };

  // Función para manejar login
  const handleLogin = (email, password) => {
    // Simulación de autenticación (en un caso real, se conectaría a una API)
    if (email && password) {
      isLoggedIn = true;
      userEmail = email;
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("userEmail", email);
      updateLoginUI();
      return true;
    }
    return false;
  };

  // Función para manejar logout
  const handleLogout = () => {
    isLoggedIn = false;
    userEmail = "";
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("userEmail");
    updateLoginUI();
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
  
  // Evento para el botón de checkout
  const checkoutBtn = document.getElementById('checkout-btn');
  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', () => {
      // Verificar si el usuario está autenticado
      const token = localStorage.getItem('authToken');
      if (!token) {
        alert('Debes iniciar sesión para realizar una compra');
        // Mostrar el modal de login
        const loginModal = document.getElementById('loginModal');
        if (loginModal) {
          loginModal.style.display = 'block';
        }
        return;
      }
      window.location.href = 'checkout.html';
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
        const removedItem = cart[index];
        cart.splice(index, 1);
        localStorage.setItem("cart_v1", JSON.stringify(cart));
        updateCartCount();
        renderCartItems();
        updateMiniCart();
        
        // Actualizar la UI de stock cuando se elimina un producto
        if (typeof window.updateProductStockUI === 'function' && removedItem) {
          window.updateProductStockUI(removedItem.productId, removedItem.size);
        }
      }
    });
  }

  // Vaciar carrito desde el mini carrito
  if (miniCartClear) {
    miniCartClear.addEventListener("click", () => {
      // Guardar información de los productos para actualizar el stock
      const removedItems = [...cart];
      
      cart = [];
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
      updateMiniCart();
      
      // Actualizar la UI de stock para todos los productos eliminados
      if (typeof window.updateProductStockUI === 'function') {
        removedItems.forEach(item => {
          window.updateProductStockUI(item.productId, item.size);
        });
      }
    });
  }

  // Eliminar items desde el modal del carrito
  if (cartItemsContainer) {
    cartItemsContainer.addEventListener("click", e => {
      if (e.target.classList.contains("remove-item")) {
        const index = e.target.dataset.index;
        const removedItem = cart[index];
        cart.splice(index, 1);
        localStorage.setItem("cart_v1", JSON.stringify(cart));
        updateCartCount();
        renderCartItems();
        updateMiniCart();
        
        // Actualizar la UI de stock cuando se elimina un producto
        if (typeof window.updateProductStockUI === 'function' && removedItem) {
          window.updateProductStockUI(removedItem.productId, removedItem.size);
        }
      }
    });
  }

  // ==================== FUNCIONES DE LOGIN ====================
  
  function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');
    
    console.log('Verificando estado de autenticación...', { token: !!token, userInfo: !!userInfo });
    
    if (token && userInfo) {
      try {
        currentUser = JSON.parse(userInfo);
        console.log('Usuario encontrado:', currentUser);
        updateLoginButton();
      } catch (e) {
        console.error('Error al parsear userInfo:', e);
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
      }
    } else {
      console.log('No hay sesión activa');
      updateLoginButton();
    }
  }

  function updateLoginButton() {
    console.log('Actualizando botón de login...', { loginLink: !!loginLink, currentUser });
    
    if (loginLink) {
      if (currentUser) {
        loginLink.textContent = `👤 ${currentUser.username}`;
        loginLink.href = "#";
        loginLink.onclick = showUserMenu;
        console.log('Botón actualizado para usuario:', currentUser.username);
      } else {
        loginLink.textContent = 'Iniciar Sesión';
        loginLink.href = "#login";
        loginLink.onclick = showLoginModal;
        console.log('Botón actualizado para login');
      }
    } else {
      console.error('loginLink no encontrado en el DOM');
    }
  }

  function showLoginModal() {
    if (loginModal) {
      loginModal.classList.add('show');
    }
  }

  function hideLoginModal() {
    if (loginModal) {
      loginModal.classList.remove('show');
    }
    // Limpiar formulario
    if (loginForm) loginForm.reset();
    hideMessages();
  }

  function hideMessages() {
    const errorDiv = document.getElementById('login-error');
    const successDiv = document.getElementById('login-success');
    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
  }

  function showMessage(message, type) {
    const errorDiv = document.getElementById('login-error');
    const successDiv = document.getElementById('login-success');
    
    hideMessages();
    
    if (type === 'error') {
      if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
      } else {
        alert(message);
      }
    } else {
      if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
      } else {
        alert(message);
      }
    }
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
      hideMessages();
    }, 5000);
  }

  // Manejar envío del formulario de login
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;
      const submitBtn = document.getElementById('login-btn');
      const loading = document.querySelector('.loading');
      
      if (!username || !password) {
        showMessage('Por favor completa todos los campos', 'error');
        return;
      }
      
      // Mostrar loading
      if (submitBtn) submitBtn.disabled = true;
      if (loading) loading.style.display = 'inline-block';
      
      try {
        // Configuración dinámica de la API
        const API_BASE = (() => {
            // Si estamos en Railway (producción), usar la URL actual
            if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                return window.location.origin;
            }
            // Si estamos en desarrollo local
            return "http://127.0.0.1:5000";
        })();
        
        const response = await fetch(`${API_BASE}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Guardar token en localStorage
          localStorage.setItem('authToken', data.session_token);
          localStorage.setItem('userInfo', JSON.stringify(data.user));
          
          currentUser = data.user;
          updateLoginButton();
          
          showMessage('¡Login exitoso!', 'success');
          
          // Cerrar modal después de 1.5 segundos
          setTimeout(() => {
            hideLoginModal();
            
            // Si es admin, mostrar opción de ir al panel
            if (data.user.role === 'admin') {
              console.log('Usuario admin detectado, preguntando si quiere ir al panel...');
              if (confirm('¿Quieres ir al panel de administración?')) {
                console.log('Redirigiendo al panel de administración...');
                window.location.href = '/admin/admin.html';
              } else {
                console.log('Usuario eligió no ir al panel');
              }
            }
          }, 1500);
          
        } else {
          showMessage(data.error || 'Error en el login', 'error');
        }
        
      } catch (error) {
        showMessage('Error de conexión. Verifica que el servidor esté corriendo.', 'error');
      } finally {
        // Ocultar loading
        if (submitBtn) submitBtn.disabled = false;
        if (loading) loading.style.display = 'none';
      }
    });
  }

  // Cerrar modal de login
  if (closeLogin) {
    closeLogin.addEventListener('click', hideLoginModal);
  }

  // Cerrar modal al hacer clic fuera
  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        hideLoginModal();
      }
    });
  }


  function showUserMenu() {
    const menu = `
      <div class="user-menu">
        <p style="color: #333; margin: 5px 0; font-weight: bold;">👤 ${currentUser.username}</p>
        <p style="color: #666; margin: 5px 0; font-size: 0.9rem;">Rol: ${currentUser.role === 'admin' ? 'Administrador' : 'Usuario'}</p>
        <a href="profile.html" style="background: #337ab7; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin: 5px 5px 5px 0; font-size: 0.9rem; text-decoration: none; display: inline-block;">Mi Perfil</a>
        ${currentUser.role !== 'admin' ? '<a href="orders.html" style="background: #f0ad4e; color: #333; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin: 5px 5px 5px 0; font-size: 0.9rem; text-decoration: none; display: inline-block;">Mis Pedidos</a>' : ''}
        ${currentUser.role === 'admin' ? '<button onclick="goToAdmin()" style="background: #5bc0de; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin: 5px 5px 5px 0; font-size: 0.9rem;">Panel Admin</button>' : ''}
        <button onclick="logout()" style="background: #d9534f; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin: 5px 5px 5px 0; font-size: 0.9rem;">Cerrar Sesión</button>
      </div>
    `;
    
    // Crear un popup simple
    const popup = document.createElement('div');
    popup.className = 'user-popup';
    popup.innerHTML = menu;
    popup.style.cssText = `
      position: absolute;
      top: 60px;
      right: 20px;
      background: white;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      min-width: 200px;
    `;
    
    document.body.appendChild(popup);
    
    // Cerrar al hacer clic fuera
    setTimeout(() => {
      document.addEventListener('click', function closePopup(e) {
        if (!popup.contains(e.target) && e.target !== loginLink) {
          popup.remove();
          document.removeEventListener('click', closePopup);
        }
      });
    }, 100);
  }

  function logout() {
    const token = localStorage.getItem('authToken');
    
    if (token) {
      // Configuración dinámica de la API
      const API_BASE = (() => {
          // Si estamos en Railway (producción), usar la URL actual
          if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
              return window.location.origin;
          }
          // Si estamos en desarrollo local
          return "http://127.0.0.1:5000";
      })();
      
      // Intentar cerrar sesión en el servidor
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
    currentUser = null;
    updateLoginButton();
    
    // Recargar página para limpiar estado
    location.reload();
  }

  function goToAdmin() {
    console.log('Función goToAdmin ejecutada');
    try {
      window.location.href = '/admin/admin.html';
    } catch (error) {
      console.error('Error al redirigir al admin:', error);
      // Fallback: intentar con URL relativa
      window.location.href = 'admin/admin.html';
    }
  }

  function showRegisterForm() {
    showMessage('Función de registro en desarrollo. Usa las credenciales de prueba.', 'error');
  }
  
  // Hacer funciones globales para que funcionen desde el HTML
  window.logout = logout;
  window.goToAdmin = goToAdmin;
  window.showRegisterForm = showRegisterForm;

  // Eventos para el botón de login
  if (loginLink) {
    loginLink.addEventListener("click", e => {
      e.preventDefault();
      if (currentUser) {
        showUserMenu();
      } else {
        showLoginModal();
      }
    });
  }

  // ==================== INICIALIZAR ====================
  if (cartModal) cartModal.style.display = "none";
  updateCartCount();
  renderCartItems();
  updateMiniCart();
  // updateLoginButton() ya se llama en checkAuthStatus()
});