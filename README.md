# Analizador de Complejidades

Sistema integral para estimar la complejidad computacional (O, Ω, Θ) de algoritmos descritos en el pseudocódigo oficial del curso de **Análisis y Diseño de Algoritmos**. El proyecto quedó separado en dos capas:

- `backend/`: motor de análisis (Python/FastAPI) + dataset de algoritmos + API REST.
- `frontend/`: interfaz web moderna construida con React/Vite, tema oscuro y soporte para subir archivos de pseudocódigo.

---

## Tabla de contenidos
1. [Objetivos clave](#objetivos-clave)
2. [Estructura del repositorio](#estructura-del-repositorio)
3. [Requisitos](#requisitos)
4. [Primeros pasos](#primeros-pasos)
5. [Uso del SDK Python](#uso-del-sdk-python)
6. [API REST (FastAPI)](#api-rest-fastapi)
7. [Frontend React](#frontend-react)
9. [Pruebas](#pruebas)
10. [Notas adicionales](#notas-adicionales)

---

## Objetivos clave
- Interpretar pseudocódigo estructurado y generar representaciones internas (AST, tablas de símbolos, patrones).
- Calcular costos elementales y obtener cotas fuertes para los casos mejor, peor y promedio.
- Reconocer patrones complejos (divide y vencerás, recursión, grafos) apoyándose en heurísticas y LLMs.
- Generar reportes explicativos, diagramas y un dataset mínimo de 10 algoritmos de prueba.

---

## Estructura del repositorio

```
.
├── backend/                  # Proyecto Python / FastAPI
│   ├── docs/                 # Documentación y arquitectura
│   ├── src/                  # Código fuente del analizador + API
│   ├── tests/                # Pruebas unitarias y de integración
│   ├── pyproject.toml        # Dependencias y build
│   └── pytest.ini
├── frontend/                 # Interfaz React + Vite (tema oscuro)
│   ├── src/                  # Componentes, estilos, hooks
│   ├── package.json
│   └── vite.config.js
├── README.md                 # Este documento
└── .gitignore
```

> La documentación técnica (arquitectura, roadmap, etc.) está en `backend/docs/architecture.md`.

---

## Requisitos
- **Python 3.11** (para el backend).
- **Node.js 18+** (para el frontend).
- Opcional: API key de tu LLM favorito (actualmente el código deja la integración preparada).

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
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

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
cd backend
.venv\Scripts\activate
uvicorn server.app:app --reload --port 8000
```

Endpoints principales:

| Método | Ruta              | Descripción                                   |
| ------ | ----------------- | --------------------------------------------- |
| GET    | `/api/health`     | Verificación rápida del servicio              |
| GET    | `/api/samples`    | Dataset con +10 algoritmos de referencia      |
| POST   | `/api/analyze`    | Analiza pseudocódigo enviado en JSON          |
| POST   | `/api/analyze-file` | Recibe un archivo (multipart) y lo analiza |

Ejemplo de request:

```bash
curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d "{\"source\": \"begin\\n    ...\\nend\"}"
```

Respuesta:
```json
{
  "summary": {
    "best_case": "Ω(n)",
    "worst_case": "O(n)",
    "average_case": "Θ(n)"
  },
  "annotations": {
    "pattern_summary": "...",
    "heuristica": "...",
    "nota": "..."
  }
}
```

---

## Frontend React

```bash
cd frontend
npm run dev          # http://localhost:5173
```

- Tema oscuro con fuentes Space Grotesk y efectos glassmorphism.
- Editor enriquecido con limpieza rápida, subida de archivos (TXT, PSC, ALGO, etc.) o entrada manual.
- Grid de algoritmos de ejemplo (divide y vencerás, recursión, grafos, etc.).
- Panel de resultados muestra las cotas O/Ω/Θ y las anotaciones generadas por el backend.
- Configura `VITE_API_BASE_URL` si el backend vive en otra URL.

---

## Pruebas

Desde `backend/`:
```bash
python -m pytest
```

Cobertura actual:
- `tests/test_pipeline.py`: flujo base del motor.
- `tests/test_api.py`: rutas `/api/health`, `/api/analyze`, `/api/analyze-file`.

Se recomienda añadir pruebas para los nuevos algoritmos que se vayan incorporando al dataset.

---

## Notas adicionales
- Mantén el código documentado en español (docstrings y comentarios breves cuando el contexto lo requiera).
- Los archivos `frontend/.env` o `backend/.env` no están versionados; úsalos para variables sensibles.
- Si agregas integraciones LLM, documenta los prompts en `backend/docs/`.

¡Listo! Ahora tienes un backend modular, un API REST documentada y un frontend listo para presentar el proyecto. 💡🚀
