#!/usr/bin/env python3
"""
Servicio de notificaciones por email usando Resend para WHIP HELMETS
"""

import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResendEmailService:
    def __init__(self):
        """Inicializar servicio de email con Resend"""
        self.api_key = os.environ.get('RESEND_API_KEY', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'onboarding@resend.dev')
        self.from_name = os.environ.get('FROM_NAME', 'WHIP HELMETS')
        
        # Verificar configuración
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("⚠️  Resend no configurado - notificaciones deshabilitadas")
            logger.warning("   Configura: RESEND_API_KEY")
        else:
            try:
                import resend
                resend.api_key = self.api_key
                print("✅ Resend configurado correctamente")
            except ImportError:
                logger.error("❌ Módulo 'resend' no instalado")
                self.is_configured = False
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Enviar email usando Resend"""
        if not self.is_configured:
            logger.warning(f"Email no enviado a {to_email}: Resend no configurado")
            return False, "Servicio de email no configurado"
        
        try:
            import resend
            
            print(f"🔄 Intentando enviar email a {to_email}")
            print(f"   From: {self.from_name} <{self.from_email}>")
            print(f"   Subject: {subject}")
            print(f"   API Key configurada: {bool(self.api_key)}")
            
            # Preparar datos del email
            email_data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            # Agregar contenido de texto si está disponible
            if text_content:
                email_data["text"] = text_content
            
            print(f"📧 Datos del email preparados")
            print(f"   From: {email_data['from']}")
            print(f"   To: {email_data['to']}")
            print(f"   Subject: {email_data['subject']}")
            
            # Enviar email
            response = resend.Emails.send(email_data)
            
            print(f"📨 Respuesta de Resend: {response}")
            print(f"   Tipo de respuesta: {type(response)}")
            
            if response and (hasattr(response, 'id') or (isinstance(response, dict) and 'id' in response)):
                email_id = response.id if hasattr(response, 'id') else response['id']
                print(f"✅ Email enviado a {to_email}: {subject} (ID: {email_id})")
                return True, f"Email enviado correctamente (ID: {email_id})"
            else:
                print(f"❌ Error enviando email a {to_email}: Respuesta inválida")
                print(f"   Respuesta recibida: {response}")
                print(f"   Atributos de respuesta: {dir(response) if response else 'None'}")
                return False, f"Error en respuesta del servicio: {response}"
            
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to_email}: {e}")
            logger.error(f"   Tipo de error: {type(e).__name__}")
            logger.error(f"   Detalles completos: {str(e)}")
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
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .order-details {{ background: white; padding: 20px; margin: 15px 0; border-left: 4px solid #f0ad4e; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .product-item {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
                .product-item:last-child {{ border-bottom: none; }}
                .total {{ font-weight: bold; font-size: 20px; color: #f0ad4e; text-align: center; margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .order-number {{ font-size: 18px; margin: 10px 0; }}
                .status-badge {{ background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; }}
                .whatsapp-btn {{ background: #25d366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px 5px; }}
                .whatsapp-btn:hover {{ background: #128c7e; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏍️ WHIP HELMETS</div>
                    <h1>¡Pedido Confirmado!</h1>
                    <div class="order-number">Pedido #{order_data.get('order_number', 'N/A')}</div>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name}</strong>,</p>
                    
                    <p>¡Gracias por tu compra! Hemos recibido tu pedido y lo estamos procesando.</p>
                    
                    <div class="order-details">
                        <h3>📋 Detalles del Pedido</h3>
                        <p><strong>Número de Pedido:</strong> {order_data.get('order_number', 'N/A')}</p>
                        <p><strong>Fecha:</strong> {order_data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M'))}</p>
                        <p><strong>Estado:</strong> <span class="status-badge">{order_data.get('status', 'Pendiente')}</span></p>
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
                        <p>• Si tienes alguna consulta, contáctanos por WhatsApp</p>
                        <p>• ¡Gracias por elegir WHIP HELMETS!</p>
                        
                        <div style="text-align: center; margin-top: 20px;">
                            <a href="https://wa.me/542954544001" class="whatsapp-btn">
                                📱 Contactar por WhatsApp
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>WHIP HELMETS</strong> - Cascos y Accesorios de Motociclismo</p>
                    <p>WhatsApp: +54 295 454-4001</p>
                    <p>Email: {self.from_email}</p>
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
        - Consultas: +54 295 454-4001 (WhatsApp)
        
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
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .whatsapp-btn {{ background: #25d366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px 5px; }}
                .whatsapp-btn:hover {{ background: #128c7e; }}
                .shop-btn {{ background: #f0ad4e; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px 5px; }}
                .shop-btn:hover {{ background: #e67e22; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏍️ WHIP HELMETS</div>
                    <h1>¡Bienvenido!</h1>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name}</strong>,</p>
                    
                    <p>¡Bienvenido a WHIP HELMETS! Estamos emocionados de tenerte como parte de nuestra comunidad de motociclistas.</p>
                    
                    <div class="feature">
                        <h3>🎯 ¿Qué puedes hacer en tu cuenta?</h3>
                        <ul>
                            <li>Ver el historial de tus pedidos</li>
                            <li>Actualizar tu información personal</li>
                            <li>Recibir notificaciones de nuevos productos</li>
                            <li>Acceso a ofertas exclusivas</li>
                        </ul>
                    </div>
                    
                    <div class="feature">
                        <h3>🛒 Explora nuestros productos</h3>
                        <p>Tenemos una amplia selección de cascos y accesorios de las mejores marcas para tu seguridad y estilo.</p>
                        
                        <div style="text-align: center; margin-top: 20px;">
                            <a href="https://whip-helmets.up.railway.app" class="shop-btn">
                                🛍️ Ver Productos
                            </a>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <h3>📞 ¿Necesitas ayuda?</h3>
                        <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                        
                        <div style="text-align: center; margin-top: 20px;">
                            <a href="https://wa.me/542954544001" class="whatsapp-btn">
                                📱 Contactar por WhatsApp
                            </a>
                        </div>
                    </div>
                    
                    <p>¡Que disfrutes tu experiencia de compra!</p>
                </div>
                
                <div class="footer">
                    <p><strong>WHIP HELMETS</strong> - Cascos y Accesorios de Motociclismo</p>
                    <p>WhatsApp: +54 295 454-4001</p>
                    <p>Email: {self.from_email}</p>
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
        
        Consultas: +54 295 454-4001 (WhatsApp)
        
        ¡Que disfrutes tu experiencia de compra!
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def send_password_reset(self, customer_email, customer_name, reset_token):
        """Enviar email de recuperación de contraseña"""
        subject = "Recuperar Contraseña - WHIP HELMETS"
        
        # URL del reset (ajustar según tu dominio)
        reset_url = f"https://whip-helmets.up.railway.app/reset-password?token={reset_token}"
        
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
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .reset-btn {{ background: #f0ad4e; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                .reset-btn:hover {{ background: #e67e22; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .token {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">WHIP HELMETS</div>
                    <h1>Recuperar Contraseña</h1>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name}</strong>,</p>
                    
                    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en WHIP HELMETS.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" class="reset-btn">
                            Restablecer Contraseña
                        </a>
                    </div>
                    
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <div class="token">{reset_url}</div>
                    
                    <div class="warning">
                        <strong>Importante:</strong>
                        <ul>
                            <li>Este enlace expira en <strong>1 hora</strong></li>
                            <li>Solo puedes usarlo <strong>una vez</strong></li>
                            <li>Si no solicitaste este cambio, ignora este email</li>
                        </ul>
                    </div>
                    
                    <p>Si tienes problemas con el enlace, contáctanos por WhatsApp:</p>
                    
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="https://wa.me/542954544001" style="background: #25d366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; display: inline-block;">
                            Contactar por WhatsApp
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>WHIP HELMETS</strong> - Cascos y Accesorios de Motociclismo</p>
                    <p>WhatsApp: +54 295 454-4001</p>
                    <p>Email: {self.from_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        WHIP HELMETS - Recuperar Contraseña
        
        Hola {customer_name},
        
        Recibimos una solicitud para restablecer la contraseña de tu cuenta.
        
        Para restablecer tu contraseña, haz clic en este enlace:
        {reset_url}
        
        IMPORTANTE:
        - Este enlace expira en 1 hora
        - Solo puedes usarlo una vez
        - Si no solicitaste este cambio, ignora este email
        
        Si tienes problemas, contáctanos: +54 295 454-4001 (WhatsApp)
        
        WHIP HELMETS
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
    
    def send_email_verification(self, customer_email, customer_name, verification_token):
        """Enviar email de verificación de cuenta"""
        subject = "Verifica tu cuenta - WHIP HELMETS"
        
        verification_url = f"https://whip-helmets.up.railway.app/verify-email.html?token={verification_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verifica tu cuenta</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f0ad4e, #e67e22); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 10px 10px; }}
                .verify-btn {{ background: #f0ad4e; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .verify-btn:hover {{ background: #e67e22; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Verifica tu cuenta</h1>
                </div>
                
                <div class="content">
                    <h2>¡Hola {customer_name}!</h2>
                    <p>Gracias por registrarte en WHIP HELMETS. Para completar tu registro, necesitas verificar tu dirección de email.</p>
                    
                    <p>Haz clic en el botón de abajo para verificar tu cuenta:</p>
                    
                    <a href="{verification_url}" class="verify-btn">✅ Verificar mi cuenta</a>
                    
                    <p><strong>Este enlace expira en 24 horas.</strong></p>
                    
                    <p>Si no creaste una cuenta en WHIP HELMETS, puedes ignorar este email.</p>
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
        Verifica tu cuenta - WHIP HELMETS
        
        ¡Hola {customer_name}!
        
        Gracias por registrarte en WHIP HELMETS. Para completar tu registro, necesitas verificar tu dirección de email.
        
        Para verificar tu cuenta, visita este enlace:
        {verification_url}
        
        Este enlace expira en 24 horas.
        
        Si no creaste una cuenta en WHIP HELMETS, puedes ignorar este email.
        
        WHIP HELMETS
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)

# Instancia global del servicio de email
resend_email_service = ResendEmailService()
