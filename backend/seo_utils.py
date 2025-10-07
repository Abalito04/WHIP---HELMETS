#!/usr/bin/env python3
"""
Utilidades para SEO y meta tags
"""

import os
from datetime import datetime

class SEOUtils:
    """Clase para generar meta tags y datos SEO"""
    
    def __init__(self):
        self.base_url = os.environ.get('BASE_URL', 'https://whip-helmets.up.railway.app')
        self.site_name = "WHIP HELMETS"
        self.default_description = "Cascos y accesorios de motociclismo de alta calidad. Encuentra el casco perfecto para tu seguridad y estilo."
        self.default_keywords = "cascos, motociclismo, seguridad, accesorios, moto, helmet, protección"
    
    def get_homepage_meta(self):
        """Meta tags para la página principal"""
        return {
            "title": f"{self.site_name} - Cascos y Accesorios de Motociclismo",
            "description": self.default_description,
            "keywords": self.default_keywords,
            "og_title": f"{self.site_name} - Cascos y Accesorios de Motociclismo",
            "og_description": self.default_description,
            "og_image": f"{self.base_url}/assets/images/logo.png",
            "og_url": self.base_url,
            "og_type": "website",
            "twitter_card": "summary_large_image",
            "twitter_title": f"{self.site_name} - Cascos y Accesorios de Motociclismo",
            "twitter_description": self.default_description,
            "twitter_image": f"{self.base_url}/assets/images/logo.png"
        }
    
    def get_product_meta(self, product):
        """Meta tags para páginas de productos"""
        if not product:
            return self.get_homepage_meta()
        
        product_name = product.get('name', 'Producto')
        product_price = product.get('price', 0)
        product_description = product.get('description', f"Casco {product_name} de alta calidad para motociclismo")
        
        # Limpiar descripción para SEO
        clean_description = product_description[:160] if len(product_description) > 160 else product_description
        
        return {
            "title": f"{product_name} - {self.site_name}",
            "description": f"{clean_description} Precio: ${product_price:.2f}. Envío gratis.",
            "keywords": f"{product_name}, casco, motociclismo, {self.default_keywords}",
            "og_title": f"{product_name} - {self.site_name}",
            "og_description": f"{clean_description} Precio: ${product_price:.2f}",
            "og_image": f"{self.base_url}/assets/images/products/{product.get('image', 'default.jpg')}",
            "og_url": f"{self.base_url}/producto/{product.get('id', '')}",
            "og_type": "product",
            "product_price_amount": product_price,
            "product_price_currency": "ARS",
            "product_availability": "in stock" if product.get('stock', 0) > 0 else "out of stock",
            "twitter_card": "summary_large_image",
            "twitter_title": f"{product_name} - {self.site_name}",
            "twitter_description": f"{clean_description} Precio: ${product_price:.2f}",
            "twitter_image": f"{self.base_url}/assets/images/products/{product.get('image', 'default.jpg')}"
        }
    
    def get_category_meta(self, category_name):
        """Meta tags para páginas de categorías"""
        return {
            "title": f"Cascos {category_name} - {self.site_name}",
            "description": f"Encuentra los mejores cascos {category_name} para motociclismo. Calidad, seguridad y estilo garantizados.",
            "keywords": f"cascos {category_name}, motociclismo, {self.default_keywords}",
            "og_title": f"Cascos {category_name} - {self.site_name}",
            "og_description": f"Encuentra los mejores cascos {category_name} para motociclismo",
            "og_image": f"{self.base_url}/assets/images/logo.png",
            "og_url": f"{self.base_url}/categoria/{category_name.lower()}",
            "og_type": "website",
            "twitter_card": "summary_large_image",
            "twitter_title": f"Cascos {category_name} - {self.site_name}",
            "twitter_description": f"Encuentra los mejores cascos {category_name} para motociclismo",
            "twitter_image": f"{self.base_url}/assets/images/logo.png"
        }
    
    def get_contact_meta(self):
        """Meta tags para página de contacto"""
        return {
            "title": f"Contacto - {self.site_name}",
            "description": "Contacta con WHIP HELMETS. WhatsApp: +54 295 454-4001. Atención personalizada para tus consultas.",
            "keywords": f"contacto, whatsapp, {self.default_keywords}",
            "og_title": f"Contacto - {self.site_name}",
            "og_description": "Contacta con WHIP HELMETS. WhatsApp: +54 295 454-4001",
            "og_image": f"{self.base_url}/assets/images/logo.png",
            "og_url": f"{self.base_url}/contacto",
            "og_type": "website",
            "twitter_card": "summary",
            "twitter_title": f"Contacto - {self.site_name}",
            "twitter_description": "Contacta con WHIP HELMETS. WhatsApp: +54 295 454-4001",
            "twitter_image": f"{self.base_url}/assets/images/logo.png"
        }
    
    def generate_structured_data(self, page_type="website", product=None):
        """Generar datos estructurados JSON-LD"""
        base_data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.site_name,
            "url": self.base_url,
            "logo": f"{self.base_url}/assets/images/logo.png",
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "+54-295-454-4001",
                "contactType": "customer service",
                "availableLanguage": "Spanish"
            },
            "sameAs": [
                "https://wa.me/542954544001"
            ]
        }
        
        if page_type == "product" and product:
            product_data = {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": product.get('name', ''),
                "description": product.get('description', ''),
                "image": f"{self.base_url}/assets/images/products/{product.get('image', 'default.jpg')}",
                "brand": {
                    "@type": "Brand",
                    "name": self.site_name
                },
                "offers": {
                    "@type": "Offer",
                    "price": product.get('price', 0),
                    "priceCurrency": "ARS",
                    "availability": "https://schema.org/InStock" if product.get('stock', 0) > 0 else "https://schema.org/OutOfStock",
                    "seller": {
                        "@type": "Organization",
                        "name": self.site_name
                    }
                }
            }
            return product_data
        
        return base_data
