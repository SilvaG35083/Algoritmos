"""Aplicacion FastAPI que expone el analizador como servicio REST."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv no está instalado, usar variables de entorno del sistema
    pass

from analyzer import AnalysisPipeline
from analyzer.samples import SampleAlgorithm
from llm.chat_service import LLMChatService, ChatMessage
from services.analysis_service import analyze_algorithm_flow
from . import models
from .deps import get_pipeline, get_samples
from .llm_service import llm_analyze


def create_app() -> FastAPI:
    app = FastAPI(title="Analizador de Complejidades", version="0.3.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación y los devuelve en formato legible."""
        errors = exc.errors()
        error_messages = []
        for error in errors:
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "Error de validación")
            error_messages.append(f"{field}: {msg}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Error de validación en los datos enviados",
                "errors": error_messages,
                "full_errors": errors,
            },
        )

    @app.get("/api/health", response_model=models.HealthResponse)
    def health_check() -> models.HealthResponse:
        return models.HealthResponse(status="ok", version="0.3.0")

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
    ):
        """
        Analiza un algoritmo y devuelve el resultado en formato detallado para el modal.
        Usa el servicio analysis_service que genera el formato esperado por el frontend.
        """
        source = payload.source.strip()
        if not source:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El pseudocodigo no puede estar vacio.")
        
        try:
            # Usar el servicio que genera el formato correcto para el modal
            result = analyze_algorithm_flow(source)
            return result
        except Exception as exc:
            error_msg = str(exc)
            # Si hay información de corrección en el error, incluirla
            if "corrección" in error_msg.lower() or "correction" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Error de parsing. {error_msg}",
                }
            return {
                "success": False,
                "error": f"Error al analizar el algoritmo: {error_msg}",
            }

    @app.post("/api/analyze-file", response_model=models.AnalyzeResponse)
    async def analyze_algorithm_file(
        file: UploadFile = File(...),
        pipeline: AnalysisPipeline = Depends(get_pipeline),
    ) -> models.AnalyzeResponse:
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
        try:
            report = pipeline.run(source)
            summary = models.ComplexitySummary(**report.summary)
            return models.AnalyzeResponse(summary=summary, annotations=report.annotations)
        except Exception as exc:
            error_msg = str(exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al analizar el archivo: {error_msg}",
            ) from exc

    @app.post("/api/llm/analyze", response_model=models.LLMChatResponse)
    def llm_analyze_endpoint(payload: models.LLMChatRequest) -> models.LLMChatResponse:
        query = payload.query.strip()
        if len(query) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La peticion es demasiado corta.")
        provider = getattr(payload, "provider", None)
        return llm_analyze(query, provider=provider)

    @app.post("/api/llm/chat", response_model=models.LLMChatResponse)
    def llm_chat_endpoint(payload: models.ChatRequest) -> models.LLMChatResponse:
        """Endpoint de chat interactivo con historial de conversación."""
        message = payload.message.strip()
        if len(message) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El mensaje no puede estar vacío.")
        
        provider = payload.provider or "openai"
        
        # Convertir historial de conversación
        history = None
        if payload.conversation_history:
            history = [
                ChatMessage(role=msg.role, content=msg.content, timestamp=msg.timestamp)
                for msg in payload.conversation_history
            ]
        
        try:
            chat_service = LLMChatService(provider=provider)
            result = chat_service.generate_algorithm_with_analysis(message, conversation_history=history)
            
            # Convertir a formato de respuesta con validación de tipos
            steps = []
            for step in result.get("steps", []):
                # Convertir line_number a int si es string
                line_number = step.get("line_number")
                if isinstance(line_number, str):
                    try:
                        line_number = int(line_number)
                    except (ValueError, TypeError):
                        line_number = None
                elif not isinstance(line_number, int):
                    line_number = None
                
                steps.append(
                    models.LLMAnalysisStep(
                        title=str(step.get("title", "Paso")),
                        detail=str(step.get("detail", "")),
                        cost=str(step.get("cost")) if step.get("cost") else None,
                        recurrence=str(step.get("recurrence")) if step.get("recurrence") else None,
                        line=str(step.get("line_code") or step.get("line")) if (step.get("line_code") or step.get("line")) else None,
                        line_number=line_number,
                        method_used=str(step.get("method_used")) if step.get("method_used") else None,
                        explanation=str(step.get("explanation")) if step.get("explanation") else None,
                    )
                )
            
            equations = None
            if result.get("equations"):
                equations = [
                    models.Equation(
                        type=eq.get("type", "recurrence"),
                        equation=eq.get("equation", ""),
                        explanation=eq.get("explanation", ""),
                        solution=eq.get("solution"),
                    )
                    for eq in result["equations"]
                ]
            
            recursion_tree = None
            if result.get("recursion_tree"):
                rt = result["recursion_tree"]
                # Convertir y validar niveles del árbol de recursión
                validated_levels = []
                for level in rt.get("levels", []):
                    # Convertir level a int si es string
                    level_num = level.get("level", 0)
                    if isinstance(level_num, str):
                        try:
                            level_num = int(level_num)
                        except (ValueError, TypeError):
                            level_num = 0
                    elif not isinstance(level_num, int):
                        level_num = 0
                    
                    # Asegurar que nodes es una lista
                    nodes = level.get("nodes", [])
                    if not isinstance(nodes, list):
                        nodes = []
                    
                    validated_levels.append(
                        models.RecursionTreeLevel(
                            level=level_num,
                            nodes=nodes,
                            cost=str(level.get("cost", "")),
                        )
                    )
                
                recursion_tree = models.RecursionTree(
                    description=str(rt.get("description", "")),
                    levels=validated_levels,
                    total_cost=str(rt.get("total_cost", "")),
                )
            
            complexity_analysis = None
            if result.get("complexity_analysis"):
                comp = result["complexity_analysis"]
                complexity_analysis = models.ComplexityAnalysis(
                    best_case=comp.get("best_case", ""),
                    worst_case=comp.get("worst_case", ""),
                    average_case=comp.get("average_case", ""),
                    space_complexity=comp.get("space_complexity"),
                )
            
            # Si hay un error, mostrar el mensaje de error en el summary
            if result.get("error"):
                summary = result.get("summary", "Error desconocido")
            else:
                summary_parts = [result.get("summary", "Análisis generado por LLM.")]
                if result.get("method"):
                    summary_parts.append(f"Método: {result['method']}")
                summary = " | ".join(summary_parts)
            
            # Obtener el proveedor/modelo usado
            provider = payload.provider or "openai"
            model_info = f"Modelo: {provider.upper()}"
            if provider == "openai":
                model_info += " (GPT-4 o GPT-3.5-turbo)"
            elif provider == "gemini":
                model_info += " (Gemini Pro)"
            
            return models.LLMChatResponse(
                pseudocode=result.get("pseudocode", "").strip(),
                summary=summary,
                steps=steps,
                raw_text=result.get("raw_text") or result.get("error_details"),
                method=result.get("method"),
                equations=equations,
                recursion_tree=recursion_tree,
                complexity_analysis=complexity_analysis,
                tokens_used=result.get("tokens_used"),
                latency_ms=result.get("latency_ms"),
                model_used=model_info,  # Agregar información del modelo
            )
        except Exception as exc:
            # Log del error completo para debugging
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ Error en /api/llm/chat: {error_traceback}")
            
            # Mejorar mensaje de error para errores de cuota
            error_str = str(exc)
            error_type = type(exc).__name__
            
            # Errores específicos
            if "429" in error_str or "quota" in error_str.lower():
                detail = (
                    "Has excedido tu cuota. "
                    "Intenta cambiar a Gemini o recarga créditos."
                )
            elif "404" in error_str or "not found" in error_str.lower():
                if "gemini" in error_str.lower() or "model" in error_str.lower():
                    detail = (
                        "Modelo de Gemini no encontrado. "
                        "Ejecuta 'python backend/test_gemini_models.py' para ver modelos disponibles."
                    )
                else:
                    detail = f"Recurso no encontrado: {error_str}"
            elif "401" in error_str or ("invalid" in error_str.lower() and "api" in error_str.lower()):
                detail = (
                    f"API key inválida para {provider}. "
                    f"Verifica tu {'OPENAI_API_KEY' if provider == 'openai' else 'GEMINI_API_KEY'} en .env"
                )
            elif "JSON" in error_type or "json" in error_str.lower():
                detail = (
                    f"Error al parsear respuesta del LLM: {error_str}. "
                    "El modelo puede haber devuelto un formato inválido."
                )
            else:
                detail = f"Error en el servicio de chat ({error_type}): {error_str}"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail,
            ) from exc

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)
