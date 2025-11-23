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

        relation = extract_generic_recurrence(ast)

        response_steps["extraction"] = {
            "title": "Modelado Matemático",
            "description": "Ecuación extraída del análisis estático.",
            "equation": relation.recurrence,
            "explanation": relation.notes
        }

        # LOGS
        print(f"✅ Relación de Recurrencia Detectada: {relation.recurrence}")
        print(f"🔍 Detalles del objeto Relation: {relation}")
        print("📦 JSON PARA FRONTEND (Extraction):")
        print(json.dumps(response_steps["extraction"], indent=2, ensure_ascii=False))

    except Exception as e:
        return _error_response(f"Error en Extracción: {str(e)}")

    # --- PASO 4: SOLVER ---
    try:

        print("\n" + "🔸" * 30)
        print("📍 PASO 4: SOLVER (Resolución de Complejidad)")
        print("🔸" * 30)

        solver = RecurrenceSolver.default()
        solution = solver.solve(relation)

        if solution:
            # 1. Obtenemos la info "humana" usando la función de arriba
            info = _get_complexity_details(solution.theta)

            # 2. Construimos el objeto EXACTO que espera el Frontend nuevo
            response_steps["solution"] = {
                "title": "Análisis de Complejidad",
                
                # --- Datos nuevos para el Header y Badge ---
                "main_result": solution.theta,       # Antes era 'complexity'
                "complexity_class": info["name"],    # Ej: "Lineal"
                "complexity_desc": info["desc"],     # Ej: "El tiempo crece..."

                # --- Datos agrupados para las Cards (Grid) ---
                "cases": {
                    "best": solution.lower,   # Omega
                    "worst": solution.upper,  # O
                    "average": solution.theta # Theta
                },

                # --- Datos para la sección inferior ---
                "justification": solution.justification,
                "math_steps": solution.math_steps or []
            }
            
            # Logs de depuración
            print(f"✅ Solución: {solution.theta} ({info['name']})")
            print(json.dumps(response_steps["solution"], indent=2, ensure_ascii=False))

        else:
            # Caso de fallo: enviamos estructura vacía pero compatible para no romper el UI
            response_steps["solution"] = {
                "title": "No resuelto",
                "main_result": "?",
                "complexity_class": "Desconocida",
                "complexity_desc": "No se pudo determinar un patrón estándar.",
                "cases": { "best": "?", "worst": "?", "average": "?" },
                "justification": "Intenta simplificar la estructura del algoritmo.",
                "math_steps": []
            }
            print("⚠️ No se pudo resolver la recurrencia.")

    except Exception as e:
        print(f"❌ Error en Solver: {e}")
        return _error_response(f"Error resolviendo ecuación: {str(e)}")

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