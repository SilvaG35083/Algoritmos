# Configuración de LLMs

Este proyecto soporta múltiples proveedores de LLM para análisis de algoritmos y corrección gramatical.

## Proveedores Soportados

- **OpenAI (ChatGPT)**: Recomendado para mejor calidad (requiere créditos)
- **Google Gemini**: Alternativa gratuita con buena calidad (recomendado si excedes cuota de OpenAI)

> 💡 **Tip**: Si recibes errores de cuota con OpenAI, cambia a Gemini. Ver `GEMINI_SETUP.md` para configuración rápida.

## Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto `backend/` o configura las variables de entorno en tu sistema:

#### Para OpenAI (ChatGPT)
```bash
export OPENAI_API_KEY="sk-tu-api-key-aqui"
export OPENAI_MODEL="gpt-4o-mini"  # Opcional, por defecto usa gpt-4o-mini
export LLM_PROVIDER="openai"  # Opcional, por defecto es "openai"
```

#### Para Google Gemini
```bash
export GEMINI_API_KEY="tu-api-key-aqui"
export LLM_PROVIDER="gemini"
```

### Obtener API Keys

#### OpenAI
1. Ve a https://platform.openai.com/api-keys
2. Crea una cuenta o inicia sesión
3. Genera una nueva API key
4. Copia la key y configúrala en tu entorno

#### Google Gemini
1. Ve a https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Genera una nueva API key
4. Copia la key y configúrala en tu entorno

## Instalación de Dependencias

Las dependencias LLM son opcionales. Para instalarlas:

```bash
cd backend
pip install -e ".[llm]"
```

O instalar manualmente:

```bash
# Para OpenAI
pip install openai>=1.0

# Para Gemini
pip install google-generativeai>=0.6
```

## Uso

Una vez configuradas las variables de entorno, el sistema usará automáticamente el LLM para:

1. **Corrección gramatical**: Cuando hay errores de parsing, el LLM intenta corregir el pseudocódigo
2. **Chat interactivo**: El componente de chat permite pedir algoritmos en lenguaje natural
3. **Análisis detallado**: El LLM genera análisis línea por línea con ecuaciones y árboles de recursión

## Sin API Key

Si no configuras una API key, el sistema funcionará pero:
- No habrá corrección gramatical automática
- El chat mostrará respuestas simuladas
- Los análisis detallados no estarán disponibles

## Troubleshooting

### Error: "openai no está instalado"
```bash
pip install openai
```

### Error: "google-generativeai no está instalado"
```bash
pip install google-generativeai
```

### Error: "No hay API key configurada"
Verifica que hayas configurado la variable de entorno correctamente:
```bash
echo $OPENAI_API_KEY  # o $GEMINI_API_KEY
```

### El LLM no responde
- Verifica que tu API key sea válida
- Revisa que tengas créditos disponibles en tu cuenta
- Verifica la conexión a internet
