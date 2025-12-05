# Documentación del análisis

El backend centraliza el análisis en el extractor (`src/analysis/extractor.py`) y en el servicio `analyze_algorithm_flow`, que arma el payload consumido por el modal del frontend.

## Flujo de análisis
1. **Lexer** (`parsing.lexer.Lexer`): tokeniza pseudocódigo con soporte Unicode y comentarios.
2. **Parser** (`parsing.parser.Parser`): construye AST con bucles, condicionales, llamadas y procedimientos.
3. **Costo por línea** (`analysis.line_costs.LineCostAnalyzer`):
   - O(n^k) según profundidad de bucles; trata bucles secuenciales sin sumar profundidad extra.
   - Reconoce whiles logarítmicos (búsqueda binaria, divisiones por 2) y añade factores `log n`.
4. **Extractor** (`analysis.extractor.extract_generic_recurrence`):
   - Devuelve `ExtractionResult` con:
     - `relation`: `RecurrenceRelation` (`identifier`, `recurrence`, `base_case`, `notes`).
     - `structural`: `ComplexityResult` (`best_case`, `worst_case`, `average_case`, `annotations`).
   - Heurísticas rastreadas: bucles anidados/seriales, llamadas recursivas, recursión en bucles, patrones divide y vencerás, recursión lineal vs. por división, profundidad logarítmica.
5. **Solución** (`services.analysis_service.analyze_algorithm_flow`):
   - Usa `ComplexityEngine` cuando hay llamadas en bucles, patrones iterativos o logarítmicos.
   - Usa `RecurrenceSolver` cuando la recurrencia es resoluble y fiable; si falla, vuelve a `structural`.
   - Traduce la notación a nombres legibles (lineal, cuadrática, exponencial, etc.) y construye `steps["solution"]`.
6. **Dynamic Programming (opcional)**:
   - Si la recurrencia es candidata (ej. `T(n) = T(n-1) + T(n-2)`), se añade `steps["dynamic_programming"]` con modelo recursivo, tablas y vector SOA; incluye caso especial de Fibonacci.

## API pública del extractor
```python
extract_generic_recurrence(ast_root, func_name="self") -> ExtractionResult
# relation: RecurrenceRelation
# structural: ComplexityResult
```

## Datos expuestos al frontend (`steps`)
- `lexer`: tokens en string.
- `parser`: AST serializado.
- `line_costs`: filas `{line, code, cost}`.
- `extraction`: `equation`, `explanation`.
- `solution`: `main_result`, `cases` (best/worst/average), `method_used`, `justification`, `math_steps`, `complexity_class/desc`, `expected` (si hay referencia).
- `dynamic_programming` (si aplica): modelo recursivo + tablas de óptimos/caminos + Vector SOA demo.

## Extender
- Nuevas heurísticas: agrégalas en `extractor` o `pattern_library` y añade anotaciones claras.
- Nuevas métricas: extiende `ComplexityResult` y propaga al `AnalysisModal`.
- Mantén las funciones puras y testeables (no acoples a FastAPI).

## Pruebas recomendadas
- Unit tests para `ComplexityEngine`, `LineCostAnalyzer` y extractores de patrones.
- Integración: `extract_generic_recurrence` sobre snippets representativos.
- Contract tests: validar la forma de `steps` en `/api/analyze` cuando se añadan claves nuevas.

Actualizado: 2025-12-05
