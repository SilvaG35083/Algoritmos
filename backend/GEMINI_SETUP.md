# Configuración de Google Gemini (gratis/rápido)

Gemini es el proveedor recomendado si no quieres usar créditos de OpenAI. También es obligatorio para la ruta `/api/simulate` (simulador basado en LLM).

## Ventajas
- Gratis con límites generosos.
- Modelos rápidos (`gemini-2.5-flash`) y opción de mayor calidad (`gemini-2.5-pro`).
- Integra bien con el chat y la simulación.

## Pasos
### 1) Obtener API key
1. Ve a https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google.
3. Crea una API key y cópiala.

### 2) Configurar `.env` en `backend/`
```env
GEMINI_API_KEY=tu-api-key
GEMINI_MODEL=gemini-2.5-flash   # opcional
LLM_PROVIDER=gemini             # si quieres que chat/analyze usen Gemini
```

### 3) Instalar dependencia
```bash
cd backend
pip install google-generativeai>=0.6
# o todas las extras LLM:
pip install -e ".[llm]"
```

### 4) Usar en frontend/backend
- Chat: selecciona **Gemini** en el dropdown del chat.
- Simulación: `/api/simulate` usa Gemini por defecto; sin `GEMINI_API_KEY` fallará.

## Troubleshooting
- **404 Modelo no encontrado**: ejecuta `python backend/test_gemini_models.py` y usa un modelo de la lista (`GEMINI_MODEL=...`).
- **No hay API key configurada**: verifica `echo $env:GEMINI_API_KEY` (PowerShell) o `echo $GEMINI_API_KEY` (Linux/macOS).
- **google-generativeai no está instalado**: `pip install google-generativeai`.

## Límites gratuitos (referencia)
- ~60 solicitudes/minuto y ~1,500/día, suficiente para desarrollo académico.

Listo: con la key en `.env` y la dependencia instalada, podrás usar Gemini en el chat y en el simulador.
