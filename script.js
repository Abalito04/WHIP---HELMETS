document.addEventListener("DOMContentLoaded", () => {
  // ==================== VARIABLES ====================
  const cartCountEl = document.querySelector(".cart");
  const productCards = document.querySelectorAll(".product-card");
  const cartModal = document.getElementById("cart-modal");
  const cartItemsContainer = document.getElementById("cart-items");
  const cartClose = cartModal.querySelector(".close-cart");
  let cart = JSON.parse(localStorage.getItem("cart_v1")) || [];

  // ==================== FUNCIONES CARRITO ====================
  function updateCartCount() {
    cartCountEl.textContent = `🛒 Carrito (${cart.length})`;
  }

  function renderCartItems() {
    cartItemsContainer.innerHTML = "";
    if (cart.length === 0) {
      cartItemsContainer.innerHTML = "<p style='text-align:center;'>Tu carrito está vacío</p>";
      return;
    }

    // Tabla centrada
    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.textAlign = "center";
    table.style.borderCollapse = "collapse";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Producto</th><th>Talle</th><th>Precio</th><th>Eliminar</th></tr>";
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    let total = 0;
    cart.forEach((item, index) => {
      total += parseFloat(item.price.replace(/\$|,/g, '')) || 0;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.productName}</td>
        <td>${item.size}</td>
        <td>${item.price}</td>
        <td><button class="remove-item" data-index="${index}" style="background:#f0a946;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;">X</button></td>
      `;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    cartItemsContainer.appendChild(table);
  }

  function showMiniNotification(msg) {
    const notif = document.createElement("div");
    notif.textContent = msg;
    notif.style.position = "fixed";
    notif.style.bottom = "20px";
    notif.style.right = "20px";
    notif.style.background = "#f0ad4e";
    notif.style.color = "#000";
    notif.style.padding = "10px 20px";
    notif.style.borderRadius = "8px";
    notif.style.boxShadow = "0 4px 8px rgba(0,0,0,0.2)";
    notif.style.zIndex = "2000";
    notif.style.opacity = "0";
    notif.style.transition = "opacity 0.3s ease";

    document.body.appendChild(notif);
    setTimeout(() => notif.style.opacity = "1", 10);
    setTimeout(() => {
      notif.style.opacity = "0";
      setTimeout(() => notif.remove(), 300);
    }, 1500);
  }

  function addToCart(productName, price, size) {
    cart.push({ productName, price, size });
    localStorage.setItem("cart_v1", JSON.stringify(cart));
    updateCartCount();
    renderCartItems();
    showMiniNotification(`${productName} (${size}) agregado al carrito`);
  }

  // ==================== EVENTOS CARRITO ====================
  cartCountEl.addEventListener("click", () => {
    renderCartItems();
    cartModal.style.display = "flex";
  });

  cartClose.addEventListener("click", () => cartModal.style.display = "none");
  cartModal.addEventListener("click", e => { if (e.target === cartModal) cartModal.style.display = "none"; });

  cartItemsContainer.addEventListener("click", e => {
    if (e.target.classList.contains("remove-item")) {
      const index = e.target.dataset.index;
      cart.splice(index, 1);
      localStorage.setItem("cart_v1", JSON.stringify(cart));
      updateCartCount();
      renderCartItems();
    }
  });

  // Botón "Eliminar todo"
  const clearCartBtn = document.createElement("button");
  clearCartBtn.textContent = "Eliminar todo";
  clearCartBtn.style.marginTop = "10px";
  clearCartBtn.style.padding = "10px 20px";
  clearCartBtn.style.background = "#d9534f";
  clearCartBtn.style.border = "none";
  clearCartBtn.style.borderRadius = "5px";
  clearCartBtn.style.cursor = "pointer";
  clearCartBtn.addEventListener("click", () => {
    cart = [];
    localStorage.setItem("cart_v1", JSON.stringify(cart));
    updateCartCount();
    renderCartItems();
  });
  cartModal.querySelector(".cart-content").appendChild(clearCartBtn);

  // ==================== PRODUCTOS ====================
  productCards.forEach(card => {
    const button = card.querySelector("button");
    const productName = card.querySelector("h3").textContent;
    const price = card.querySelector(".price").textContent;
    const select = card.querySelector("select.size-selector");

    button.addEventListener("click", e => {
      e.stopPropagation();
      const size = select ? select.value : "";
      addToCart(productName, price, size);
    });
  });

  // ==================== FILTRO DE MARCAS ====================
  const brands = Array.from(new Set([...productCards].map(c => c.dataset.brand))).filter(b => b);
  if (brands.length > 0) {
    const filterContainer = document.createElement("div");
    filterContainer.id = "brand-filter";
    filterContainer.style.textAlign = "center";
    filterContainer.style.margin = "20px 0";
    filterContainer.style.display = "flex";
    filterContainer.style.justifyContent = "center";
    filterContainer.style.alignItems = "center";
    filterContainer.style.gap = "10px";

    const label = document.createElement("span");
    label.textContent = "Filtrar por marcas:";
    label.style.color = "#fff";

    const selectFilter = document.createElement("select");
    selectFilter.style.padding = "5px 10px";
    selectFilter.style.fontSize = "1em";

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

    const mainSection = document.querySelector("main");
    mainSection.insertBefore(filterContainer, document.querySelector("#destacados"));

    selectFilter.addEventListener("change", () => {
      const selectedBrand = selectFilter.value;
      productCards.forEach(card => {
        card.style.display = (selectedBrand === "Todas" || card.dataset.brand === selectedBrand) ? "block" : "none";
      });
    });
  }

  // ==================== MODAL DE PRODUCTO ====================
  const productModal = document.createElement("div");
  productModal.id = "product-modal";
  productModal.style.display = "none";
  productModal.style.position = "fixed";
  productModal.style.top = "0";
  productModal.style.left = "0";
  productModal.style.width = "100%";
  productModal.style.height = "100%";
  productModal.style.backgroundColor = "rgba(0,0,0,0.7)";
  productModal.style.justifyContent = "center";
  productModal.style.alignItems = "center";
  productModal.style.zIndex = "1000";
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

  function openProductModal(card) {
    currentImages = Array.from(card.querySelectorAll(".product-image")).map(img => img.src);
    currentIndex = 0;
    modalMainImage.src = currentImages[currentIndex];

    modalThumbnails.innerHTML = "";
    currentImages.forEach((src, idx) => {
      const thumb = document.createElement("img");
      thumb.src = src;
      thumb.style.width = "80px";
      thumb.style.cursor = "pointer";
      thumb.style.border = idx === currentIndex ? "2px solid #f0ad4e" : "1px solid #ccc";
      thumb.style.borderRadius = "5px";
      thumb.addEventListener("click", () => {
        currentIndex = idx;
        modalMainImage.src = currentImages[currentIndex];
        updateThumbnails();
      });
      modalThumbnails.appendChild(thumb);
    });

    productModal.style.display = "flex";
  }

  function updateThumbnails() {
    Array.from(modalThumbnails.children).forEach((thumb, idx) => {
      thumb.style.border = idx === currentIndex ? "2px solid #f0ad4e" : "1px solid #ccc";
    });
  }

  modalClose.addEventListener("click", () => productModal.style.display = "none");
  productModal.addEventListener("click", e => {
    if (e.target === productModal) productModal.style.display = "none";
  });

  productCards.forEach(card => {
  card.addEventListener("click", e => {
    // Abrir modal solo si se hace click en una imagen
    if (e.target.classList.contains("product-image")) {
      openProductModal(card);
    }
  });
});


  // ==================== INICIALIZAR ====================
  cartModal.style.display = "none"; 
  updateCartCount();
  renderCartItems();
});
