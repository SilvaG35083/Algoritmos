"""Servicio de chat interactivo con LLM para generar algoritmos y análisis detallado."""

from __future__ import annotations

import json
import os
import time
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class ChatMessage:
    """Representa un mensaje en el chat."""

    def __init__(self, role: str, content: str, timestamp: Optional[float] = None):
        self.role = role  # "user", "assistant", "system"
        self.content = content
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class LLMChatService:
    """Servicio de chat interactivo con LLM para análisis de algoritmos."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Inicializa el servicio de chat.
        
        Args:
            provider: "openai" o "gemini"
            api_key: API key del proveedor
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "openai":
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")
            if OpenAI is None:
                raise ImportError("openai no está instalado")
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif self.provider == "gemini":
            if not self.api_key:
                self.api_key = os.getenv("GEMINI_API_KEY")
            if genai is None:
                raise ImportError("google-generativeai no está instalado")
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self.client = genai if self.api_key else None
            # Usar gemini-2.5-flash (más rápido y gratuito) o gemini-2.5-pro (más potente)
            # También disponible: gemini-flash-latest (siempre el último flash)
            self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        else:
            raise ValueError(f"Proveedor no soportado: {provider}")

    def generate_algorithm_with_analysis(
        self, user_query: str, conversation_history: Optional[List[ChatMessage]] = None
    ) -> dict:
        """
        Genera un algoritmo en pseudocódigo y su análisis detallado.
        
        Returns:
            dict con:
                - pseudocode: pseudocódigo generado
                - summary: resumen del análisis
                - steps: lista de pasos de análisis línea por línea
                - equations: ecuaciones de recurrencia si aplica
                - recursion_tree: representación del árbol de recursión si aplica
                - method: método utilizado (divide y vencerás, programación dinámica, etc.)
                - tokens_used: tokens consumidos
                - latency_ms: latencia en milisegundos
        """
        if not self.client:
            return self._stub_response(user_query)

        start_time = time.time()
        
        # Construir historial de conversación
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(),
            }
        ]
        
        if conversation_history:
            for msg in conversation_history[-10:]:  # Últimos 10 mensajes
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        messages.append({
            "role": "user",
            "content": user_query,
        })

        try:
            if self.provider == "openai":
                if not self.client:
                    raise ValueError("No hay API key configurada para OpenAI")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                content = response.choices[0].message.content or "{}"
                tokens_used = response.usage.total_tokens if hasattr(response, "usage") else None
            else:  # gemini
                if not self.client:
                    raise ValueError("No hay API key configurada para Gemini")
                
                # Extraer system prompt y construir prompt completo
                system_prompt = None
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    elif msg["role"] == "user":
                        user_messages.append(msg["content"])
                    elif msg["role"] == "assistant":
                        # Para Gemini, incluimos las respuestas anteriores en el contexto
                        user_messages.append(f"Respuesta anterior: {msg['content']}")
                
                # Construir prompt completo
                full_prompt = ""
                if system_prompt:
                    full_prompt += f"{system_prompt}\n\n"
                
                # Agregar historial de conversación
                if len(user_messages) > 1:
                    full_prompt += "Historial de conversación:\n"
                    for i, msg in enumerate(user_messages[:-1], 1):
                        full_prompt += f"{i}. {msg}\n"
                    full_prompt += "\n"
                
                # Agregar la consulta actual
                full_prompt += f"Consulta actual: {user_messages[-1] if user_messages else user_query}"
                
                # Generar respuesta - intentar con modelos alternativos si falla
                model_names_to_try = [
                    self.model,  # El modelo configurado
                    "gemini-2.5-flash",  # Modelo rápido y estable
                    "gemini-flash-latest",  # Siempre el último flash disponible
                    "gemini-2.0-flash",     # Versión anterior estable
                    "gemini-2.5-pro",       # Modelo potente
                    "gemini-pro-latest",    # Siempre el último pro disponible
                ]
                
                # Eliminar duplicados manteniendo el orden
                seen = set()
                model_names_to_try = [m for m in model_names_to_try if not (m in seen or seen.add(m))]
                
                last_error = None
                for model_name in model_names_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(
                            full_prompt,
                            generation_config={
                                "temperature": 0.3,
                                "response_mime_type": "application/json",
                            },
                        )
                        content = response.text
                        tokens_used = None
                        # Si llegamos aquí, el modelo funcionó
                        break
                    except Exception as e:
                        last_error = e
                        # Si es el último modelo, lanzar el error
                        if model_name == model_names_to_try[-1]:
                            raise last_error
                        # Si no, continuar con el siguiente modelo
                        continue

            latency_ms = (time.time() - start_time) * 1000
            
            # Intentar parsear JSON con manejo de errores mejorado
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_err:
                # Si falla el parseo, intentar extraer JSON del texto
                print(f"⚠️ Error al parsear JSON: {json_err}")
                print(f"Contenido recibido (primeros 500 chars): {content[:500]}")
                
                # Intentar encontrar JSON en el contenido
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except:
                        raise ValueError(
                            f"Error al parsear respuesta JSON del LLM. "
                            f"Contenido recibido: {content[:200]}..."
                        ) from json_err
                else:
                    raise ValueError(
                        f"El LLM no devolvió JSON válido. "
                        f"Respuesta: {content[:200]}..."
                    ) from json_err
            
            return {
                "pseudocode": result.get("pseudocode", "").strip(),
                "summary": result.get("summary", "").strip(),
                "steps": result.get("steps", []),
                "equations": result.get("equations", []),
                "recursion_tree": result.get("recursion_tree"),
                "method": result.get("method", "Desconocido"),
                "complexity_analysis": result.get("complexity_analysis", {}),
                "tokens_used": tokens_used,
                "latency_ms": round(latency_ms, 2),
            }
        except Exception as e:
            error_message = self._parse_error(e)
            return {
                "pseudocode": "",
                "summary": error_message,
                "steps": [],
                "equations": [],
                "recursion_tree": None,
                "method": "Error",
                "complexity_analysis": {},
                "tokens_used": None,
                "latency_ms": None,
                "error": True,
                "error_details": str(e),
            }

    def _parse_error(self, error: Exception) -> str:
        """Parsea errores de la API y devuelve mensajes amigables."""
        error_str = str(error)
        
        # Error 404: Model not found (Gemini)
        if "404" in error_str or "not found" in error_str.lower():
            if "gemini" in error_str.lower() or "model" in error_str.lower():
                return (
                    "⚠️ Error: Modelo de Gemini no encontrado.\n\n"
                    "El sistema intentó automáticamente varios modelos pero ninguno funcionó.\n\n"
                    "Pasos para resolver:\n"
                    "1. Ejecuta el script de diagnóstico: python backend/test_gemini_models.py\n"
                    "2. Verifica que tu GEMINI_API_KEY sea válida\n"
                    "3. Configura GEMINI_MODEL en .env con un modelo de la lista disponible\n"
                    "4. Modelos recomendados: gemini-2.5-flash, gemini-2.5-pro, gemini-flash-latest\n"
                    "5. Verifica la documentación: https://ai.google.dev/models/gemini"
                )
            return f"⚠️ Error 404: Recurso no encontrado. {error_str}"
        
        # Error 429: Quota exceeded
        if "429" in error_str or "insufficient_quota" in error_str.lower() or "quota" in error_str.lower():
            return (
                "⚠️ Error: Has excedido tu cuota. "
                "Opciones:\n"
                "1. Si usas OpenAI: Recarga créditos en https://platform.openai.com/account/billing\n"
                "2. Cambia a Gemini (gratis) seleccionando 'Gemini' en el selector de proveedor\n"
                "3. Espera a que se renueve tu límite de uso"
            )
        
        # Error 401: Invalid API key
        if "401" in error_str or ("invalid" in error_str.lower() and "api" in error_str.lower()):
            provider_name = "OpenAI" if self.provider == "openai" else "Gemini"
            return (
                f"⚠️ Error: API key inválida o no configurada para {provider_name}. "
                f"Verifica tu {'OPENAI_API_KEY' if self.provider == 'openai' else 'GEMINI_API_KEY'} "
                "en el archivo .env o variables de entorno."
            )
        
        # Error 429: Rate limit
        if "rate_limit" in error_str.lower() or "too many requests" in error_str.lower():
            return (
                "⚠️ Error: Demasiadas solicitudes. "
                "Espera unos momentos antes de intentar de nuevo."
            )
        
        # Error genérico de OpenAI
        if "openai" in error_str.lower():
            return (
                f"⚠️ Error de OpenAI: {error_str}\n"
                "Sugerencia: Intenta cambiar a Gemini o verifica tu configuración."
            )
        
        # Error genérico de Gemini
        if "gemini" in error_str.lower():
            return (
                f"⚠️ Error de Gemini: {error_str}\n"
                "Sugerencia: Verifica tu GEMINI_API_KEY y que el modelo sea válido."
            )
        
        # Error genérico
        return f"⚠️ Error al generar respuesta: {error_str}"

    def _get_system_prompt(self) -> str:
        """Retorna el prompt del sistema para el análisis de algoritmos."""
        return """Eres un experto analista de algoritmos. Tu tarea es:

