import os
import json
import mercadopago
from datetime import datetime
from flask import jsonify, request
import sqlite3
from config import MP_ACCESS_TOKEN, SUCCESS_URL, FAILURE_URL, PENDING_URL, WEBHOOK_URL

class PaymentHandler:
    def __init__(self):
        # Configurar MercadoPago
        self.mp = mercadopago.SDK(MP_ACCESS_TOKEN)
        self.db_path = 'productos.db'
        
    def create_payment_preference(self, items, customer_info):
        """
        Crear preferencia de pago en MercadoPago
        """
        try:
            # Preparar items para MercadoPago
            mp_items = []
            for item in items:
                mp_items.append({
                    "title": item['name'],
                    "quantity": item['quantity'],
                    "unit_price": float(item['price']),
                    "currency_id": "ARS"
                })
            
            # Crear preferencia
            preference_data = {
                "items": mp_items,
                "payer": {
                    "name": customer_info.get('name', 'Cliente'),
                    "email": customer_info.get('email', 'cliente@example.com'),
                    "phone": {
                        "number": customer_info.get('phone', '')
                    }
                },
                "back_urls": {
                    "success": SUCCESS_URL,
                    "failure": FAILURE_URL,
                    "pending": PENDING_URL
                },
                "auto_return": "approved",
                "external_reference": f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "notification_url": WEBHOOK_URL
            }
            
            preference_response = self.mp.preference().create(preference_data)
            
            if preference_response["status"] == 201:
                return {
                    "success": True,
                    "preference_id": preference_response["response"]["id"],
                    "init_point": preference_response["response"]["init_point"],
                    "sandbox_init_point": preference_response["response"]["sandbox_init_point"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Error al crear preferencia de pago: {preference_response.get('response', {}).get('message', 'Error desconocido')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_webhook(self, data):
        """
        Procesar webhook de MercadoPago
        """
        try:
            if data["type"] == "payment":
                payment_id = data["data"]["id"]
                payment_info = self.mp.payment().get(payment_id)
                
                if payment_info["status"] == 200:
                    payment_data = payment_info["response"]
                    
                    # Actualizar estado del pedido
                    self.update_order_status(
                        payment_data["external_reference"],
                        payment_data["status"],
                        payment_data["id"]
                    )
                    
                    return {
                        "success": True,
                        "payment_id": payment_id,
                        "status": payment_data["status"]
                    }
            
            return {"success": False, "error": "Tipo de webhook no soportado"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_payment_status(self, payment_id):
        """
        Obtener estado de un pago
        """
        try:
            payment_info = self.mp.payment().get(payment_id)
            
            if payment_info["status"] == 200:
                return {
                    "success": True,
                    "payment_data": payment_info["response"]
                }
            else:
                return {
                    "success": False,
                    "error": "Error al obtener información del pago"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_order(self, items, customer_info, total_amount):
        """
        Crear pedido en la base de datos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla de pedidos si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE,
                    user_id INTEGER,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    total_amount REAL,
                    status TEXT DEFAULT 'pending',
                    payment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Crear tabla de items del pedido si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    product_id INTEGER,
                    product_name TEXT,
                    quantity INTEGER,
                    unit_price REAL,
                    size TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Generar número de pedido
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
            
            # Insertar pedido
            cursor.execute('''
                INSERT INTO orders (order_number, user_id, customer_name, customer_email, customer_phone, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                order_number,
                customer_info.get('user_id'),
                customer_info.get('name', ''),
                customer_info.get('email', ''),
                customer_info.get('phone', ''),
                total_amount
            ))
            
            order_id = cursor.lastrowid
            
            # Insertar items del pedido
            for item in items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, size)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    item.get('product_id'),
                    item['name'],
                    item['quantity'],
                    item['price'],
                    item.get('size', '')
                ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "order_id": order_id,
                "order_number": order_number
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_order_status(self, order_number, status, payment_id=None):
        """
        Actualizar estado de un pedido
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if payment_id:
                cursor.execute('''
                    UPDATE orders 
                    SET status = ?, payment_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_number = ?
                ''', (status, payment_id, order_number))
            else:
                cursor.execute('''
                    UPDATE orders 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_number = ?
                ''', (status, order_number))
            
            conn.commit()
            conn.close()
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_order(self, order_number, user_id=None):
        """
        Obtener información de un pedido
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener pedido (con verificación de usuario si se proporciona)
            if user_id:
                cursor.execute('''
                    SELECT * FROM orders WHERE order_number = ? AND user_id = ?
                ''', (order_number, user_id))
            else:
                cursor.execute('''
                    SELECT * FROM orders WHERE order_number = ?
                ''', (order_number,))
            
            order = cursor.fetchone()
            
            if not order:
                return {"success": False, "error": "Pedido no encontrado"}
            
            # Obtener items del pedido
            cursor.execute('''
                SELECT * FROM order_items WHERE order_id = ?
            ''', (order[0],))
            
            items = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "order": {
                    "id": order[0],
                    "order_number": order[1],
                    "user_id": order[2],
                    "customer_name": order[3],
                    "customer_email": order[4],
                    "customer_phone": order[5],
                    "total_amount": order[6],
                    "status": order[7],
                    "payment_id": order[8],
                    "created_at": order[9],
                    "updated_at": order[10]
                },
                "items": [
                    {
                        "id": item[0],
                        "product_id": item[2],
                        "product_name": item[3],
                        "quantity": item[4],
                        "unit_price": item[5],
                        "size": item[6]
                    }
                    for item in items
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_orders(self, user_id):
        """
        Obtener todos los pedidos de un usuario
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener pedidos del usuario
            cursor.execute('''
                SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            
            orders = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "orders": [
                    {
                        "id": order[0],
                        "order_number": order[1],
                        "user_id": order[2],
                        "customer_name": order[3],
                        "customer_email": order[4],
                        "customer_phone": order[5],
                        "total_amount": order[6],
                        "status": order[7],
                        "payment_id": order[8],
                        "created_at": order[9],
                        "updated_at": order[10]
                    }
                    for order in orders
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
