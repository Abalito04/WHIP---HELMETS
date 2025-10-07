#!/usr/bin/env python3
"""
Servicio de notificaciones por email usando SMTP (Gmail) para WHIP HELMETS
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMTPEmailService:
    def __init__(self):
        """Inicializar servicio de email con SMTP"""
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@whiphelmets.com')
        self.from_name = os.environ.get('FROM_NAME', 'WHIP HELMETS')
        
        # Verificar configuración
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("⚠️  SMTP no configurado - notificaciones deshabilitadas")
            logger.warning("   Configura: SMTP_USERNAME y SMTP_PASSWORD")
        else:
            print("✅ SMTP configurado correctamente")
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Enviar email usando SMTP"""
        if not self.is_configured:
            logger.warning(f"Email no enviado a {to_email}: SMTP no configurado")
            return False, "Servicio de email no configurado"
        
        try:
            print(f"🔄 Intentando enviar email SMTP a {to_email}")
            print(f"   From: {self.from_name} <{self.from_email}>")
            print(f"   Subject: {subject}")
            print(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Agregar contenido HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Agregar contenido de texto si está disponible
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            print(f"📧 Mensaje SMTP preparado")
            print(f"   From: {msg['From']}")
            print(f"   To: {msg['To']}")
            print(f"   Subject: {msg['Subject']}")
            
            # Conectar y enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            print(f"✅ Email SMTP enviado a {to_email}: {subject}")
            return True, f"Email enviado correctamente via SMTP"
            
        except Exception as e:
            logger.error(f"❌ Error enviando email SMTP a {to_email}: {e}")
            logger.error(f"   Tipo de error: {type(e).__name__}")
            logger.error(f"   Detalles completos: {str(e)}")
            return False, f"Error enviando email: {str(e)}"
    
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
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .whatsapp-btn {{ background: #25d366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px 5px; }}
                .whatsapp-btn:hover {{ background: #128c7e; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏍️ WHIP HELMETS</div>
                    <h1>¡Bienvenido, {customer_name}!</h1>
                </div>
                
                <div class="content">
                    <h2>¡Gracias por registrarte en WHIP HELMETS!</h2>
                    <p>Estamos emocionados de tenerte como parte de nuestra comunidad de motociclistas.</p>
                    
                    <div class="feature">
                        <h3>🎯 ¿Qué puedes hacer ahora?</h3>
                        <ul>
                            <li>Explorar nuestra colección de cascos nuevos y usados</li>
                            <li>Encontrar el casco perfecto para tu estilo</li>
                            <li>Realizar pedidos con envío a todo el país</li>
                            <li>Recibir ofertas exclusivas por email</li>
                        </ul>
                    </div>
                    
                    <div class="feature">
                        <h3>🛡️ Nuestros Cascos</h3>
                        <p>Todos nuestros cascos están <strong>100% homologados</strong> y en perfecto estado, garantizando tu seguridad en cada viaje.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>📱 ¿Necesitas ayuda?</h3>
                        <p>Nuestro equipo está aquí para ayudarte:</p>
                        <a href="https://wa.me/5492954123456" class="whatsapp-btn">💬 WhatsApp</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>WHIP HELMETS - Tu tienda de confianza para cascos</p>
                    <p>Este email fue enviado automáticamente. No responder.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        ¡Bienvenido a WHIP HELMETS, {customer_name}!
        
        Gracias por registrarte en nuestra tienda de cascos.
        
        ¿Qué puedes hacer ahora?
        - Explorar nuestra colección de cascos nuevos y usados
        - Encontrar el casco perfecto para tu estilo
        - Realizar pedidos con envío a todo el país
        - Recibir ofertas exclusivas por email
        
        Nuestros cascos están 100% homologados y en perfecto estado.
        
        ¿Necesitas ayuda? WhatsApp: +54 9 2954 123456
        
        ¡Gracias por elegir WHIP HELMETS!
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def send_password_reset(self, customer_email, customer_name, reset_token):
        """Enviar email de recuperación de contraseña"""
        subject = "Recuperar Contraseña - WHIP HELMETS"
        
        reset_url = f"https://whip-helmets.up.railway.app/reset-password.html?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recuperar Contraseña</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .reset-btn {{ background: #f0ad4e; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .reset-btn:hover {{ background: #e67e22; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Recuperar Contraseña</h1>
                </div>
                
                <div class="content">
                    <h2>Hola {customer_name},</h2>
                    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en WHIP HELMETS.</p>
                    
                    <p>Haz clic en el botón de abajo para crear una nueva contraseña:</p>
                    
                    <a href="{reset_url}" class="reset-btn">🔄 Restablecer Contraseña</a>
                    
                    <p><strong>Este enlace expira en 1 hora.</strong></p>
                    
                    <p>Si no solicitaste este cambio, puedes ignorar este email.</p>
                </div>
                
                <div class="footer">
                    <p>WHIP HELMETS - Tu tienda de confianza para cascos</p>
                    <p>Este email fue enviado automáticamente. No responder.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Recuperar Contraseña - WHIP HELMETS
        
        Hola {customer_name},
        
        Recibimos una solicitud para restablecer la contraseña de tu cuenta.
        
        Para crear una nueva contraseña, visita este enlace:
        {reset_url}
        
        Este enlace expira en 1 hora.
        
        Si no solicitaste este cambio, puedes ignorar este email.
        
        WHIP HELMETS
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def send_order_confirmation(self, customer_email, customer_name, order_data):
        """Enviar confirmación de pedido"""
        subject = f"Confirmación de Pedido #{order_data.get('order_number', 'N/A')} - WHIP HELMETS"
        
        # Crear lista de productos
        items_html = ""
        items_text = ""
        for item in order_data.get('items', []):
            items_html += f"""
            <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #f0ad4e;">
                <strong>{item.get('name', 'Producto')}</strong><br>
                Talle: {item.get('size', 'N/A')} | Cantidad: {item.get('quantity', 1)}<br>
                Precio: ${item.get('price', 0):.2f}
            </div>
            """
            items_text += f"- {item.get('name', 'Producto')} (Talle: {item.get('size', 'N/A')}) - ${item.get('price', 0):.2f}\n"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmación de Pedido</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .order-info {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .total {{ font-size: 18px; font-weight: bold; color: #f0ad4e; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Pedido Confirmado</h1>
                    <p>Pedido #{order_data.get('order_number', 'N/A')}</p>
                </div>
                
                <div class="content">
                    <h2>¡Gracias por tu compra, {customer_name}!</h2>
                    <p>Tu pedido ha sido confirmado y está siendo procesado.</p>
                    
                    <div class="order-info">
                        <h3>📋 Detalles del Pedido</h3>
                        <p><strong>Número de Pedido:</strong> #{order_data.get('order_number', 'N/A')}</p>
                        <p><strong>Fecha:</strong> {order_data.get('created_at', 'N/A')}</p>
                        <p><strong>Total:</strong> <span class="total">${order_data.get('total_amount', 0):.2f}</span></p>
                    </div>
                    
                    <div class="order-info">
                        <h3>🛍️ Productos</h3>
                        {items_html}
                    </div>
                    
                    <div class="order-info">
                        <h3>📦 Próximos Pasos</h3>
                        <p>Te contactaremos pronto para coordinar el envío de tu pedido.</p>
                        <p>¿Tienes preguntas? WhatsApp: +54 9 2954 123456</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>WHIP HELMETS - Tu tienda de confianza para cascos</p>
                    <p>Este email fue enviado automáticamente. No responder.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Confirmación de Pedido #{order_data.get('order_number', 'N/A')} - WHIP HELMETS
        
        ¡Gracias por tu compra, {customer_name}!
        
        Tu pedido ha sido confirmado y está siendo procesado.
        
        Detalles del Pedido:
        - Número: #{order_data.get('order_number', 'N/A')}
        - Fecha: {order_data.get('created_at', 'N/A')}
        - Total: ${order_data.get('total_amount', 0):.2f}
        
        Productos:
        {items_text}
        
        Próximos Pasos:
        Te contactaremos pronto para coordinar el envío de tu pedido.
        ¿Tienes preguntas? WhatsApp: +54 9 2954 123456
        
        WHIP HELMETS
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)

# Crear instancia del servicio
smtp_email_service = SMTPEmailService()
