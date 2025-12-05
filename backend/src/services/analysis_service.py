from parsing.lexer import Lexer       
from parsing.parser import Parser, ParserConfig, ParserError
from parsing.lexer import LexerError
from analysis.recurrence_solver import RecurrenceSolver, RecurrenceRelation
from analysis.extractor import extract_generic_recurrence
from analysis.line_costs import LineCostAnalyzer
from analysis.recurrence_solver import RecurrenceSolver
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

    # --- PASO 3: EXTRACCIÓN Y ANÁLISIS MATEMÁTICO ---
    try:

        print("\n" + "🔹" * 30)
        print("📍 PASO 3: EXTRACCIÓN (Modelado Matemático Formal)")
        print("🔹" * 30)

        extraction = extract_generic_recurrence(ast)
        relation = extraction.relation

        # 1. RESOLVER LA ECUACIÓN CON EL NUEVO SOLVER
        solver = RecurrenceSolver()
        math_solution = solver.solve(relation.recurrence)

        # 2. PREPARAR DATOS PARA EL SEMÁFORO (Best/Avg/Worst)
        # El solver nos da la notación formal (Theta) y la simple (Big-O).
        # Construimos el objeto que espera el componente 'ComplexityAnalysisPanel'
        complexity_simple = math_solution.get("complexity", "?")
        formal_notation = math_solution.get("formal_notation", "?")
        
        # Lógica simple para inferir mejor caso (Ω) desde el promedio (Θ) si es posible
        best_case_infer = formal_notation.replace("Θ", "Ω") if "Θ" in formal_notation else "?"

        response_steps["extraction"] = {
            "title": "Modelado Matemático Formal",
            "description": "Ecuación extraída y resuelta analíticamente.",
            "equation": relation.recurrence,
            "explanation": relation.notes,
            
            # --- NUEVO OBJETO PARA EL FRONTEND ---
            "mathematical_analysis": {
                "recurrence_relation": math_solution.get("recurrence_relation", relation.recurrence),
                "technique_used": math_solution.get("technique", "Análisis Heurístico"),
                "technique_explanation": math_solution.get("explanation", "No se detectó un patrón matemático estándar."),
                "complexity": {
                    "best_case": best_case_infer,   # Ω
                    "average_case": formal_notation, # Θ (Theta es la cota ajustada/promedio)
                    "worst_case": complexity_simple  # O (Big-O es la cota superior/peor)
                }
            }
        }

        # Añadimos también la estimación estructural producida internamente (Legacy/Respaldo)
        response_steps["structural_engine"] = {
            "title": "Estimación Estructural (ComplexityEngine)",
            "description": "Estimación basada en análisis estructural del AST.",
            "best_case": extraction.structural.best_case,
            "worst_case": extraction.structural.worst_case,
            "average_case": extraction.structural.average_case,
            "annotations": extraction.structural.annotations,
        }

        # LOGS
        print(f"✅ Ecuación Detectada: {relation.recurrence}")
        print(f"🧮 Técnica Aplicada: {math_solution.get('technique')}")
        print("📦 JSON PARA FRONTEND (Extraction):")
        print(json.dumps(response_steps["extraction"], indent=2, ensure_ascii=False))

    except Exception as e:
        # Importante imprimir el error para depurar si el solver falla
        import traceback
        traceback.print_exc() 
        return _error_response(f"Error en Extracción Matemática: {str(e)}")
    
    # --- PASO 4: ANÁLISIS FINAL (Structural vs Solver) ---
    try:

        print("\n" + "🔸" * 30)
        print("📍 PASO 4: ANÁLISIS FINAL (Priorizar Structural sobre Solver)")
        print("🔸" * 30)

        # Estrategia: Usar Solver SOLO para ecuaciones de recurrencia recursivas válidas
        # Usar Structural para todo lo demás (iterativo, híbrido, patrones especiales)
        structural = extraction.structural
        relation = extraction.relation
        
        # Detectar si la ecuación es recursiva válida para el Solver
        is_recursive_equation = (
            "T(n-" in relation.recurrence or      # Recursión lineal: T(n) = T(n-1) + ...
            "T(n/" in relation.recurrence or      # Divide y Conquista: T(n) = aT(n/b) + ...
            relation.recurrence.count("T(") >= 2  # Múltiples llamadas: T(n) = T(n-1) + T(n-2)
        )
        
        # Determinar si debemos usar Solver (recursivo puro) o Structural (resto)
        use_structural = (
            not is_recursive_equation or                   # No es ecuación recursiva
            "calls_in_loops" in structural.annotations or  # Híbrido: llamadas en bucles
            "iterativo" in relation.notes.lower()          # Explícitamente iterativo
        )
        
        if use_structural:
            print("✅ Usando análisis Structural (iterativo con llamadas anidadas)")
            main_result = structural.average_case
            best_case = structural.best_case
            worst_case = structural.worst_case
            justification = structural.annotations.get("loop_summary", "Bucles anidados detectados.")
            
            # --- MEJORA: GENERAR MATEMÁTICAS PARA ITERATIVOS ---
            # Si es O(n^2), construimos la notación de Sumatoria para que el panel se vea bonito
            math_technique = "Conteo de Operaciones (Sumatoria)"
            math_equation = "T(n) = \\sum_{i=1}^{n} T(\\text{Insertar})"
            math_equation_display = "T(n) = Σ(i=1 hasta n) T(Insertar)"  # Versión legible sin LaTeX
            math_explanation = "El algoritmo utiliza bucles anidados. El costo total es la suma del costo de cada iteración."

            if "n^2" in main_result:
                math_equation = "T(n) \\approx \\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}"
                math_equation_display = "T(n) ≈ Σ(i=1 hasta n) i = n(n+1)/2"
                math_explanation = "Se detectaron dos niveles de anidación. Esto corresponde a una serie aritmética cuadrática."
            elif "n" in main_result:
                math_equation = "T(n) = \\sum_{i=1}^{n} c = c \\cdot n"
                math_equation_display = "T(n) = Σ(i=1 hasta n) c = c·n"
                math_explanation = "Bucle simple con operaciones constantes."

            # Sobreescribimos el objeto mathematical_analysis en extraction
            # para que el Frontend tenga qué mostrar en el panel izquierdo
            response_steps["extraction"]["mathematical_analysis"] = {
                "recurrence_relation": math_equation_display,  # Versión legible
                "recurrence_relation_latex": math_equation,     # Versión LaTeX para KaTeX
                "technique_used": math_technique,
                "technique_explanation": math_explanation,
                "complexity": {
                    "best_case": best_case.replace("O", "Ω").replace("Θ", "Ω"), 
                    "average_case": main_result,
                    "worst_case": worst_case
                }
            }
            
            math_steps = []

        else:
            print("✅ Usando Solver (recursión o caso simple)")
            solver = RecurrenceSolver()
            solution = solver.solve(relation.recurrence)
            
            if solution and solution.get("complexity") != "Desconocida":
                main_result = solution.get("formal_notation", "Θ(?)")
                best_case = f"Ω({solution.get('complexity', '?').replace('O(', '').replace(')', '')})"
                worst_case = solution.get("complexity", "O(?)")
                justification = f"{solution.get('technique', 'Solver matemático')}: {solution.get('explanation', '')}"
                math_steps = []
            else:
                # Fallback a structural si solver falla
                print("⚠️ Solver falló, usando Structural como fallback")
                main_result = structural.average_case
                best_case = structural.best_case
                worst_case = structural.worst_case
                justification = "No se pudo resolver la recurrencia. Usando análisis estructural."
                math_steps = []
        
        # Obtener detalles legibles considerando el patrón detectado
        detected_pattern = structural.annotations.get("heuristica", "")
        info = _get_complexity_details(main_result, detected_pattern, worst_case)
        
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
def _get_complexity_details(theta_str: str, heuristica: str = "", worst_case: str = "") -> dict:
    """
    Traduce la notación matemática a nombres legibles para la UI.
    Considera el contexto del algoritmo (patrón detectado y peor caso).
    Ej: Theta(n) -> { name: "Lineal", desc: "..." }
    """
    s = str(theta_str).lower()
    heur_lower = heuristica.lower()
    worst_lower = worst_case.lower()
    
    # Detectar exponencial (2^n, 3^n, etc)
    if "^n" in s:
        if "fibonacci" in heur_lower:
            return {"name": "Exponencial", "desc": "Fibonacci: crece exponencialmente O(2^n). Intratable para n > 40."}
        elif "hanoi" in heur_lower:
            return {"name": "Exponencial", "desc": "Torres de Hanoi: T(n) = 2*T(n-1) + 1 → O(2^n). Intratable para n > 30."}
        elif "2^n" in s:
            return {"name": "Exponencial", "desc": "Crece exponencialmente O(2^n). Intratable para datos grandes."}
        else:
            return {"name": "Exponencial", "desc": "Crece exponencialmente. Intratable para datos grandes."}
    
    if "log" in s and "n" not in s.split("log")[0]: # O(log n)
        return {"name": "Logarítmica", "desc": "Muy eficiente. Divide el problema paso a paso."}
    elif "n log n" in s:
        # Distinguir entre QuickSort y MergeSort basado en peor caso
        if "quicksort" in heur_lower:
            return {"name": "Cuasilineal", "desc": "QuickSort: eficiente en promedio, pero O(n²) en peor caso."}
        elif "mergesort" in heur_lower or "n^2" not in worst_lower:
            return {"name": "Cuasilineal", "desc": "El estándar óptimo para ordenamientos (MergeSort)."}
        else:
            return {"name": "Cuasilineal", "desc": "Eficiencia óptima para ordenamiento (n log n)."}
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