# Arquitectura del Analizador de Complejidades

## Visión general
El sistema sigue una arquitectura cliente-servidor claramente separada:

- **Backend (`backend/`)**: Implementado en Python con FastAPI. Aquí viven el lexer, parser, motor de complejidad, dataset de algoritmos y la API REST (`/api/analyze`, `/api/analyze-file`, `/api/samples`, `/api/health`). Este servicio entrega resultados estructurados para que cualquier cliente (React, scripts, LLMs) los consuma.
- **Frontend (`frontend/`)**: Aplicación React/Vite con tema oscuro/glassmorphism. Permite escribir o subir pseudocódigo, consultar ejemplos, disparar análisis y mostrar los resultados O/Ω/Θ junto con anotaciones.

Ya **no existe una interfaz Tkinter dentro del backend**; toda interacción visual pasa por el frontend.

## Flujo de procesamiento (backend)
1. **Ingesta**: se recibe pseudocódigo (texto o archivo) mediante el API.
2. **Parsing estructural**: el lexer reconoce comentarios (`►`), flechas de asignación (`🡨`), operadores Unicode y palabras reservadas; luego el parser genera el AST con bucles, condicionales, llamadas, arreglos, etc.
3. **Normalización y metadatos**: se crean tablas básicas de símbolos, se detectan patrones de control y se construyen estructuras para análisis posterior.
4. **Análisis de complejidad**: el motor polinómico calcula grados sobre `n` y potencias de `log n`, combinando secuencias, bucles, condicionales y heurísticas recursivas; produce las cotas O/Ω/Θ.
5. **Reporte**: `reporter.py` arma un resumen y anotaciones; FastAPI lo serializa y el frontend lo visualiza.

## Módulos principales (backend)
- `src/parsing/`: lexer, parser, AST y gramática.
- `src/analysis/`: motor de complejidad, modelos de costo, biblioteca de patrones y resolutores de recurrencias (base).
- `src/analyzer/`: pipeline, reporter, validators y dataset `samples.py`.
- `src/server/`: app FastAPI (`app.py`), modelos Pydantic (`models.py`) y dependencias compartidas (`deps.py`).
- `src/llm/`: scaffolding para integrar futuros asistentes basados en modelos de lenguaje.

## Frontend
- `frontend/src/App.jsx`: orquesta editor, carga de archivos, ejemplos y panel de resultados.
- `frontend/src/components/`: `Header`, `AlgorithmCard`, `ResultPanel`, etc.
- `frontend/src/styles.css`: tema oscuro, efectos glassmorphism y layout responsivo.
- Se comunica con el backend usando `fetch` hacia `VITE_API_BASE_URL`.

## Estado actual del motor
- Soporta `for`, `while`, `repeat-until`, condicionales e invocaciones `CALL`.
- Detección de patrones iterativos/recursivos para ajustar heurísticas.
- Resultados en notación `Ω(...)`, `O(...)`, `Θ(...)` con anotaciones descriptivas.

## Roadmap (resumen)
1. Extender el parser con declaraciones completas de procedimientos/objetos y validaciones semánticas.
2. Implementar resolutores de recurrencias reales (Master Theorem, sustitución, árboles de recurrencia).
3. Añadir métricas espaciales y tiempo estimado (microsegundos/tokens).
4. Integrar asistentes LLM en parsing, verificación y documentación.
5. Generar diagramas automáticos (CFG, árboles de recurrencia) y enriquecer el frontend con visualizaciones interactivas.
6. Ampliar el dataset de pruebas (≥10 algoritmos) y automatizar su ejecución.

## Buenas prácticas
- Mantener los módulos desacoplados y cubiertos por pruebas (`python -m pytest` dentro de `backend/`).
- Documentar en español solo cuando la lógica no sea evidente.
- Usar `python -m pip` dentro de la venv (`backend/.venv`) para evitar problemas con rutas.
- Cada cambio grande debe reflejarse en esta documentación y en el README principal.
