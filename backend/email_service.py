#!/usr/bin/env python3
"""
Servicio de notificaciones por email para WHIP HELMETS
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """Inicializar servicio de email"""
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'WHIP HELMETS')
        
        # Verificar configuración
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("⚠️  Email no configurado - notificaciones deshabilitadas")
            logger.warning("   Configura: SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL")
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Enviar email"""
        if not self.is_configured:
            logger.warning(f"Email no enviado a {to_email}: servicio no configurado")
            return False, "Servicio de email no configurado"
        
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar contenido
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado a {to_email}: {subject}")
            return True, "Email enviado correctamente"
            
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to_email}: {e}")
            return False, f"Error enviando email: {str(e)}"
    
    def send_order_confirmation(self, customer_email, customer_name, order_data):
        """Enviar confirmación de pedido"""
        subject = f"Confirmación de Pedido #{order_data.get('order_number', 'N/A')} - WHIP HELMETS"
        
        # Contenido HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmación de Pedido</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f0ad4e; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; }}
                .order-details {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #f0ad4e; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .product-item {{ border-bottom: 1px solid #eee; padding: 10px 0; }}
                .total {{ font-weight: bold; font-size: 18px; color: #f0ad4e; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏍️ WHIP HELMETS</h1>
                    <h2>¡Pedido Confirmado!</h2>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name}</strong>,</p>
                    
                    <p>¡Gracias por tu compra! Hemos recibido tu pedido y lo estamos procesando.</p>
                    
                    <div class="order-details">
                        <h3>📋 Detalles del Pedido</h3>
                        <p><strong>Número de Pedido:</strong> {order_data.get('order_number', 'N/A')}</p>
                        <p><strong>Fecha:</strong> {order_data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M'))}</p>
                        <p><strong>Estado:</strong> {order_data.get('status', 'Pendiente')}</p>
                        <p><strong>Método de Pago:</strong> {order_data.get('payment_method', 'N/A')}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>📦 Productos</h3>
                        {self._format_order_items(order_data.get('items', []))}
                        <div class="total">
                            <p>Total: ${order_data.get('total_amount', 0):,.2f}</p>
                        </div>
                    </div>
                    
                    <div class="order-details">
                        <h3>📞 Próximos Pasos</h3>
                        <p>• Te contactaremos pronto para coordinar la entrega</p>
                        <p>• Si tienes alguna consulta, contáctanos al +54 295 454-4001</p>
                        <p>• ¡Gracias por elegir WHIP HELMETS!</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>WHIP HELMETS - Cascos y Accesorios de Motociclismo</p>
                    <p>WhatsApp: +54 295 454-4001</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Contenido texto plano
        text_content = f"""
        WHIP HELMETS - Confirmación de Pedido
        
        Hola {customer_name},
        
        ¡Gracias por tu compra! Hemos recibido tu pedido.
        
        Detalles del Pedido:
        - Número: {order_data.get('order_number', 'N/A')}
        - Fecha: {order_data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M'))}
        - Estado: {order_data.get('status', 'Pendiente')}
        - Total: ${order_data.get('total_amount', 0):,.2f}
        
        Productos:
        {self._format_order_items_text(order_data.get('items', []))}
        
        Próximos pasos:
        - Te contactaremos para coordinar la entrega
        - Consultas: +54 295 454-4001
        
        ¡Gracias por elegir WHIP HELMETS!
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def send_welcome_email(self, customer_email, customer_name):
        """Enviar email de bienvenida"""
        subject = "¡Bienvenido a WHIP HELMETS! 🏍️"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bienvenido a WHIP HELMETS</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f0ad4e; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏍️ WHIP HELMETS</h1>
                    <h2>¡Bienvenido!</h2>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name}</strong>,</p>
                    
                    <p>¡Bienvenido a WHIP HELMETS! Estamos emocionados de tenerte como parte de nuestra comunidad de motociclistas.</p>
                    
                    <h3>🎯 ¿Qué puedes hacer en tu cuenta?</h3>
                    <ul>
                        <li>Ver el historial de tus pedidos</li>
                        <li>Actualizar tu información personal</li>
                        <li>Recibir notificaciones de nuevos productos</li>
                        <li>Acceso a ofertas exclusivas</li>
                    </ul>
                    
                    <h3>🛒 Explora nuestros productos</h3>
                    <p>Tenemos una amplia selección de cascos y accesorios de las mejores marcas para tu seguridad y estilo.</p>
                    
                    <p>Si tienes alguna pregunta, no dudes en contactarnos al +54 295 454-4001</p>
                    
                    <p>¡Que disfrutes tu experiencia de compra!</p>
                </div>
                
                <div class="footer">
                    <p>WHIP HELMETS - Cascos y Accesorios de Motociclismo</p>
                    <p>WhatsApp: +54 295 454-4001</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        WHIP HELMETS - ¡Bienvenido!
        
        Hola {customer_name},
        
        ¡Bienvenido a WHIP HELMETS! Estamos emocionados de tenerte como parte de nuestra comunidad.
        
        ¿Qué puedes hacer en tu cuenta?
        - Ver el historial de tus pedidos
        - Actualizar tu información personal
        - Recibir notificaciones de nuevos productos
        - Acceso a ofertas exclusivas
        
        Explora nuestros productos de cascos y accesorios de las mejores marcas.
        
        Consultas: +54 295 454-4001
        
        ¡Que disfrutes tu experiencia de compra!
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def _format_order_items(self, items):
        """Formatear items del pedido para HTML"""
        if not items:
            return "<p>No hay productos en el pedido</p>"
        
        html = ""
        for item in items:
            html += f"""
            <div class="product-item">
                <strong>{item.get('name', 'Producto')}</strong> - {item.get('brand', '')}<br>
                Cantidad: {item.get('quantity', 1)} | Precio: ${item.get('price', 0):,.2f}
            </div>
            """
        return html
    
    def _format_order_items_text(self, items):
        """Formatear items del pedido para texto plano"""
        if not items:
            return "No hay productos en el pedido"
        
        text = ""
        for item in items:
            text += f"- {item.get('name', 'Producto')} ({item.get('brand', '')}) - Cantidad: {item.get('quantity', 1)} - ${item.get('price', 0):,.2f}\n"
        return text

# Instancia global del servicio de email
email_service = EmailService()