1. Generar pseudocódigo estructurado que respete la gramática del proyecto
2. Analizar la complejidad línea por línea
3. Identificar el método algorítmico utilizado
4. Proporcionar ecuaciones de recurrencia cuando aplique
5. Generar representaciones de árboles de recursión cuando sea relevante

REGLAS DE GRAMÁTICA:
- Usa begin/end para bloques
- Usa 🡨 para asignaciones
- FOR: for i 🡨 1 to n do begin ... end
- WHILE: while condición do begin ... end
- IF: if condición then begin ... end [else begin ... end]
- CALL para llamadas a procedimientos
- return para retornos

FORMATO DE RESPUESTA (JSON):
{
    "pseudocode": "código completo aquí",
    "summary": "resumen del análisis de complejidad",
    "method": "divide y vencerás | programación dinámica | voraz | etc.",
    "steps": [
        {
            "line_number": 1,
            "line_code": "begin",
            "title": "Inicio del programa",
            "detail": "Descripción detallada",
            "cost": "O(1)",
            "method_used": "inicialización",
            "recurrence": null,
            "explanation": "Explicación del costo"
        }
    ],
    "equations": [
        {
            "type": "recurrence",
            "equation": "T(n) = 2T(n/2) + O(n)",
            "explanation": "Divide el problema en dos subproblemas de tamaño n/2",
            "solution": "T(n) = O(n log n)"
        }
    ],
    "recursion_tree": {
        "description": "Árbol de recursión para el algoritmo",
        "levels": [
            {"level": 0, "nodes": ["T(n)"], "cost": "O(n)"},
            {"level": 1, "nodes": ["T(n/2)", "T(n/2)"], "cost": "O(n)"},
            {"level": 2, "nodes": ["T(n/4)", "T(n/4)", "T(n/4)", "T(n/4)"], "cost": "O(n)"}
        ],
        "total_cost": "O(n log n)"
    },
    "complexity_analysis": {
        "best_case": "O(n log n)",
        "worst_case": "O(n log n)",
        "average_case": "O(n log n)",
        "space_complexity": "O(n)"
    }
}

Sé detallado y preciso en tu análisis."""

    def _stub_response(self, query: str) -> dict:
        """Respuesta simulada cuando no hay API key."""
        return {
            "pseudocode": """begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + A[i]
    end
    return suma
end""",
            "summary": "Complejidad: O(n) en todos los casos. (Respuesta simulada - configura OPENAI_API_KEY o GEMINI_API_KEY)",
            "method": "Iterativo",
            "steps": [
                {
                    "line_number": 1,
                    "line_code": "begin",
                    "title": "Inicio",
                    "detail": "Inicio del programa",
                    "cost": "O(1)",
                    "method_used": "inicialización",
                    "recurrence": None,
                    "explanation": "Costo constante"
                },
            ],
            "equations": [],
            "recursion_tree": None,
            "complexity_analysis": {
                "best_case": "O(n)",
                "worst_case": "O(n)",
                "average_case": "O(n)",
                "space_complexity": "O(1)"
            },
            "tokens_used": None,
            "latency_ms": None,
        }
