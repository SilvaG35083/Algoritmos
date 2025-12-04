from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.simulation_service import SimulationService

# 1. Creamos el Router (es como un mini-servidor solo para esto)
router = APIRouter(tags=["Simulation"])

# 2. Instanciamos el servicio (la lógica que creamos antes)
simulation_service = SimulationService()

# 3. Definimos qué datos va a recibir (el contrato)
class SimulationRequest(BaseModel):
    code: str      # El código del algoritmo
    inputs: str    # Ej: "n=5"

# 4. Creamos el Endpoint (la URL)
@router.post("/api/simulate")
async def simulate_algorithm_endpoint(request: SimulationRequest):
    """
    Recibe un algoritmo y sus inputs, y devuelve el árbol de ejecución (JSON).
    """
    # Llamamos a la lógica del servicio
    result = await simulation_service.run_simulation(request.code, request.inputs)
    
    if not result["success"]:
        # Si falló, devolvemos un error 500
        raise HTTPException(status_code=500, detail=result.get("error"))
        
    return result["data"]