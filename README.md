# Analizador de Complejidades

Sistema integral para estimar complejidad (O, Θ, Ω) de algoritmos escritos en el pseudocódigo oficial del curso de **Análisis y Diseño de Algoritmos**. Incluye motor de análisis estático, heurísticas por estructura, rutas REST, chat LLM y un simulador apoyado por modelo generativo.

---

## Tabla de contenidos
1. [Objetivos clave](#objetivos-clave)
2. [Estructura del repositorio](#estructura-del-repositorio)
3. [Requisitos](#requisitos)
4. [Primeros pasos](#primeros-pasos)
5. [API REST](#api-rest)
6. [Frontend](#frontend)
7. [Pruebas](#pruebas)
8. [LLM y claves](#llm-y-claves)
9. [Documentación extra](#documentación-extra)

---

## Objetivos clave
- Interpretar pseudocódigo estructurado y generar AST, tablas de símbolos y patrones.
- Calcular cotas fuertes (mejor/peor/promedio) combinando `ComplexityEngine` + solver de recurrencias.
- Detectar patrones avanzados (divide y vencerás, recursión, grafos) y anotar heurísticas.
- Entregar dataset de referencia (≥10 algoritmos) y flujo de análisis paso a paso para el modal del frontend.
- **Chat LLM** (OpenAI/Gemini) para generar algoritmos y análisis línea por línea.
- **Simulación LLM**: ruta `/api/simulate` que devuelve árbol de ejecución JSON para inputs dados.

---

## Estructura del repositorio
```
.
├─ backend/                  # FastAPI + motor de análisis
│  ├─ docs/                  # Documentación técnica
│  ├─ src/                   # Analyzer, server, LLM, servicios
│  ├─ tests/                 # Pruebas unitarias/integración
│  ├─ GEMINI_SETUP.md        # Guía rápida Gemini
│  ├─ LLM_SETUP.md           # Configuración general de LLMs
│  └─ README_ENV.md          # Ejemplos de .env/variables
├─ frontend/                 # React + Vite
│  ├─ src/                   # App, componentes, estilos
│  └─ package.json
├─ README.md                 # Este documento
└─ informe_final.md          # Informe final (no tocar)
```

---

## Requisitos
- **Python 3.11+** para backend.
- **Node.js 18+** para frontend.
- Claves opcionales:
  - `OPENAI_API_KEY`/`OPENAI_MODEL` para chat/LLM (proveedor `openai`).
  - `GEMINI_API_KEY`/`GEMINI_MODEL` para chat y simulación (`provider: gemini` o `/api/simulate`).
  - Instala extras con `pip install -e .[llm]` en `backend/`.

---

## Primeros pasos
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e .[dev]
python -m pytest              # opcional: smoke test
uvicorn server.app:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```
Define `VITE_API_BASE_URL` si el backend corre en otro host/puerto.

---

## API REST
Base por defecto: `http://localhost:8000`

| Método | Ruta                | Descripción                                                                                 |
| ------ | ------------------- | ------------------------------------------------------------------------------------------- |
| GET    | `/api/health`       | Estado y versión (`0.3.0`).                                                                 |
| GET    | `/api/samples`      | Dataset de algoritmos (≥10) con pseudocódigo y complejidad esperada.                       |
| POST   | `/api/analyze`      | Análisis detallado (lexer → parser → costo por línea → extracción → solución).             |
| POST   | `/api/analyze-file` | Igual que `/api/analyze`, leyendo un archivo UTF-8 (multipart).                             |
| POST   | `/api/llm/analyze`  | Genera pseudocódigo + análisis vía LLM (stub si no hay API key).                            |
| POST   | `/api/llm/chat`     | Chat interactivo con historial; proveedor seleccionable (`openai`/`gemini`).               |
| POST   | `/api/simulate`     | Simulación con LLM: entrega árbol de ejecución JSON según inputs. Requiere `GEMINI_API_KEY`. |

### Forma de respuesta de `/api/analyze`
```json
{
  "success": true,
  "steps": {
    "lexer": {...},
    "parser": {...},
    "line_costs": {"rows": [{"line": 5, "cost": "n^2", "code": "..."}]},
    "extraction": {"equation": "T(n) = 2T(n/2) + n", "explanation": "..."},
    "solution": {"main_result": "Θ(n log n)", "cases": {...}},
    "dynamic_programming": {...}
  },
  "annotations": {}
}
```

Ejemplo rápido:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"source\": \"begin\\n for i <- 1 to n do\\n begin\\n  x <- x + 1\\n end\\nend\"}"
```

---

## Frontend
- Editor con limpieza rápida y carga de archivos (`.txt`, `.psc`, `.algo`, `.md`, `.json`, `.py`).
- Modal de análisis paso a paso consumiendo `steps` del backend (lexer, parser, costo por línea, extracción, solución, DP).
- Selector de algoritmo de ejemplo desde `/api/samples`.
- Chat LLM con historial y switch de proveedor (OpenAI/Gemini); rellena el editor si el asistente devuelve pseudocódigo.
- Modal de simulación que consume `/api/simulate` y muestra el árbol de ejecución devuelto por el LLM.
- Tema oscuro/glassmorphism listo para escritorio y móvil.

---

## Pruebas
En `backend/`:
```bash
python -m pytest
```
Cobertura principal:
- `tests/test_api.py`: health, analyze, analyze-file, llm/analyze (stub).
- `tests/test_pipeline.py`: flujo base del motor.
- `tests/test_*`: lexer, parser con procedimientos, palabras clave, bloques relajados y swap.

---

## LLM y claves
- Sin API key: `/api/llm/analyze` y `/api/llm/chat` devuelven respuestas simuladas; `/api/simulate` fallará.
- Con `OPENAI_API_KEY`: chat/analyze usan `gpt-4o-mini` (configurable vía `OPENAI_MODEL`).
- Con `GEMINI_API_KEY`: chat/analyze pueden usar `gemini-2.5-flash` (configurable) y la simulación se habilita.
- Variables recomendadas en `backend/.env`: `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL`.
Consulta `backend/LLM_SETUP.md`, `backend/GEMINI_SETUP.md` y `backend/README_ENV.md` para ejemplos.

---

## Documentación extra
- `backend/docs/architecture.md`: capas, flujo backend y rutas expuestas.
- `backend/docs/analysis.md`: extractor, heurísticas, line-costs y decisiones solver vs. estructural.

Listo: backend modular, API REST, frontend moderno con modal de análisis, chat LLM y simulador. ¿Vamos?
