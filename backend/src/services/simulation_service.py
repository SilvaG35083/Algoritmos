# UBICACIÓN: src/services/simulation_service.py
import json
from src.llm.prompt_library import PromptBuilder
from src.llm.client import simple_llm_call # Ahora sí importaremos del cliente real

class SimulationService:
    def __init__(self):
        self.prompts = PromptBuilder()

    async def run_simulation(self, code: str, inputs: str):
        # 1. Preparar los prompts
        system_instruction = self.prompts.build_simulation_system_instruction()
        user_message = self.prompts.build_simulation_user_prompt(code, inputs)

        try:
            # 2. Llamar al LLM
            response_text = await simple_llm_call(
                system=system_instruction, 
                user=user_message,
                json_mode=True # Activamos modo JSON
            )

            # 3. Limpieza de respuesta
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # 4. Convertir a Diccionario Python
            data = json.loads(cleaned_text)
            
            return {
                "success": True,
                "data": data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": locals().get('response_text', 'No response')
            }