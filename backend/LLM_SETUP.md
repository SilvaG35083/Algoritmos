# Configuración de LLMs

El proyecto usa modelos de lenguaje en tres puntos:
- `/api/llm/analyze` y `/api/llm/chat`: generación de pseudocódigo y análisis línea a línea (OpenAI o Gemini).
- `/api/simulate`: simulación del algoritmo y retorno de un árbol de ejecución JSON (requiere Gemini).
- Corrección gramatical opcional en `AnalysisPipeline` cuando se inyecta un `GrammarCorrector`.

## Proveedores soportados
- **OpenAI (ChatGPT)**: mayor calidad, necesita créditos.
- **Google Gemini**: alternativa gratuita/rápida; también impulsa el simulador.

## Variables clave
- `LLM_PROVIDER`: `openai` o `gemini` (por defecto `openai` para chat/analyze).
- `OPENAI_API_KEY`, `OPENAI_MODEL` (ej. `gpt-4o-mini`).
- `GEMINI_API_KEY`, `GEMINI_MODEL` (ej. `gemini-2.5-flash`).

## Configuración rápida (.env en `backend/`)
### OpenAI
```env
OPENAI_API_KEY=sk-tu-api-key
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
```

### Gemini
```env
GEMINI_API_KEY=tu-api-key-gemini
GEMINI_MODEL=gemini-2.5-flash   # opcional
LLM_PROVIDER=gemini             # si quieres que chat/analyze usen Gemini
```

> La ruta `/api/simulate` siempre usa Gemini; sin `GEMINI_API_KEY` fallará.

## Dependencias
Instala extras LLM desde `backend/`:
```bash
pip install -e ".[llm]"
# o solo el proveedor que necesites:
pip install openai>=1.0
pip install google-generativeai>=0.6
```

## Comportamiento sin API key
- `/api/llm/analyze` y `/api/llm/chat` devuelven respuestas simuladas.
- `/api/simulate` no podrá ejecutarse.
- La corrección gramatical no se activa a menos que inyectes un corrector y haya clave disponible.

## Verificación rápida
- Gemini: `python test_gemini_models.py` para listar modelos disponibles con tu key.
- OpenAI: prueba `curl -X POST http://localhost:8000/api/llm/analyze -d '{"query":"suma un arreglo"}' -H "Content-Type: application/json"`.

## Cambiar de proveedor
- Frontend: selector en el chat (OpenAI/Gemini).
- Backend: ajusta `LLM_PROVIDER` en `.env` y reinicia el servidor.

Si hay errores de cuota, cambia a Gemini; si necesitas mayor calidad, usa OpenAI.
