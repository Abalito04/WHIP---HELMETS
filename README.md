# 🛒 WHIP Helmets — E-commerce Web App

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)](https://whip-helmets.up.railway.app/)
[![MercadoPago](https://img.shields.io/badge/Payments-MercadoPago-009EE3?style=flat-square&logo=mercadopago&logoColor=white)](https://www.mercadopago.com.ar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> **EN:** Full-featured e-commerce web application for a motorcycle helmet store. Built with Flask and deployed on Railway, it includes user authentication, shopping cart, checkout flow, and MercadoPago payment integration.
>
> **ES:** Aplicación web de e-commerce completa para una tienda de cascos de moto. Desarrollada con Flask y desplegada en Railway, incluye autenticación de usuarios, carrito de compras, flujo de checkout e integración con MercadoPago.

🌐 **Live Demo:** [whip-helmets.up.railway.app](https://whip-helmets.up.railway.app/)

---

## ✨ Features · Características

- 🔐 **User authentication** — register, login, email verification, forgot/reset password (Resend API)
- 🛒 **Shopping cart** — add, remove, update quantities, persistent across sessions
- 💳 **MercadoPago integration** — full checkout flow with payment gateway
- 📦 **Order management** — users can track their orders
- 👤 **User profile** — edit personal info and view order history
- 🛡️ **Admin panel** — manage products, orders and users
- 📧 **Transactional emails** — order confirmation and password reset via Resend
- 📱 **Responsive design** — mobile-friendly UI

---

## 🗂️ Project Structure

```
WHIP---HELMETS/
├── app.py                  # Flask entry point
├── backend/                # Routes, models, business logic
├── admin/                  # Admin panel
├── payment/                # MercadoPago integration
├── pages/                  # HTML page templates
├── assets/                 # Static files (CSS, JS, images)
├── templates/              # Jinja2 base templates
├── index.html              # Landing page
├── checkout.html           # Checkout page
├── orders.html             # Order tracking page
├── profile.html            # User profile page
├── register.html           # Registration page
├── verify-email.html       # Email verification page
├── forgot-password.html    # Forgot password page
├── reset-password.html     # Reset password page
├── requirements.txt
├── Procfile                # Railway deployment config
└── runtime.txt
```

---

## 🚀 Quick Start · Instalación local

### Prerequisites
- Python 3.8+
- pip
- A MercadoPago developer account (for payments)
- A Resend account (for emails)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Abalito04/WHIP---HELMETS.git
cd WHIP---HELMETS

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables (copy from railway.env as reference)
# MERCADOPAGO_ACCESS_TOKEN=your_token
# RESEND_API_KEY=your_key
# SECRET_KEY=your_secret

# 5. Run the app
python app.py
```

App will be available at `http://localhost:5000`

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python · Flask |
| Frontend | HTML5 · CSS3 · JavaScript |
| Database | SQLite (local) / PostgreSQL (production) |
| Payments | MercadoPago API |
| Emails | Resend API |
| Deployment | Railway |
| Server | Gunicorn |

---

## ☁️ Deployment

This app is deployed on **Railway**. See [`RAILWAY_DEPLOY.md`](RAILWAY_DEPLOY.md) for the full deployment guide.

For email setup, see [`RESEND_SETUP.md`](RESEND_SETUP.md).

---

## 👨‍💻 Author

**Matias Abalo** — [@Abalito04](https://github.com/Abalito04)

🌐 [Portfolio](https://matiabalo.up.railway.app/) · ✉️ [abalito95@gmail.com](mailto:abalito95@gmail.com)
