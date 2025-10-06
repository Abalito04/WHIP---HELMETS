# 🚀 Configuración de Resend para WHIP HELMETS

## **¿Por qué Resend?**

✅ **Gratuito** - 3,000 emails/mes gratis  
✅ **Simple** - Solo necesitas una API Key  
✅ **Confiable** - 99.9% de deliverability  
✅ **Moderno** - API REST simple  
✅ **Sin configuración SMTP** - No necesitas configurar servidores  

---

## **📋 PASO A PASO**

### **PASO 1: Crear cuenta en Resend**

1. **Ve a [resend.com](https://resend.com)**
2. **Haz clic en "Sign Up"**
3. **Regístrate con tu email**
4. **Verifica tu email**

### **PASO 2: Obtener API Key**

1. **Inicia sesión en tu dashboard**
2. **Ve a "API Keys" en el menú lateral**
3. **Haz clic en "Create API Key"**
4. **Dale un nombre: "WHIP HELMETS"**
5. **Copia la API Key** (empieza con `re_`)

### **PASO 3: Configurar en Railway**

1. **Ve a tu proyecto en Railway**
2. **Ve a "Variables"**
3. **Agrega estas variables:**

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@whiphelmets.com
FROM_NAME=WHIP HELMETS
```

### **PASO 4: Verificar configuración**

1. **Espera 2-3 minutos** para que Railway reinicie
2. **Ve a tu app** y prueba el endpoint:
   ```
   GET https://tu-app.up.railway.app/api/email/status
   ```
3. **Debería responder:**
   ```json
   {
     "available": true,
     "configured": true,
     "service": "Resend",
     "message": "Sistema de email configurado"
   }
   ```

---

## **🎯 CONFIGURACIÓN AVANZADA (Opcional)**

### **Dominio personalizado**

Si tienes un dominio propio:

1. **En Resend, ve a "Domains"**
2. **Agrega tu dominio** (ej: `whiphelmets.com`)
3. **Configura los registros DNS** que te indique
4. **Usa `noreply@tudominio.com` como FROM_EMAIL**

### **Templates personalizados**

Los templates están en `backend/resend_service.py`:
- `send_welcome_email()` - Email de bienvenida
- `send_order_confirmation()` - Confirmación de pedido

---

## **📊 LÍMITES Y PRECIOS**

### **Plan Gratuito:**
- ✅ **3,000 emails/mes**
- ✅ **100 emails/día**
- ✅ **1 dominio**
- ✅ **API completa**

### **Plan Pro ($20/mes):**
- ✅ **50,000 emails/mes**
- ✅ **Dominios ilimitados**
- ✅ **Soporte prioritario**
- ✅ **Analytics avanzados**

---

## **🔧 TROUBLESHOOTING**

### **Error: "Invalid API Key"**
- Verifica que la API Key sea correcta
- Asegúrate de que empiece con `re_`
- Verifica que no tenga espacios extra

### **Error: "Domain not verified"**
- Si usas dominio personalizado, verifica los registros DNS
- O usa `noreply@resend.dev` temporalmente

### **Emails no llegan**
- Revisa la carpeta de spam
- Verifica que el email de destino sea válido
- Revisa los logs de Railway

### **Error: "Rate limit exceeded"**
- Has alcanzado el límite diario (100 emails/día en plan gratuito)
- Espera hasta el día siguiente o actualiza el plan

---

## **📈 MONITOREO**

### **Dashboard de Resend:**
- Ve a [resend.com/dashboard](https://resend.com/dashboard)
- Revisa estadísticas de envío
- Ve logs de emails enviados

### **Logs de Railway:**
```bash
# En los logs verás:
✅ Email enviado a cliente@email.com: Confirmación de Pedido #TRF-20241201123456 (ID: abc123)
⚠️  Error enviando email: Invalid API Key
```

---

## **🚀 PRÓXIMOS PASOS**

Una vez configurado:

1. **Prueba el registro** de un nuevo usuario
2. **Prueba crear un pedido** por transferencia
3. **Verifica que lleguen los emails**
4. **Revisa el dashboard** de Resend

---

## **💡 CONSEJOS**

- **Usa un email profesional** como FROM_EMAIL
- **Personaliza el FROM_NAME** con tu marca
- **Revisa los templates** y personalízalos si quieres
- **Monitorea el uso** en el dashboard de Resend
- **Configura un dominio** cuando tengas uno propio

---

## **🆘 SOPORTE**

- **Documentación:** [resend.com/docs](https://resend.com/docs)
- **Discord:** [resend.com/discord](https://resend.com/discord)
- **Email:** support@resend.com

**¡Con Resend tendrás emails profesionales funcionando en minutos! 🎉**
