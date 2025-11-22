# Analizador de Complejidades

Sistema integral para estimar la complejidad computacional (O, Ω, Θ) de algoritmos descritos en el pseudocódigo oficial del curso de **Análisis y Diseño de Algoritmos**. El proyecto está dividido en dos capas:

- `backend/`: motor de análisis en Python/FastAPI, dataset de algoritmos y API REST (incluye asistente LLM).
- `frontend/`: interfaz web moderna en React/Vite, tema oscuro, con editor, carga de archivos y consumo del API.

---

## Tabla de contenidos
1. [Objetivos clave](#objetivos-clave)
2. [Estructura del repositorio](#estructura-del-repositorio)
3. [Requisitos](#requisitos)
4. [Primeros pasos](#primeros-pasos)
5. [Uso del SDK Python](#uso-del-sdk-python)
6. [API REST (FastAPI)](#api-rest-fastapi)
7. [Frontend React](#frontend-react)
8. [Pruebas](#pruebas)
9. [Notas adicionales](#notas-adicionales)

---

## Objetivos clave
- Interpretar pseudocódigo estructurado y generar representaciones internas (AST, tablas de símbolos, patrones).
- Calcular costos elementales y obtener cotas fuertes para los casos mejor, peor y promedio.
- Reconocer patrones complejos (divide y vencerás, recursión, grafos) con apoyo de heurísticas y LLMs.
- Generar reportes explicativos y un dataset de prueba (≥10 algoritmos).
- **Corrección gramatical automática** usando LLMs cuando hay errores de parsing.
- **Chat interactivo** para generar algoritmos en lenguaje natural con análisis detallado línea por línea.
- **Análisis avanzado** con ecuaciones de recurrencia, árboles de recursión y métodos algorítmicos.

---

## Estructura del repositorio

```
.
├── backend/                  # Proyecto Python / FastAPI
│   ├── docs/                 # Documentación y arquitectura
│   ├── src/                  # Código fuente del analizador + API REST
│   ├── tests/                # Pruebas unitarias e integración
│   ├── pyproject.toml        # Dependencias y build
│   └── pytest.ini
├── frontend/                 # Interfaz React + Vite (tema oscuro)
│   ├── src/                  # Componentes, estilos, hooks
│   ├── package.json
│   └── vite.config.js
├── README.md
└── .gitignore
```

> Documentación técnica adicional en `backend/docs/architecture.md`.

---

## Requisitos
- **Python 3.11+** (backend).
- **Node.js 18+** (frontend).
- Opcional: `OPENAI_API_KEY` o `GEMINI_API_KEY` para habilitar el asistente LLM (por defecto usa respuesta simulada). 
  - Instala extras con `pip install -e .[llm]` si usarás modelos externos.
  - Ver `backend/LLM_SETUP.md` para configuración detallada.

---

## Primeros pasos

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e .[dev]
python -m pytest
uvicorn server.app:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

Configura `VITE_API_BASE_URL` si el backend corre en otra URL.

---

## Uso del SDK Python

```python
from analyzer import AnalysisPipeline

pipeline = AnalysisPipeline()
reporte = pipeline.run("""begin
    for i 🡨 1 to n do
    begin
        x 🡨 x + 1
    end
end""")

print(reporte.summary)       # {'best_case': 'Ω(n)', 'worst_case': 'O(n)', 'average_case': 'Θ(n)'}
print(reporte.annotations)   # notas/heurísticas detectadas
```

---

## API REST (FastAPI)

```bash
uvicorn server.app:app --reload --port 8000
```

| Método | Ruta                 | Descripción                                       |
| ------ | -------------------- | ------------------------------------------------- |
| GET    | `/api/health`        | Verificación del servicio                         |
| GET    | `/api/samples`       | Dataset con algoritmos de referencia              |
| POST   | `/api/analyze`       | Analiza pseudocódigo enviado en JSON (con corrección gramatical automática) |
| POST   | `/api/analyze-file`  | Analiza pseudocódigo subido como archivo (multipart) |
| POST   | `/api/llm/analyze`   | Asistente LLM: genera pseudocódigo y análisis     |
| POST   | `/api/llm/chat`      | Chat interactivo con historial de conversación   |

Ejemplo de chat:
```bash
curl -X POST http://localhost:8000/api/llm/chat \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Genera quicksort y analiza su complejidad",
       "provider": "openai"
     }'
```

Sin `OPENAI_API_KEY` o `GEMINI_API_KEY`, la API devuelve respuestas simuladas.

---

## Frontend React

- Tema oscuro con efectos glassmorphism.
- Editor con limpieza rápida, subida de archivos o entrada manual.
- Grid de algoritmos de ejemplo (divide y vencerás, recursión, grafos, etc.).
- Panel de resultados O/Ω/Θ y anotaciones.
- **Chat interactivo LLM**: 
  - Conversación en tiempo real con historial
  - Generación de algoritmos en lenguaje natural
  - Análisis detallado línea por línea con:
    - Ecuaciones de recurrencia
    - Árboles de recursión visuales
    - Métodos algorítmicos identificados
    - Costos por línea de código
    - Complejidad espacial y temporal
  - Soporte para múltiples proveedores (ChatGPT/Gemini)
  - Métricas de uso (tokens, latencia)

```bash
cd frontend
npm run dev
```

---

## Pruebas

Desde `backend/`:
```bash
python -m pytest
```

Cobertura actual:
- `tests/test_pipeline.py`: flujo base del motor.
- `tests/test_api.py`: rutas `/api/health`, `/api/analyze`, `/api/analyze-file`.

Agregar pruebas para `/api/llm/analyze` con mocks cuando se use la clave LLM.

---

## Funcionalidades LLM

### Corrección Gramatical Automática
Cuando el parser detecta errores en el pseudocódigo, el sistema usa un LLM para:
- Identificar errores gramaticales
- Sugerir correcciones automáticas
- Mantener la lógica del algoritmo intacta
- Proporcionar explicaciones de las correcciones

### Chat Interactivo
El componente de chat permite:
- Pedir algoritmos en lenguaje natural
- Mantener historial de conversación
- Obtener análisis detallados con:
  - Pseudocódigo estructurado
  - Ecuaciones de recurrencia
  - Árboles de recursión
  - Análisis línea por línea
  - Identificación de métodos algorítmicos

### Análisis Detallado
Cada análisis incluye:
- **Ecuaciones**: Relaciones de recurrencia con explicaciones
- **Árboles**: Representación visual de la recursión
- **Métodos**: Identificación de técnicas (divide y vencerás, DP, voraz, etc.)
- **Costos**: Análisis O/Ω/Θ por línea
- **Métricas**: Tokens usados y latencia

Ver `backend/LLM_SETUP.md` para configuración detallada.

## Notas adicionales
- Documentar en español solo cuando la lógica no sea evidente.
- Variables sensibles en `.env` (no versionado) tanto para backend como frontend.
- Los prompts y decisiones de diseño del LLM deben registrarse en `backend/docs/`.
- El sistema funciona sin API keys pero con funcionalidad limitada (respuestas simuladas).

¡Listo! Backend modular, API REST, frontend moderno con chat interactivo y asistente LLM avanzado para generar y analizar algoritmos. 🚀
