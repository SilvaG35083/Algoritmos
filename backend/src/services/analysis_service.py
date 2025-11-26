from parsing.lexer import Lexer       
from parsing.parser import Parser, ParserConfig, ParserError
from parsing.lexer import LexerError
from analysis.recurrence_solver import RecurrenceSolver, RecurrenceRelation
from analysis.extractor import extract_generic_recurrence
from analysis.line_cost_analyzer import LineCostAnalyzer
from analysis.recursion_tree_builder import RecursionTreeBuilder
from analysis.dp_detector import DPDetector

def analyze_algorithm_flow(source_code: str) -> dict:
    """
    Ejecuta el pipeline completo y devuelve el JSON estructurado para el Frontend.
    """
    response_steps = {}

    # --- PASO 1: LEXER ---
    try:
        # Instancia tu Lexer real
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        tokens_display = [str(token) for token in tokens]  # Convertir tokens a string para mostrar
        
        response_steps["lexer"] = {
            "title": "Análisis Léxico",
            "description": "Tokenización exitosa.",
            "data": tokens_display

        }
    except Exception as e:
        return _error_response(f"Error en Lexer: {str(e)}")

    # --- PASO 2: PARSER ---
    algorithm_name = 'Sin nombre'  # Inicializar antes del try
    try:
        parser = Parser(source_code, ParserConfig())
        ast = parser.parse()        
        ast_display = str(ast) 

        # Agregar información del nombre del algoritmo si existe
        algorithm_name = getattr(ast, 'name', '') or 'Sin nombre'
        
        response_steps["parser"] = {
            "title": "Análisis Sintáctico (AST)",
            "description": f"Árbol generado correctamente. Algoritmo: {algorithm_name}",
            "data": ast_display,
            "algorithm_name": algorithm_name
        }
    except (ParserError, LexerError) as e:
        return _error_response(f"Error en Parser: {str(e)}")
    except Exception as e:
        return _error_response(f"Error inesperado en Parser: {str(e)}")

    # --- PASO 3: EXTRACCIÓN ---
    try:
        relation = extract_generic_recurrence(ast)

        response_steps["extraction"] = {
            "title": "Modelado Matemático",
            "description": "Ecuación extraída del análisis estático.",
            "equation": relation.recurrence,
            "explanation": relation.notes or "Ecuación de recurrencia detectada.",
            "base_case": relation.base_case,
            "source": "Análisis estático del AST"
        }
    except Exception as e:
        return _error_response(f"Error en Extracción: {str(e)}")

    # --- PASO 3.5: ANÁLISIS DE COSTO POR LÍNEA ---
    try:
        line_analyzer = LineCostAnalyzer()
        line_analysis = line_analyzer.analyze(ast, source_code)
        
        line_costs_data = []
        for cost in line_analysis.line_costs:
            line_costs_data.append({
                "line_number": cost.line_number,
                "line_code": cost.line_code,
                "scope": cost.scope,
                "cost": cost.cost,
                "explanation": cost.explanation,
                "source": cost.source
            })
        
        response_steps["line_costs"] = {
            "title": "Análisis de Costo por Línea",
            "description": f"Costo total estimado: {line_analysis.total_cost}",
            "line_costs": line_costs_data,
            "total_cost": line_analysis.total_cost,
            "complexity_breakdown": line_analysis.complexity_breakdown
        }
    except Exception as e:
        # No es crítico, continuar sin este análisis
        print(f"Advertencia: Error en análisis de costo por línea: {str(e)}")

    # --- PASO 3.6: ÁRBOL DE RECURSIÓN ---
    try:
        tree_builder = RecursionTreeBuilder()
        recursion_tree = tree_builder.build(ast)
        
        if recursion_tree:
            response_steps["recursion_tree"] = {
                "title": "Árbol de Recursión",
                "description": recursion_tree.description,
                "levels": recursion_tree.levels,
                "total_cost": recursion_tree.total_cost,
                "max_level": recursion_tree.max_level,
                "structure": recursion_tree.structure,
            }
        else:
            # Si no hay recursión, indicarlo explícitamente
            response_steps["recursion_tree"] = {
                "title": "Árbol de Recursión",
                "description": "Este algoritmo no es recursivo.",
                "levels": [],
                "total_cost": "N/A",
                "max_level": 0
            }
    except Exception as e:
        # Si hay error, intentar construir un árbol básico
        print(f"Advertencia: Error construyendo árbol de recursión: {str(e)}")
        response_steps["recursion_tree"] = {
            "title": "Árbol de Recursión",
            "description": f"No se pudo construir el árbol: {str(e)}",
            "levels": [],
            "total_cost": "N/A",
            "max_level": 0
        }

    # --- PASO 3.7: DETECCIÓN DE PROGRAMACIÓN DINÁMICA ---
    try:
        dp_detector = DPDetector()
        dp_analysis = dp_detector.detect(ast)
        
        if dp_analysis.is_dp:
            # Construir tablas de ejemplo
            problem_size = 10  # Tamaño de ejemplo
            tables_data = dp_detector.build_dp_tables(
                problem_size, dp_analysis.model_type, dp_analysis.approach
            )
            
            def _stringify_dp_keys(table_map):
                formatted = {}
                for key, value in table_map.items():
                    if isinstance(key, (list, tuple)):
                        key_str = "[" + ", ".join(str(k) for k in key) + "]"
                    else:
                        key_str = str(key)
                    formatted[key_str] = value
                return formatted

            response_steps["dynamic_programming"] = {
                "title": "Programación Dinámica",
                "description": dp_analysis.explanation,
                "is_dp": True,
                "approach": dp_analysis.approach,
                "model_type": dp_analysis.model_type,
                "space_complexity": dp_analysis.space_complexity,
                "tables": {
                    "optimos": {
                        "name": "Tabla de Óptimos",
                        "description": "Almacena los valores óptimos de los subproblemas",
                        "data": _stringify_dp_keys(tables_data["optimos"]["data"]),
                        "dimensions": tables_data["optimos"]["dimensions"],
                        "approach": tables_data["optimos"]["approach"],
                        "initialization": tables_data["optimos"]["initialization"],
                    },
                    "caminos": {
                        "name": "Tabla de Caminos",
                        "description": "Almacena las decisiones para reconstruir la solución",
                        "data": _stringify_dp_keys(tables_data["caminos"]["data"]),
                        "dimensions": tables_data["caminos"]["dimensions"],
                    },
                    "soa": {
                        "name": "Vector SOA",
                        "description": "Subestructura Óptima - se llena durante la reconstrucción",
                        "data": tables_data["soa"]["data"],
                    },
                },
                "reconstruction_steps": dp_analysis.reconstruction_steps,
                "explanation": f"""
                Este algoritmo utiliza Programación Dinámica con enfoque {dp_analysis.approach}.
                
                {'Enfoque Top-Down (Memoization):' if dp_analysis.approach == 'top_down' else 'Enfoque Bottom-Up:'}
                {'- Se inicializa la tabla de óptimos con valores que nunca se alcanzarán (ej: negativos)' if dp_analysis.approach == 'top_down' else '- Se llena la tabla de forma iterativa desde los casos base'}
                {'- Antes de calcular, se verifica si el problema ya está resuelto en la tabla' if dp_analysis.approach == 'top_down' else '- Se llena la tabla de forma sistemática (por filas o columnas)'}
                {'- Si está resuelto, se retorna el valor de la tabla' if dp_analysis.approach == 'top_down' else '- Se evitan recálculos al llenar la tabla de forma ordenada'}
                {'- Si no está resuelto, se calcula recursivamente y se guarda en la tabla' if dp_analysis.approach == 'top_down' else ''}
                
                Modelo: {dp_analysis.model_type}
                Complejidad Espacial: {dp_analysis.space_complexity}
                """
            }
        else:
            response_steps["dynamic_programming"] = {
                "title": "Programación Dinámica",
                "description": "No se detectó uso de Programación Dinámica en este algoritmo.",
                "is_dp": False,
            }
    except Exception as e:
        print(f"Advertencia: Error en detección de DP: {str(e)}")
        response_steps["dynamic_programming"] = {
            "title": "Programación Dinámica",
            "description": f"Error al analizar: {str(e)}",
            "is_dp": False,
        }

    # --- PASO 4: SOLVER ---
    try:
        solver = RecurrenceSolver.default()
        solution = solver.solve(relation)

        if solution:
            # Usar cases si está disponible, sino usar los bounds
            if hasattr(solution, 'cases') and solution.cases:
                cases = solution.cases
            else:
                cases = {
                    "best": solution.lower or "Ω(?)",
                    "average": solution.theta or "Θ(?)",
                    "worst": solution.upper or "O(?)",
                }
            response_steps["solution"] = {
                "title": "Solución Final",
                "description": solution.justification,
                "complexity": solution.theta,
                "upper_bound": solution.upper,
                "lower_bound": solution.lower,
                "details": solution.justification,
                "math_steps": solution.math_steps if hasattr(solution, 'math_steps') else [],
                "equation_source": "Teorema Maestro" if "master" in str(solution.justification).lower() or "quicksort" in str(solution.justification).lower() else "Sustitución",
                "cases": cases,
            }
        else:
             response_steps["solution"] = {
                "title": "No resuelto",
                "description": "No se encontró un patrón conocido.",
                "complexity": "Unknown",
                "details": "Intenta simplificar el algoritmo.",
                "math_steps": [],
                "equation_source": "No aplicable"
            }

    except Exception as e:
        return _error_response(f"Error resolviendo ecuación: {str(e)}")

    # Agregar resumen final con complejidades
    final_complexity = "Unknown"
    if "solution" in response_steps and response_steps["solution"].get("complexity"):
        final_complexity = response_steps["solution"]["complexity"]
    
    has_recursion = False
    if "recursion_tree" in response_steps:
        recursion_info = response_steps["recursion_tree"]
        has_recursion = recursion_info.get("max_level", 0) > 0 or len(recursion_info.get("levels", [])) > 0
    
    return {
        "success": True,
        "steps": response_steps,
        "algorithm_name": algorithm_name,
        "final_complexity": final_complexity,
        "has_recursion": has_recursion
    }

def _error_response(msg):
    return {"success": False, "error": msg}