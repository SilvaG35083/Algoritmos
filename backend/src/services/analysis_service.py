from parsing.lexer import Lexer       
from parsing.parser import Parser, ParserConfig, ParserError
from parsing.lexer import LexerError
from analysis.recurrence_solver import RecurrenceSolver, RecurrenceRelation
from analysis.extractor import extract_generic_recurrence

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
    try:
        parser = Parser(source_code)
        ast = parser.parse()        
        ast_display = str(ast) 

        response_steps["parser"] = {
            "title": "Análisis Sintáctico (AST)",
            "description": "Árbol generado correctamente.",
            "data": ast_display
        }
    except Exception as e:
        return _error_response(f"Error en Parser: {str(e)}")

    # --- PASO 3: EXTRACCIÓN ---
    try:
        relation = extract_generic_recurrence(ast)

        response_steps["extraction"] = {
            "title": "Modelado Matemático",
            "description": "Ecuación extraída del análisis estático.",
            "equation": relation.recurrence,
            "explanation": "Se detectó estructura Divide y Vencerás."
        }
    except Exception as e:
        return _error_response(f"Error en Extracción: {str(e)}")

    # --- PASO 4: SOLVER ---
    try:
        solver = RecurrenceSolver.default()
        solution = solver.solve(relation)

        if solution:
            response_steps["solution"] = {
                "title": "Solución Final",
                "description": solution.justification,
                "complexity": solution.theta,
                "details": solution.justification,
                "math_steps": solution.math_steps # ¡Esto es lo nuevo!
            }
        else:
             response_steps["solution"] = {
                "title": "No resuelto",
                "description": "No se encontró un patrón conocido.",
                "complexity": "Unknown",
                "details": "Intenta simplificar el algoritmo.",
                "math_steps": []
            }

    except Exception as e:
        return _error_response(f"Error resolviendo ecuación: {str(e)}")

    return {
        "success": True,
        "steps": response_steps
    }

def _error_response(msg):
    return {"success": False, "error": msg}