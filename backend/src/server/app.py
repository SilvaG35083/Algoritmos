"""Aplicacion FastAPI que expone el analizador como servicio REST."""

from __future__ import annotations

from typing import List, Dict, Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from analyzer import AnalysisPipeline
from analyzer.samples import SampleAlgorithm
from . import models
from .deps import get_pipeline, get_samples
from services.analysis_service import analyze_algorithm_flow


def create_app() -> FastAPI:
    app = FastAPI(title="Analizador de Complejidades", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=models.HealthResponse)
    def health_check() -> models.HealthResponse:
        return models.HealthResponse(status="ok", version="0.2.0")

    @app.get("/api/samples", response_model=List[models.SampleAlgorithmOut])
    def list_samples(samples: List[SampleAlgorithm] = Depends(get_samples)) -> List[models.SampleAlgorithmOut]:
        return [
            models.SampleAlgorithmOut(
                name=item.name,
                category=item.category,
                description=item.description,
                pseudocode=item.pseudocode,
                expected_complexity=item.expected_complexity,
            )
            for item in samples
        ]

    @app.post("/api/analyze")
    def analyze_algorithm(
        payload: models.AnalyzeRequest,
        # pipeline ya no es necesario aquí
    ) -> Dict[str, Any]:
        
        source = payload.source.strip()
        if not source:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El pseudocodigo no puede estar vacio.")
        
        # --- USAMOS EL NUEVO SERVICIO ---
        result = analyze_algorithm_flow(source)
        
        # Si el servicio reporta un error interno controlado
        if not result.get("success"):
             # Opcional: puedes retornar el error 400 o devolver el JSON con success:false
             # Para debugging, devolver el JSON suele ser útil
             pass 

        return result
    
    @app.post("/api/analyze-file")
    async def analyze_algorithm_file(
        file: UploadFile = File(...),
        # pipeline ya no es necesario aquí
    ) -> Dict[str, Any]:
        
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo esta vacio.",
            )
        try:
            source = raw_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo decodificar el archivo como UTF-8.",
            ) from exc
            
        if not source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no contenia pseudocodigo.",
            )
            
        # --- USAMOS EL NUEVO SERVICIO ---
        result = analyze_algorithm_flow(source)
        
        return result

    return app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)
