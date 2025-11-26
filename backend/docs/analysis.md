# Documentación del Análisis (Extractor como fachada)

Este documento describe la organización actual del subsistema de análisis y explica cómo usar y extender el extractor (`src/analysis/extractor.py`), que ahora actúa como la única entrada para el análisis.

## Objetivo
Centralizar en `extractor` todas las funcionalidades de análisis para que el resto del sistema (pipeline, endpoints) use una sola API y no existan rutas divergentes.

## ¿Qué hace el extractor?
- Recorre el AST generado por el parser y calcula:
  - Una forma canónica de la recurrencia: `RecurrenceRelation` con `recurrence` y `notes`.
  - Una estimación estructural usando `ComplexityEngine` (Ω/O/Θ y anotaciones).
- Devuelve un `ExtractionResult` con las dos piezas: `relation` y `structural`.

## API pública
- `extract_generic_recurrence(ast_root, func_name="self") -> ExtractionResult`
  - `ExtractionResult.relation`: `RecurrenceRelation` (campos: `identifier`, `recurrence`, `base_case`, `notes`)
  - `ExtractionResult.structural`: `ComplexityResult` (campos: `best_case`, `worst_case`, `average_case`, `annotations`)

## Integración con pipeline y endpoints
- `analyzer.pipeline.AnalysisPipeline.run` usa ahora `extract_generic_recurrence(program)` y genera el `AnalysisReport` con `extraction.structural`.
- `services.analysis_service.analyze_algorithm_flow` llama a `extract_generic_recurrence(ast)` y:
  - expone `response_steps["extraction"]` con la ecuación y notas
  - expone `response_steps["structural_engine"]` con las cotas del `ComplexityEngine`
  - utiliza `relation` (recurrence) para el `RecurrenceSolver`.

## Beneficios del diseño
- Mantiene `ComplexityEngine` como una unidad reutilizable y testeable.
- Evita duplicación: mejoras en heurísticas quedan en `ComplexityEngine` y se usan automáticamente cuando el extractor invoca al engine.
- Permite que el frontend reciba tanto la ecuación matemática como la estimación estructural en una sola respuesta JSON.

## Ejemplo de uso (script rápido)
```python
from parsing.parser import Parser
from analysis.extractor import extract_generic_recurrence

src = "for i from 1 to n: sum += i"
parser = Parser(src)
ast = parser.parse()
extraction = extract_generic_recurrence(ast)
print('Recurrence:', extraction.relation.recurrence)
print('Structural:', extraction.structural.best_case, extraction.structural.worst_case, extraction.structural.average_case)
```

## Extender el extractor
- Si quieres añadir nuevas heurísticas (detectores de patrones, análisis de espacio, métricas por línea), hazlo dentro de `extractor` y añade datos al `ExtractionResult`.
- Mantén las funciones de bajo nivel (recorrer AST, detectar llamadas recursivas) como funciones puras y testables.

## Pruebas sugeridas
- Unit tests para `ComplexityEngine` (pequeños snippets y resultados esperados).
- Integration tests para `extract_generic_recurrence` que validen la relación y la estructura devuelta.

## Notas de mantenimiento
- Documenta cualquier heurística nueva dentro del extractor.
- Evita mover lógica pesada a `services/` o `server/` — deben limitarse a orquestación y exposición HTTP.

---

Actualizado: 2025-11-26
