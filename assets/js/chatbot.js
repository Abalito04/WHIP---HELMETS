// ================================================== */
//                  CHATBOT FUNCTIONALITY            */
// ================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // Variables del chatbot
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotBadge = document.getElementById('chatbot-badge');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    const initialTime = document.getElementById('initial-time');

    // Configurar hora inicial
    if (initialTime) {
        initialTime.textContent = getCurrentTime();
    }

    // Base de conocimiento del chatbot
    const chatbotResponses = {
        'nuevo-usado': {
            response: '¡Excelente pregunta! 🏍️ En WHIP-HELMETS manejamos tanto cascos nuevos como usados. Todos nuestros cascos, sin importar si son nuevos o usados, están completamente homologados y en perfecto estado para tu seguridad. Los cascos usados pasan por una revisión exhaustiva antes de ser puestos a la venta.',
            keywords: ['nuevo', 'usado', 'estado', 'condición', 'homologado']
        },
        'tallas': {
            response: '📏 Tenemos una amplia variedad de tallas disponibles para que encuentres el casco perfecto. Las tallas van desde XS hasta XXL, y cada casco tiene su tabla de tallas específica. Te recomendamos medir tu cabeza o probarte el casco antes de comprar para asegurar el ajuste perfecto. ¿Te gustaría que te ayude a encontrar tu talla ideal?',
            keywords: ['talla', 'tallas', 'medida', 'xs', 's', 'm', 'l', 'xl', 'xxl', 'tamaño']
        },
        'horarios': {
            response: '🕒 Nuestros horarios de atención son: Lunes a Viernes de 9:00 a 18:00 hs y Sábados de 9:00 a 13:00 hs. Los domingos permanecemos cerrados. También puedes contactarnos por WhatsApp al +54 295 454-4001 o por Instagram @whip.helmets en cualquier momento. ¡Estamos aquí para ayudarte!',
            keywords: ['horario', 'horarios', 'atención', 'abierto', 'cerrado', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        },
        'envios': {
            response: '🚚 ¡Sí! Realizamos envíos a domicilio en toda la ciudad y alrededores. Los envíos son gratuitos para compras superiores a $50.000. Para compras menores, el costo del envío es de $3.000. Los pedidos se despachan dentro de las 24-48 horas hábiles. ¿Te gustaría conocer más detalles sobre el envío?',
            keywords: ['envío', 'envíos', 'domicilio', 'delivery', 'gratis', 'costo', 'precio', 'despacho']
        },
        'marcas': {
            response: '🏆 Trabajamos con las mejores marcas del mercado: Fox, Bell, Alpinestars, Troy Lee Design, Fly Racing y muchas más. Cada marca tiene sus características especiales y niveles de protección. ¿Hay alguna marca específica que te interese o necesitas recomendaciones según tu tipo de uso?',
            keywords: ['marca', 'marcas', 'fox', 'bell', 'alpinestars', 'troy lee', 'fly racing', 'modelo', 'modelos']
        }
    };

    // Respuestas por defecto
    const defaultResponses = [
        '¡Hola! 👋 Soy el asistente de WHIP-HELMETS. Puedo ayudarte con información sobre nuestros productos, horarios, envíos y más. ¿En qué puedo ayudarte?',
        '¡Perfecto! 🤔 Si no encuentras la respuesta que buscas, puedes usar los botones de sugerencias o escribir tu pregunta directamente. También puedes contactarnos por WhatsApp al +54 295 454-4001.',
        '¡Excelente pregunta! 💡 Te recomiendo revisar los botones de sugerencias que aparecen abajo, o puedes contactarnos directamente por WhatsApp para una atención más personalizada.',
        '¡Gracias por tu consulta! 🏍️ Si necesitas más información específica, no dudes en contactarnos por WhatsApp al +54 295 454-4001 o por Instagram @whip.helmets.'
    ];

    // Función para obtener la hora actual
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    // Función para agregar mensaje al chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = getCurrentTime();
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        chatbotMessages.appendChild(messageDiv);
        
        // Scroll al final
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        
        // Ocultar badge después del primer mensaje
        if (isUser && chatbotBadge) {
            chatbotBadge.style.display = 'none';
        }
    }

    // Función para procesar el mensaje del usuario
    function processUserMessage(message) {
        const lowerMessage = message.toLowerCase();
        
        // Buscar coincidencias por palabras clave
        for (const [key, data] of Object.entries(chatbotResponses)) {
            for (const keyword of data.keywords) {
                if (lowerMessage.includes(keyword)) {
                    return data.response;
                }
            }
        }
        
        // Si no encuentra coincidencias, devolver respuesta aleatoria
        return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    }

    // Función para simular escritura del bot
    function typeMessage(message, callback) {
        let i = 0;
        const typingSpeed = 30; // Velocidad de escritura en ms
        
        function typeChar() {
            if (i < message.length) {
                const currentMessage = message.substring(0, i + 1);
                callback(currentMessage);
                i++;
                setTimeout(typeChar, typingSpeed);
            }
        }
        
        typeChar();
    }

    // Función para enviar mensaje
    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;
        
        // Agregar mensaje del usuario
        addMessage(message, true);
        
        // Limpiar input
        chatbotInput.value = '';
        
        // Deshabilitar botón de envío
        chatbotSend.disabled = true;
        
        // Simular delay del bot
        setTimeout(() => {
            const botResponse = processUserMessage(message);
            
            // Crear mensaje del bot
            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'chatbot-message bot-message';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = getCurrentTime();
            
            botMessageDiv.appendChild(contentDiv);
            botMessageDiv.appendChild(timeDiv);
            chatbotMessages.appendChild(botMessageDiv);
            
            // Efecto de escritura
            typeMessage(botResponse, (text) => {
                contentDiv.textContent = text;
                chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
            });
            
            // Habilitar botón de envío
            chatbotSend.disabled = false;
            
        }, 1000);
    }

    // Función para manejar sugerencias
    function handleSuggestion(questionType) {
        const suggestion = chatbotResponses[questionType];
        if (suggestion) {
            // Agregar mensaje del usuario (la pregunta)
            const questionText = document.querySelector(`[data-question="${questionType}"]`).textContent;
            addMessage(questionText, true);
            
            // Deshabilitar botón de envío
            chatbotSend.disabled = true;
            
            // Simular delay del bot
            setTimeout(() => {
                const botMessageDiv = document.createElement('div');
                botMessageDiv.className = 'chatbot-message bot-message';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'message-time';
                timeDiv.textContent = getCurrentTime();
                
                botMessageDiv.appendChild(contentDiv);
                botMessageDiv.appendChild(timeDiv);
                chatbotMessages.appendChild(botMessageDiv);
                
                // Efecto de escritura
                typeMessage(suggestion.response, (text) => {
                    contentDiv.textContent = text;
                    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
                });
                
                // Habilitar botón de envío
                chatbotSend.disabled = false;
                
            }, 1000);
        }
    }

    // Event Listeners
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', () => {
            chatbotWindow.classList.toggle('active');
            if (chatbotWindow.classList.contains('active')) {
                chatbotInput.focus();
            }
        });
    }

    if (chatbotClose) {
        chatbotClose.addEventListener('click', () => {
            chatbotWindow.classList.remove('active');
        });
    }

    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendMessage);
    }

    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Event listeners para botones de sugerencia
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const questionType = btn.getAttribute('data-question');
            handleSuggestion(questionType);
        });
    });

    // Cerrar chatbot al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (!chatbotContainer.contains(e.target) && chatbotWindow.classList.contains('active')) {
            chatbotWindow.classList.remove('active');
        }
    });

    // Mostrar badge después de 3 segundos
    setTimeout(() => {
        if (chatbotBadge) {
            chatbotBadge.style.display = 'flex';
        }
    }, 3000);
});
