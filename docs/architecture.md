# Arquitectura del Analizador de Complejidades

## Vision general
El sistema interpreta algoritmos escritos en el pseudocodigo oficial del curso, construye un arbol de sintaxis abstracta (AST) y estima la complejidad temporal en notaciones O, Omega y Theta. El motor actual aplica reglas polinomicas para los casos mejor, peor y promedio, mientras que futuras iteraciones integraran resolucion de recurrencias y asistencia con modelos de lenguaje (LLMs).

## Flujo de procesamiento
1. **Ingesta de entrada**
   - Pseudocodigo estructurado o descripciones en lenguaje natural (convertibles mediante un LLM).
2. **Parsing estructural**
   - El lexer reconoce comentarios (`►`), la flecha de asignacion (`🡨`), operadores relacionales (incluyendo variantes Unicode) y palabras reservadas.
   - El parser recursivo genera un AST tipado con bucles, condicionales, llamadas `CALL`, estructuras repeat-until, arreglos, objetos y expresiones booleanas/aritmeticas.
3. **Normalizacion y metadatos**
   - Se preparan tablas basicas de simbolos y se detectan patrones de alto nivel (presencia de bucles, indicios de recursion).
4. **Analisis de complejidad**
   - El motor polinomico inspecciona cada bloque, calcula el grado sobre `n` y potencia de `log n`, y combina resultados para estructuras de control (for, while, repeat, if).
   - Para bucles `while` se verifica si la variable de control progresa; si no puede determinarse, se asume una cota conservadora.
   - El reporte final presenta las cotas `Ω(f(n))`, `O(f(n))` y `Θ(f(n))`.
5. **Reporte y visualizacion**
   - `reporter.py` compone un resumen con anotaciones (patrones detectados, grado polinomico estimado, conteo total de sentencias).
   - `ui/gui.py` muestra una interfaz `tkinter` que permite pegar pseudocodigo y observar el resultado en espanol.

## Estructura de modulos
- `src/parsing/`
  - **lexer.py**: tokenizacion con soporte para caracteres especiales y manejo de mayusculas/minusculas.
  - **ast_nodes.py**: definiciones de nodos para sentencias, expresiones, clases y procedimientos.
  - **parser.py**: analizador descendente que valida la sintaxis del proyecto y construye el AST completo.
  - **grammar.py**: referencia declarativa de producciones (base para documentacion y futuros validadores).
- `src/analysis/`
  - **complexity_engine.py**: motor polinomico con evaluacion de secuencias, bucles e if/else; genera las cotas O/Ω/Θ.
  - **cost_model.py**: tabla de costos elementales parametrizables.
  - **pattern_library.py**: detectores estructurales extensibles (ciclos, recursion).
  - **recurrence_solver.py**: cimientos para resolutores de recurrencias (aun con implementaciones de ejemplo).
- `src/analyzer/`
  - **pipeline.py**: coordina parsing, validaciones, analisis y reporte.
  - **reporter.py**: sintetiza resultados y agrega estadisticas auxiliares (conteo recursivo de sentencias).
  - **validators.py**: reglas basicas (por ejemplo, advertencias para programas vacios).
- `src/ui/`
  - **gui.py**: interfaz grafica basada en `tkinter`.
  - **__init__.py**: expone `run_app`.
- `src/llm/`
  - **client.py**, **prompt_library.py**, **assistants.py**: capa preparada para integrar proveedores de LLM.

## Estado actual del motor
- Analiza `for`, `while`, `repeat-until`, condicionales e invocaciones `CALL`.
- Determina el grado polinomico combinando dependencia de entrada y profundidad de bucles.
- Diferencia el comportamiento en mejor, peor y promedio (por ejemplo, los `while` pueden tener mejor caso constante).
- Produce anotaciones con el resumen de patrones y el grado estimado para cada caso.

## Integracion con LLMs (planeada)
- Traduccion de descripciones en lenguaje natural a pseudocodigo.
- Verificacion cruzada de resultados y explicaciones narrativas.
- Generacion de conjuntos de pruebas y documentacion tecnica asistida.

## Roadmap actualizado
1. Ampliar el parser con declaraciones completas de procedimientos, objetos y tipado semantico.
2. Implementar resolucion real de recurrencias (Master Theorem, sustitucion, arboles de recursion).
3. Incorporar metrica espacial y consumo de recursos adicionales (microsegundos, tokens).
4. Integrar asistentes LLM en parsing, verificacion y documentacion.
5. Agregar diagramas automaticos (CFG, arboles de recursion) y enriquecer la GUI.
6. Construir un dataset de pruebas amplio (minimo 10 algoritmos) y automatizar su validacion.

## Consideraciones de calidad
- Mantener modulos desacoplados y cubiertos por pruebas unitarias (`pytest`).
- Limitar comentarios a los casos donde expliquen logica no evidente.
- Disenar APIs extensibles que permitan agregar patrones o reglas sin romper compatibilidad.
- Ejecutar las pruebas de manera regular y documentar nuevas decisiones de diseno en este archivo.
