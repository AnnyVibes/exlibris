# Arquitectura

- **Django 5.2 + SQLite**, plantillas Django y CSS propio (sin framework CSS). Fuentes Poppins y Raleway.
- **Servicios** (`biblioteca/services/`): `isbn` (validación), `catalogo` (Open Library → Google Books),
  `prestamos` (reglas de préstamo), `estadisticas` (cálculos del panel). Las vistas solo orquestan.
- **Escáner**: `html5-qrcode` 2.3.8 (CDN) lee EAN-13 con la cámara trasera y redirige a
  `/libros/nuevo/?isbn=…`, donde el servidor valida, busca en el catálogo y precarga el formulario.
- **Gráficos**: Chart.js 4.4.1 (CDN).
- **IA (fase 2)**: Django llamará a webhooks de **n8n** (instalado localmente, gratis) con un LLM
  gratuito (Gemini en capa gratuita u Ollama), igual que el Lab 14: Basic LLM Chain + Structured Output Parser
  para clasificar y resumir, y un AI Agent con herramientas HTTP que consultan una API JSON de la biblioteca.
- **Diseño**: inspirado en un dashboard pastel (Pinterest): barra lateral blanca, contenido central con hero
  en degradado rosa y tarjetas muy redondeadas, panel derecho con préstamos y última anotación. En el celular
  la barra lateral se convierte en una navegación inferior.
