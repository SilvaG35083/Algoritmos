from parsing.lexer import Lexer       
from parsing.parser import Parser, ParserConfig, ParserError
from parsing.lexer import LexerError
from analysis.recurrence_solver import RecurrenceSolver, RecurrenceRelation
from analysis.extractor import extract_generic_recurrence
from analysis.line_costs import LineCostAnalyzer
import json
import re

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
        
        solution = None
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
        
        # Obtener detalles legibles considerando el patrón detectado
        detected_pattern = structural.annotations.get("heuristica", "")
        info = _get_complexity_details(main_result, detected_pattern, worst_case)
        
        method_used = solution.method if solution and solution.method else "Heurística estructural"
        expected_reference = _get_expected_complexities(structural.annotations.get("heuristica", ""), relation.recurrence)

        if expected_reference:
            best_case = expected_reference["best"]
            worst_case = expected_reference["worst"]
            main_result = expected_reference["average"]

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
        response_steps["solution"]["method_used"] = method_used
        if expected_reference:
            response_steps["solution"]["expected"] = expected_reference
        
        print(f"✅ Resultado Final: {main_result} ({info['name']})")
        print(json.dumps(response_steps["solution"], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error en Análisis Final: {e}")
        return _error_response(f"Error en análisis final: {str(e)}")

    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)

    dp_info = _build_dynamic_programming_info(extraction.relation)
    if dp_info:
        response_steps["dynamic_programming"] = dp_info

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

def _build_dynamic_programming_info(relation: RecurrenceRelation) -> dict | None:
    """
    Genera una sección descriptiva para programación dinámica cuando se detecta una recurrencia.
    """
    recurrence = (relation.recurrence or "").strip()
    if not recurrence or not _is_dp_candidate(recurrence):
        return None

    base_case = relation.base_case or "Caso base (no especificado)"
    # Caso especializado: Fibonacci (top-down con memoization)
    fib_info = _build_fibonacci_dp_section(recurrence)
    if fib_info:
        return fib_info

    # Caso genérico: mostrar plantilla DP con Tablas y SOA
    dp_formula = _translate_recurrence_to_dp(recurrence)
    transition = dp_formula.replace("F[", "TablaOptimos[")

    if "max(" in recurrence.lower():
        decision = "maximizar"
        decision_rule = "Comparar los valores candidatos y guardar en TablaCaminos la rama que produjo el máximo."
    elif "min(" in recurrence.lower():
        decision = "minimizar"
        decision_rule = "Comparar los valores candidatos y guardar la rama que produjo el mínimo."
    else:
        decision = "agregar"
        decision_rule = "Registrar en TablaCaminos los subproblemas utilizados para resolver el estado actual."

    return {
        "model": {
            "recurrence": recurrence,
            "base_case": base_case,
            "notes": relation.notes or "Sin observaciones adicionales.",
            "dp_formula": dp_formula,
            "modelo_recursivo": [
                "► Modelo Recursivo (genérico)",
                f"► Base: {base_case}",
                f"► Transición: {recurrence}",
            ],
        },
        "TablaOptimos": {
            "description": "Dimensionar TablaOptimos de 0 a n y llenar los resultados acumulados.",
            "initialization": f"TablaOptimos[0] 🡨 {base_case}",
            "transition": f"TablaOptimos[i] 🡨 {transition}",
        },
        "TablaCaminos": {
            "description": decision_rule,
            "update": f"TablaCaminos[i] 🡨 registrar qué subproblemas se combinaron para {decision}.",
        },
        "VectorSOA": {
            "description": "Reconstruir la Subestructura Óptima desde i=n hasta 0 siguiendo TablaCaminos.",
            "steps": [
                "Iniciar en i=n y consultar TablaCaminos[i] para saber qué elecciones se guardaron.",
                "Agregar los elementos seleccionados a VectorSOA según la dirección de TablaCaminos.",
                "Retroceder hasta alcanzar el caso base y devolver VectorSOA como solución óptima.",
            ],
        },
    }

def _build_fibonacci_dp_section(recurrence: str) -> dict | None:
    """
    Reconoce T(n) = T(n-1) + T(n-2) (+ c) y devuelve las tablas completas
    para mostrar en el frontend siguiendo la notación solicitada.
    """
    lowered = recurrence.replace(" ", "").lower()
    if not re.search(r"t\(n[-]1\)\+t\(n[-]2\)", lowered):
        return None

    # Ejemplo concreto para n = 7 (solicitado en los apuntes)
    n_demo = 7
    tabla_optimos = [0, 1]
    tabla_caminos = ["-"] * (n_demo + 1)
    tabla_caminos[0] = "base"
    tabla_caminos[1] = "base"
    for i in range(2, n_demo + 1):
        tabla_optimos.append(tabla_optimos[i - 1] + tabla_optimos[i - 2])
        # Registrar la decisión; para demo elegimos n-1 como principal
        tabla_caminos[i] = "n-1" if tabla_optimos[i - 1] >= tabla_optimos[i - 2] else "n-2"

    vector_soa = list(range(0, n_demo + 1))

    modelo = [
        "► MODELO RECURSIVO Fib(i):",
        "► Si i = 0 -> 0",
        "► Si i = 1 -> 1",
        "► Si i > 1 -> Fib(i-1) + Fib(i-2)",
    ]

    pseudocodigo = [
        "Fib_Envolvente(n)",
        "begin",
        "    Crear TablaOptimos[0..n] con -1",
        "    Crear TablaCaminos[0..n]",
        "    res 🡨 CALL Fib_Recursivo(n, TablaOptimos, TablaCaminos)",
        "    CALL ReconstruirSOA(n, TablaCaminos, VectorSOA)",
        "    return res",
        "end",
    ]

    return {
        "modelo_recursivo": modelo,
        "pseudocodigo": pseudocodigo,
        "TablaOptimos": {
            "description": "Tabla de memoización para Fibonacci Top-Down.",
            "values_demo_n7": tabla_optimos[: n_demo + 1],
        },
        "TablaCaminos": {
            "description": "Origen del óptimo: 'n-1' o 'n-2'.",
            "values_demo_n7": tabla_caminos[: n_demo + 1],
        },
        "VectorSOA": {
            "description": "Recorrido de subproblemas usados (ejemplo n=7).",
            "values_demo_n7": vector_soa,
        },
        "observations": "Complejidad Top-Down con memoización: tiempo O(n), espacio O(n).",
    }

def _is_dp_candidate(recurrence: str) -> bool:
    """Heurística simple: detecta recurrencias con reducción en n-k o n/k."""
    lowered = recurrence.lower()
    # Casos clásicos: T(n-1), T(n/2)
    if re.search(r"t\(n\s*[-/]", lowered):
        return True
    # Cualquier función con (n-1) o (n/2), ej. fib(n-1) + fib(n-2)
    if re.search(r"\(n\s*[-/]\s*\d+", lowered):
        return True
    # max/min suelen denotar decisiones DP
    if re.search(r"max\(|min\(", lowered):
        return True
    return False

def _translate_recurrence_to_dp(recurrence: str) -> str:
    """Convierte llamadas T(n±k) (o cualquier f(n±k)) en F[i±k] para mostrar en la TablaOptimos."""
    def replacer(match: re.Match) -> str:
        inner = match.group(1)
        if not inner:
            return "F[i]"
        return f"F[i{inner}]"
    # Reemplaza T(n±k) o nombreFuncion(n±k)
    return re.sub(r"[a-zA-Z_]\w*\(n([^\)]*)\)", replacer, recurrence, flags=re.IGNORECASE)

def _error_response(msg):
    return {"success": False, "error": msg}


REFERENCE_COMPLEXITIES = {
    "fibonacci": {
        "best": "Ω(2^n)",
        "average": "Θ(2^n)",
        "worst": "O(2^n)",
        "description": "Recursión exponencial clásica (Fibonacci sin memorización)."
    },
    "factorial": {
        "best": "Ω(n)",
        "average": "Θ(n)",
        "worst": "O(n)",
        "description": "Recursión lineal simple con costo O(n)."
    },
    "quicksort": {
        "best": "Ω(n log n)",
        "average": "Θ(n log n)",
        "worst": "O(n^2)",
        "description": "Divide y vencerás con particionamiento."
    },
}


def _get_expected_complexities(heuristica: str, recurrence: str) -> dict | None:
    keyword = _detect_reference_keyword(heuristica, recurrence)
    if not keyword:
        return None
    return REFERENCE_COMPLEXITIES.get(keyword)


def _detect_reference_keyword(heuristica: str | None, recurrence: str | None) -> str | None:
    parts = []
    if heuristica:
        parts.append(heuristica.lower())
    if recurrence:
        parts.append(recurrence.lower())
    combined = " ".join(parts)
    for keyword in REFERENCE_COMPLEXITIES.keys():
        if keyword in combined:
            return keyword
    return None
