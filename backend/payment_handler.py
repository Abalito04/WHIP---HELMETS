import os
import json
import mercadopago
from datetime import datetime
from flask import jsonify, request
from config import MP_ACCESS_TOKEN, SUCCESS_URL, FAILURE_URL, PENDING_URL, WEBHOOK_URL
from database import get_conn

class PaymentHandler:
    def __init__(self):
        # Configurar MercadoPago
        self.mp = mercadopago.SDK(MP_ACCESS_TOKEN)
        
    def create_payment_preference(self, items, customer_info):
        """
        Crear preferencia de pago en MercadoPago
        """
        try:
            # Preparar items para MercadoPago
            mp_items = []
            total_amount = 0
            
            for item in items:
                # Obtener información del producto desde la base de datos
                with get_conn() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name, price FROM productos WHERE id = %s",
                        (item['product_id'],)
                    )
                    product = cursor.fetchone()
                    
                    if not product:
                        return jsonify({"error": f"Producto {item['product_id']} no encontrado"}), 404
                    
                    product_name = product[0]
                    product_price = float(product[1])
                    quantity = int(item['quantity'])
                    item_total = product_price * quantity
                    total_amount += item_total
                    
                    mp_items.append({
                        "title": product_name,
                        "quantity": quantity,
                        "unit_price": product_price,
                        "currency_id": "ARS"
                    })
            
            # Crear preferencia de pago
            preference_data = {
                "items": mp_items,
                "payer": {
                    "name": customer_info.get('name', ''),
                    "email": customer_info.get('email', ''),
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
                "notification_url": WEBHOOK_URL,
                "external_reference": f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Crear preferencia en MercadoPago
            preference = self.mp.preference().create(preference_data)
            
            if preference["status"] == 201:
                # Guardar pedido en la base de datos
                order_id = self.save_order(items, customer_info, total_amount, preference["response"]["id"])
                
                return jsonify({
                    "success": True,
                    "preference_id": preference["response"]["id"],
                    "init_point": preference["response"]["init_point"],
                    "order_id": order_id,
                    "total_amount": total_amount
                }), 200
            else:
                return jsonify({"error": "Error al crear preferencia de pago"}), 500
                
        except Exception as e:
            print(f"Error al crear preferencia: {e}")
            return jsonify({"error": f"Error al crear preferencia: {str(e)}"}), 500
    
    def save_order(self, items, customer_info, total_amount, payment_id=None):
        """Guardar pedido en la base de datos"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Crear número de pedido único
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Insertar pedido
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, customer_name, customer_email, customer_phone, total_amount, payment_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        order_number,
                        customer_info.get('name', ''),
                        customer_info.get('email', ''),
                        customer_info.get('phone', ''),
                        total_amount,
                        payment_id,
                        'pending'
                    )
                )
                
                order_id = cursor.fetchone()[0]
                
                # Insertar items del pedido
                for item in items:
                    # Obtener precio del producto
                    cursor.execute(
                        "SELECT price FROM productos WHERE id = %s",
                        (item['product_id'],)
                    )
                    product = cursor.fetchone()
                    product_price = float(product[0]) if product else 0
                    
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (order_id, item['product_id'], item['quantity'], product_price)
                    )
                
                conn.commit()
                return order_id
                
        except Exception as e:
            print(f"Error al guardar pedido: {e}")
            raise e
    
    def update_payment_status(self, payment_id, status):
        """Actualizar estado del pago"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                if payment_id:
                    cursor.execute(
                        "UPDATE orders SET status = %s, updated_at = NOW() WHERE payment_id = %s",
                        (status, payment_id)
                    )
                    conn.commit()
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error al actualizar estado del pago: {e}")
            return False
    
    def get_order_by_payment_id(self, payment_id, user_email=None):
        """Obtener pedido por ID de pago"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Obtener pedido (con verificación de usuario si se proporciona)
                if user_email:
                    cursor.execute(
                        """
                        SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                               o.customer_phone, o.total_amount, o.status, o.payment_id,
                               o.created_at, o.updated_at
                        FROM orders o
                        WHERE o.payment_id = %s AND o.customer_email = %s
                        """,
                        (payment_id, user_email)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                               o.customer_phone, o.total_amount, o.status, o.payment_id,
                               o.created_at, o.updated_at
                        FROM orders o
                        WHERE o.payment_id = %s
                        """,
                        (payment_id,)
                    )
                
                order = cursor.fetchone()
                
                if not order:
                    return None
                
                # Obtener items del pedido
                cursor.execute(
                    """
                    SELECT oi.product_id, oi.quantity, oi.price, p.name, p.brand
                    FROM order_items oi
                    JOIN productos p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                    """,
                    (order[0],)
                )
                
                items = cursor.fetchall()
                
                return {
                    'id': order[0],
                    'order_number': order[1],
                    'customer_name': order[2],
                    'customer_email': order[3],
                    'customer_phone': order[4],
                    'total_amount': float(order[5]),
                    'status': order[6],
                    'payment_id': order[7],
                    'created_at': order[8].isoformat() if order[8] else None,
                    'updated_at': order[9].isoformat() if order[9] else None,
                    'items': [
                        {
                            'product_id': item[0],
                            'quantity': item[1],
                            'price': float(item[2]),
                            'name': item[3],
                            'brand': item[4]
                        }
                        for item in items
                    ]
                }
                
        except Exception as e:
            print(f"Error al obtener pedido: {e}")
            return None
    
    def get_user_orders(self, user_email):
        """Obtener pedidos del usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Obtener pedidos del usuario
                cursor.execute(
                    """
                    SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                           o.customer_phone, o.total_amount, o.status, o.payment_id,
                           o.created_at, o.updated_at
                    FROM orders o
                    WHERE o.customer_email = %s
                    ORDER BY o.created_at DESC
                    """,
                    (user_email,)
                )
                
                orders = cursor.fetchall()
                
                result = []
                for order in orders:
                    # Obtener items de cada pedido
                    cursor.execute(
                        """
                        SELECT oi.product_id, oi.quantity, oi.price, p.name, p.brand
                        FROM order_items oi
                        JOIN productos p ON oi.product_id = p.id
                        WHERE oi.order_id = %s
                        """,
                        (order[0],)
                    )
                    
                    items = cursor.fetchall()
                    
                    result.append({
                        'id': order[0],
                        'order_number': order[1],
                        'customer_name': order[2],
                        'customer_email': order[3],
                        'customer_phone': order[4],
                        'total_amount': float(order[5]),
                        'status': order[6],
                        'payment_id': order[7],
                        'created_at': order[8].isoformat() if order[8] else None,
                        'updated_at': order[9].isoformat() if order[9] else None,
                        'items': [
                            {
                                'product_id': item[0],
                                'quantity': item[1],
                                'price': float(item[2]),
                                'name': item[3],
                                'brand': item[4]
                            }
                            for item in items
                        ]
                    })
                
                return result
                
        except Exception as e:
            print(f"Error al obtener pedidos del usuario: {e}")
            return []

# Instancia global del handler de pagos
payment_handler = PaymentHandler()