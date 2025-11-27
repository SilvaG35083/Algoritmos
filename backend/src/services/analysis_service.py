from parsing.lexer import Lexer       
from parsing.parser import Parser, ParserConfig, ParserError
from parsing.lexer import LexerError
from analysis.recurrence_solver import RecurrenceSolver, RecurrenceRelation
from analysis.extractor import extract_generic_recurrence
from analysis.line_costs import LineCostAnalyzer
import json

def analyze_algorithm_flow(source_code: str) -> dict:
    """
    Ejecuta el pipeline completo y devuelve el JSON estructurado para el Frontend.
    """
    response_steps = {}
    
    print("\n" + "="*80)
    print("🚀 INICIANDO ANÁLISIS DE ALGORITMO")
    print("="*80)
    print(f"📝 Código fuente:\n{source_code}\n")

    # --- PASO 1: LEXER ---
    try:
        print("\n" + "-"*80)
        print("📍 PASO 1: ANÁLISIS LÉXICO (LEXER)")
        print("-"*80)
        
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        tokens_display = [str(token) for token in tokens]  # Convertir tokens a string para mostrar
        
        response_steps["lexer"] = {
            "title": "Análisis Léxico",
            "description": "Tokenización exitosa.",
            "data": tokens_display
        }
        
        print(f"✅ Tokens generados: {len(tokens)} tokens")
        print(f"📊 Datos enviados al frontend:")
        print(json.dumps(response_steps["lexer"], indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error en Lexer: {str(e)}")
        return _error_response(f"Error en Lexer: {str(e)}")

    # --- PASO 2: PARSER ---
    try:

        print("\n" + "🔸" * 30)
        print("📍 PASO 2: PARSER (Árbol de Sintaxis Abstracta)")
        print("🔸" * 30)

        parser = Parser(source_code)
        ast = parser.parse()        
        ast_display = str(ast) 

        response_steps["parser"] = {
            "title": "Análisis Sintáctico (AST)",
            "description": "Árbol generado correctamente.",
            "data": ast_display
        }

        # LOGS
        print(f"✅ AST Generado (Tipo): {type(ast)}")
        print(f"🌳 Estructura del Árbol: \n{ast_display}...")
        print("📦 JSON PARA FRONTEND (Parser):")
        print(json.dumps(response_steps["parser"], indent=2, ensure_ascii=False))

    except Exception as e:
        return _error_response(f"Error en Parser: {str(e)}")

    # --- PASO 2.5: COSTO POR LÍNEA ---
    try:
        print("\n" + "▫️" * 30)
        print("📍 PASO 2.5: COSTO POR LÍNEA (Heurístico por profundidad de bucles)")
        print("▫️" * 30)

        line_costs = LineCostAnalyzer().analyze(ast, source_code)
        response_steps["line_costs"] = {
            "title": "Costo por línea",
            "description": "Estimación heurística O(n^k) por línea según anidación de bucles.",
            "rows": line_costs,
        }

        # Imprimir tabla legible en consola
        print("\nLínea | Costo | Código")
        print("-" * 80)
        for row in line_costs:
            ln = str(row["line"]).rjust(5)
            cost = row["cost"].ljust(12)
            code = row["code"].strip()
            print(f"{ln} | {cost} | {code}")

        print("\n📦 JSON PARA FRONTEND (Line Costs):")
        print(json.dumps(response_steps["line_costs"], indent=2, ensure_ascii=False))

    except Exception as e:
        return _error_response(f"Error en Costo por Línea: {str(e)}")

    # --- PASO 3: EXTRACCIÓN ---
    try:

        print("\n" + "🔹" * 30)
        print("📍 PASO 3: EXTRACCIÓN (Modelado Matemático)")
        print("🔹" * 30)

        extraction = extract_generic_recurrence(ast)
        relation = extraction.relation

        response_steps["extraction"] = {
            "title": "Modelado Matemático",
            "description": "Ecuación extraída del análisis estático.",
            "equation": relation.recurrence,
            "explanation": relation.notes
        }

        # Añadimos también la estimación estructural producida internamente
        response_steps["structural_engine"] = {
            "title": "Estimación Estructural (ComplexityEngine)",
            "description": "Estimación basada en análisis estructural del AST.",
            "best_case": extraction.structural.best_case,
            "worst_case": extraction.structural.worst_case,
            "average_case": extraction.structural.average_case,
            "annotations": extraction.structural.annotations,
        }

        # LOGS
        print(f"✅ Relación de Recurrencia Detectada: {relation.recurrence}")
        print(f"🔍 Detalles del objeto Relation: {relation}")
        print("📦 JSON PARA FRONTEND (Extraction):")
        print(json.dumps(response_steps["extraction"], indent=2, ensure_ascii=False))
        print("📦 JSON PARA FRONTEND (Structural):")
        print(json.dumps(response_steps["structural_engine"], indent=2, ensure_ascii=False))

    except Exception as e:
        return _error_response(f"Error en Extracción: {str(e)}")

    # --- PASO 4: ANÁLISIS FINAL (Structural vs Solver) ---
    try:

        print("\n" + "🔸" * 30)
        print("📍 PASO 4: ANÁLISIS FINAL (Priorizar Structural sobre Solver)")
        print("🔸" * 30)

        # Para algoritmos iterativos con llamadas en bucles, Structural es más preciso
        # Solo usar Solver para algoritmos puramente recursivos
        structural = extraction.structural
        
        # Determinar si debemos usar Structural (iterativo complejo) o Solver (recursivo)
        use_structural = (
            "calls_in_loops" in structural.annotations or  # Hay llamadas en bucles
            "n^2" in structural.average_case or            # Complejidad cuadrática o mayor
            "n^3" in structural.average_case or
            "log n" in structural.average_case             # Complejidad logarítmica
        )
        
        if use_structural:
            print("✅ Usando análisis Structural (iterativo con llamadas anidadas)")
            main_result = structural.average_case
            best_case = structural.best_case
            worst_case = structural.worst_case
            justification = structural.annotations.get("calls_in_loops_max_called", 
                                                       structural.annotations.get("loop_summary", 
                                                       "Análisis estructural basado en profundidad de bucles."))
            math_steps = []
        else:
            print("✅ Usando Solver (recursión o caso simple)")
            solver = RecurrenceSolver.default()
            solution = solver.solve(relation)
            
            if solution:
                main_result = solution.theta
                best_case = solution.lower
                worst_case = solution.upper
                justification = solution.justification
                math_steps = solution.math_steps or []
            else:
                # Fallback a structural si solver falla
                print("⚠️ Solver falló, usando Structural como fallback")
                main_result = structural.average_case
                best_case = structural.best_case
                worst_case = structural.worst_case
                justification = "No se pudo resolver la recurrencia. Usando análisis estructural."
                math_steps = []
        
        # Obtener detalles legibles
        info = _get_complexity_details(main_result)
        
        response_steps["solution"] = {
            "title": "Análisis de Complejidad",
            "main_result": main_result,
            "complexity_class": info["name"],
            "complexity_desc": info["desc"],
            "cases": {
                "best": best_case,
                "worst": worst_case,
                "average": main_result
            },
            "justification": justification,
            "math_steps": math_steps
        }
        
        print(f"✅ Resultado Final: {main_result} ({info['name']})")
        print(json.dumps(response_steps["solution"], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error en Análisis Final: {e}")
        return _error_response(f"Error en análisis final: {str(e)}")

    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)

    return {
        "success": True,
        "steps": response_steps,
        "annotations": {}
    }

# --- Helper para dar contexto humano ---
def _get_complexity_details(theta_str: str) -> dict:
    """
    Traduce la notación matemática a nombres legibles para la UI.
    Ej: Theta(n) -> { name: "Lineal", desc: "..." }
    """
    s = str(theta_str).lower() 
    
    if "log" in s and "n" not in s.split("log")[0]: # O(log n)
        return {"name": "Logarítmica", "desc": "Muy eficiente. Divide el problema paso a paso."}
    elif "n log n" in s:
        return {"name": "Cuasilineal", "desc": "El estándar óptimo para ordenamientos (MergeSort)."}
    elif "n^2" in s:
        return {"name": "Cuadrática", "desc": "Eficiencia media/baja. Típico de bucles anidados."}
    elif "n^3" in s:
        return {"name": "Cúbica", "desc": "Ineficiente con muchos datos."}
    elif "2^n" in s:
        return {"name": "Exponencial", "desc": "Intratable para datos grandes (Recursión múltiple)."}
    elif "n" in s and "^" not in s: # O(n)
        return {"name": "Lineal", "desc": "El tiempo crece proporcionalmente a los datos."}
    elif "1" in s:
        return {"name": "Constante", "desc": "Instantáneo. No depende de la cantidad de datos."}
    
    return {"name": "Polinómica", "desc": "Complejidad calculada matemáticamente."}

def _error_response(msg):
    return {"success": False, "error": msg}