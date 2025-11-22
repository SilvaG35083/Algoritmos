# 🆓 Configuración de Google Gemini (Gratis)

Si has excedido tu cuota de OpenAI o prefieres usar una alternativa gratuita, puedes configurar Google Gemini.

## Ventajas de Gemini

- ✅ **Gratis** con límites generosos
- ✅ Buena calidad para análisis de algoritmos
- ✅ Fácil de configurar

## Pasos para configurar

### 1. Obtener API Key de Gemini

1. Ve a https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Click en "Create API Key"
4. Copia la API key generada

### 2. Configurar la API Key

#### Opción A: Archivo `.env` (Recomendado)

Crea o edita el archivo `backend/.env`:

```env
GEMINI_API_KEY=tu-api-key-de-gemini-aqui
GEMINI_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini
```

> **Nota**: `GEMINI_MODEL` es opcional. Por defecto usa `gemini-2.5-flash` (más rápido y gratuito). 
> También puedes usar:
> - `gemini-2.5-pro` para mejor calidad
> - `gemini-flash-latest` para siempre usar el último flash disponible
> - `gemini-pro-latest` para siempre usar el último pro disponible
> 
> **Ejecuta `python backend/test_gemini_models.py` para ver todos los modelos disponibles con tu API key.**

#### Opción B: Variable de entorno

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="tu-api-key-aqui"
$env:LLM_PROVIDER="gemini"
```

**Windows CMD:**
```cmd
set GEMINI_API_KEY=tu-api-key-aqui
set LLM_PROVIDER=gemini
```

**Linux/macOS:**
```bash
export GEMINI_API_KEY="tu-api-key-aqui"
export LLM_PROVIDER="gemini"
```

### 3. Instalar dependencias

```bash
cd backend
pip install google-generativeai>=0.6
```

O instalar todas las dependencias LLM:

```bash
pip install -e ".[llm]"
```

### 4. Usar en el frontend

En el componente de chat, simplemente selecciona **"Gemini"** en el selector de proveedor (dropdown arriba del chat).

## Verificar que funciona

Después de configurar, reinicia el servidor backend y prueba el chat seleccionando "Gemini" como proveedor.

## Límites de Gemini

- **Gratis**: 60 solicitudes por minuto
- **Gratis**: 1,500 solicitudes por día
- Más que suficiente para uso académico y desarrollo

## Troubleshooting

### Error 404: "Modelo no encontrado"

Si recibes un error 404, ejecuta el script de diagnóstico:

```bash
cd backend
python test_gemini_models.py
```

Este script listará todos los modelos disponibles con tu API key.

Luego, actualiza tu `.env` con un modelo de la lista:

```env
GEMINI_MODEL=nombre-del-modelo-disponible
```

### Error: "google-generativeai no está instalado"
```bash
pip install google-generativeai
```

### Error: "No hay API key configurada"
Verifica que hayas configurado `GEMINI_API_KEY`:
```bash
# Windows PowerShell
echo $env:GEMINI_API_KEY

# Linux/macOS
echo $GEMINI_API_KEY
```

### El chat no funciona con Gemini
1. Ejecuta `python backend/test_gemini_models.py` para ver modelos disponibles
2. Verifica que la API key sea válida
3. Asegúrate de haber seleccionado "Gemini" en el frontend
4. Revisa los logs del servidor para ver errores específicos
5. Prueba configurando `GEMINI_MODEL` explícitamente en `.env`

## Alternar entre proveedores

Puedes cambiar entre OpenAI y Gemini en cualquier momento:
- En el frontend: usa el selector de proveedor
- En el backend: cambia `LLM_PROVIDER` en `.env` o variables de entorno

¡Listo! Ahora puedes usar Gemini como alternativa gratuita a OpenAI. 🚀
