"""Servicio LLM para corrección gramatical de pseudocódigo."""

from __future__ import annotations

import json
import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GrammarCorrector:
    """Corrige errores gramaticales en pseudocódigo usando LLM."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Inicializa el corrector gramatical.
        
        Args:
            provider: "openai" o "gemini"
            api_key: API key del proveedor (si None, se busca en variables de entorno)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "openai":
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")
            if OpenAI is None:
                raise ImportError("openai no está instalado. Instala con: pip install openai")
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        elif self.provider == "gemini":
            if not self.api_key:
                self.api_key = os.getenv("GEMINI_API_KEY")
            if genai is None:
                raise ImportError("google-generativeai no está instalado. Instala con: pip install google-generativeai")
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self.client = genai if self.api_key else None
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Usa 'openai' o 'gemini'")

    def correct_grammar(
        self,
        pseudocode: str,
        error_message: str,
        grammar_rules: Optional[str] = None,
    ) -> dict:
        """
        Corrige errores gramaticales en el pseudocódigo.
        
        Returns:
            dict con campos:
                - corrected_code: pseudocódigo corregido
                - explanation: explicación de las correcciones
                - confidence: nivel de confianza (0-1)
        """
        if not self.client:
            return {
                "corrected_code": pseudocode,
                "explanation": "No hay API key configurada. No se puede corregir automáticamente.",
                "confidence": 0.0,
            }

        grammar_info = grammar_rules or self._default_grammar_rules()
        
        prompt = f"""Eres un experto en pseudocódigo estructurado. Tu tarea es corregir errores gramaticales.

REGLAS DE GRAMÁTICA:
{grammar_info}

PSEUDOCÓDIGO CON ERRORES:
```
{pseudocode}
```

MENSAJE DE ERROR DEL PARSER:
{error_message}

INSTRUCCIONES:
1. Identifica y corrige los errores gramaticales en el pseudocódigo
2. Mantén la lógica del algoritmo intacta
3. Asegúrate de que el código respete todas las reglas gramaticales
4. Si hay errores ambiguos, proporciona la corrección más probable

Responde en formato JSON con:
{{
    "corrected_code": "el pseudocódigo corregido aquí",
    "explanation": "explicación detallada de las correcciones realizadas",
    "confidence": 0.95
}}
"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": "Eres un experto en corrección de pseudocódigo."},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                content = response.choices[0].message.content or "{}"
            else:  # gemini
                # Usar gemini-2.5-flash (más rápido) o gemini-2.5-pro (más potente)
                # También disponible: gemini-flash-latest (siempre el último flash)
                model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json",
                    },
                )
                content = response.text

            result = json.loads(content)
            return {
                "corrected_code": result.get("corrected_code", pseudocode),
                "explanation": result.get("explanation", "Corrección realizada."),
                "confidence": float(result.get("confidence", 0.5)),
            }
        except Exception as e:
            return {
                "corrected_code": pseudocode,
                "explanation": f"Error al corregir: {str(e)}",
                "confidence": 0.0,
            }

    def _default_grammar_rules(self) -> str:
        """Retorna las reglas gramaticales por defecto."""
        return """
REGLAS DE GRAMÁTICA DEL PSEUDOCÓDIGO (OBLIGATORIAS):

1. Estructura básica:
   - Opcional: "Algoritmo NombreAlgoritmo" antes de begin
   - Todo programa debe comenzar con "begin" y terminar con "end"
   - Los bloques de código se delimitan con "begin" y "end"
   - Ejemplo: Algoritmo QUICKSORT begin ... end

2. Asignaciones:
   - OBLIGATORIO: Usa el símbolo 🡨 (o ↨) para asignaciones
   - Ejemplo: x 🡨 5 o x ↨ 5
   - NO uses = para asignaciones

3. Bucles:
   - FOR: for i 🡨 1 to n do begin ... end
   - WHILE: while (condición) do begin ... end (paréntesis opcionales pero recomendados)
   - REPEAT: repeat ... until (condición)

4. Condicionales:
   - IF: if (condición) then begin ... end [else begin ... end]
   - Los paréntesis en la condición son opcionales pero recomendados
   - Ejemplo: if p < r then begin ... end

5. Procedimientos/Subrutinas:
   - Definición: NOMBRE_PROCEDIMIENTO(param1, param2) begin ... end
   - Llamada: CALL NOMBRE_PROCEDIMIENTO(arg1, arg2)
   - Los procedimientos se definen antes del algoritmo principal

6. Retorno:
   - return expresión

7. Operadores:
   - Aritméticos: +, -, *, /, mod, div
   - Comparación: =, ≠, <, >, ≤, ≥
   - Lógicos: and, or, not

8. Comentarios:
   - Usa ► para comentarios de línea
   - Ejemplo: ► Este es un comentario

9. Identificadores:
   - Deben comenzar con letra
   - Pueden contener letras, números y guiones bajos

10. Arreglos:
    - Acceso: A[i]
    - Rango: A[1..j]
    - Tamaño: length(A)
    - Creación: memo 🡨 new Array(n+1) o memo 🡨 new Array[n+1]

11. Operadores de comparación:
    - Puedes usar <= o ≤ (ambos funcionan)
    - Puedes usar >= o ≥ (ambos funcionan)
    - Puedes usar <> o ≠ (ambos funcionan)

IMPORTANTE: SIEMPRE usa 🡨 o ↨ para asignaciones, NUNCA uses =.
"""
