# UBICACIÓN: src/llm/client.py
import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from dataclasses import dataclass
from typing import Optional

# ---------------   ------------------------------------------
# 0. CONFIGURACIÓN E INICIALIZACIÓN
# ---------------------------------------------------------

# Cargar variables de entorno
load_dotenv(find_dotenv()) 

# AQUI ESTABA EL CAMBIO: Usamos el nombre que tienes en tu .env
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Intento de fallback por si acaso, o error
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("----------------------------------------------------------------")
    print("⚠️  ADVERTENCIA CRÍTICA: GEMINI_API_KEY no encontrada en .env")
    print("----------------------------------------------------------------")
else:
    genai.configure(api_key=api_key)

# ---------------------------------------------------------
# 1. CLASES DE COMPATIBILIDAD
# ---------------------------------------------------------

@dataclass
class LLMResponse:
    """
    Clase necesaria para src/llm/assistants.py y otros módulos antiguos.
    """
    content: str
    metadata: Optional[dict] = None

# ---------------------------------------------------------
# 2. NUEVA FUNCIÓN (Para la Simulación)
# ---------------------------------------------------------

async def simple_llm_call(system: str, user: str, json_mode: bool = False) -> str:
    """
    Función directa para llamar a Gemini.
    """
    try:
        # Usamos flash por velocidad (versión más reciente)
        model_name = "gemini-2.5-flash"
        
        generation_config = {
            "temperature": 0.2, 
        }
        
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system
        )

        response = await model.generate_content_async(
            user,
            generation_config=generation_config
        )

        return response.text

    except Exception as e:
        print(f"Error en simple_llm_call: {e}")
        # Retorno seguro para no tumbar el servidor
        if json_mode: 
            return '{"error": "Fallo en LLM", "details": "Error de conexión"}'
        raise e

# ---------------------------------------------------------
# 3. CLIENTE ANTIGUO (Restaurado)
# ---------------------------------------------------------

class LLMClient:
    """
    Wrapper para mantener compatibilidad con el resto del proyecto.
    """
    def __init__(self):
        pass

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return await simple_llm_call(system=system_prompt, user=user_prompt)

    async def get_completion(self, prompt: str, system: str = "") -> LLMResponse:
        # Aquí devolvemos el OBJETO LLMResponse que pedía el error anterior
        text_result = await simple_llm_call(system=system, user=prompt)
        return LLMResponse(content=text_result)