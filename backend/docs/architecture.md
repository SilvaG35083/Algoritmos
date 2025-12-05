# Arquitectura del Analizador de Complejidades

## Visión general
- **Backend (`backend/`)**: FastAPI expone el motor de análisis, dataset, chat LLM y simulación. Rutas principales: `/api/health`, `/api/samples`, `/api/analyze`, `/api/analyze-file`, `/api/llm/analyze`, `/api/llm/chat`, `/api/simulate`.
- **Frontend (`frontend/`)**: React/Vite (tema oscuro/glass) consume el API, muestra el modal de análisis paso a paso, chat LLM y simulador.
- Toda la orquestación UI sucede en frontend; no hay GUI en backend.

## Flujo de procesamiento (backend)
1. **Ingesta** (`/api/analyze` o `/api/analyze-file`): recibe pseudocódigo plano o archivo UTF-8.
2. **Lexer**: reconoce comentarios, flechas de asignación, Unicode y keywords.
3. **Parser**: genera AST con bucles, condicionales, llamadas, arreglos y procedimientos.
4. **Costo por línea** (`analysis.line_costs.LineCostAnalyzer`): heurística O(n^k) por profundidad de bucles y factores logarítmicos (ej. búsqueda binaria).
5. **Extracción** (`analysis.extractor.extract_generic_recurrence`): devuelve `ExtractionResult` con:
   - `relation`: recurrencia canónica (`T(n) = ...`) + notas/base case.
   - `structural`: `ComplexityResult` del `ComplexityEngine` (Θ/O/Ω + anotaciones de patrones, llamadas en bucles, etc.).
6. **Decisión final** (`services.analysis_service.analyze_algorithm_flow`):
   - Usa resultado estructural cuando hay llamadas en bucles, log loops o patrones iterativos complejos.
   - Usa `RecurrenceSolver` si la recurrencia es resoluble y más fiable.
   - Genera `steps` para el modal: lexer, parser, line_costs, extraction, solution y, si aplica, `dynamic_programming` (plantilla DP o caso Fibonacci).
7. **Reporte**: serialización JSON con `success`, `steps` y `annotations` consumido por el frontend.

## Servicios adicionales
- **Simulación** (`src/services/simulation_service.py` + `server/simulation_routes.py`): invoca Gemini para producir un árbol de ejecución a partir del código y los inputs (`/api/simulate`).
- **Chat LLM** (`src/llm/chat_service.py` + `server/llm_service.py`): generación de pseudocódigo y análisis con historial; soporta OpenAI y Gemini. Sin API key devuelve stub.
- **Dataset** (`analyzer/samples.py`): ≥10 algoritmos de referencia con pseudocódigo y complejidad esperada.

## Módulos principales
- `src/parsing/`: lexer, parser, AST, gramática.
- `src/analysis/`: `complexity_engine`, `pattern_library`, `line_costs`, `recurrence_solver`, `extractor`.
- `src/analyzer/`: `pipeline`, `reporter`, `validators`, `samples`.
- `src/server/`: `app.py`, modelos Pydantic, dependencias, rutas LLM y simulación.
- `src/services/`: `analysis_service` (forma el payload del modal) y `simulation_service`.
- `src/llm/`: cliente Gemini, prompts, chat_service.

## Frontend
- `src/App.jsx`: orquesta editor, análisis, simulación y chat.
- `components/AnalysisModal`: muestra `steps` (lexer → parser → line_costs → extraction → solution → dynamic_programming).
- `components/SimulationModal`: consume `/api/simulate` y renderiza árbol JSON.
- `components/ChatPanel`: chat con selector de proveedor (OpenAI/Gemini) que puede rellenar el editor con el pseudocódigo generado.
- `styles.css`: tema oscuro, glassmorphism y layout responsivo.

## Estado actual del motor
- Soporta `for`, `while`, `repeat-until`, condicionales e invocaciones `CALL`.
- Heurísticas de detección: bucles secuenciales vs. anidados, llamadas recursivas en bucles, bucles logarítmicos, patrones divide y vencerás.
- Resultados en notación `Θ(...)`, `O(...)`, `Ω(...)` con anotaciones contextuales.

## Buenas prácticas
- Mantener pruebas al día (`python -m pytest` en `backend/`).
- Documentar cambios de heurísticas o endpoints en este archivo y en `README.md`.
- Usar `.env` para claves (`LLM_PROVIDER`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, modelos).
