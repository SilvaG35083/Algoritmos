"""High level pipeline coordinating parsing, analysis and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from analysis.complexity_engine import ComplexityEngine, ComplexityResult
from analysis.extractor import extract_generic_recurrence
from parsing.lexer import LexerError
from parsing.parser import Parser, ParserConfig, ParserError
from .reporter import AnalysisReport, Reporter
from .validators import ValidatorSuite


@dataclass(slots=True)
class PipelineConfig:
    """Controls which stages are executed."""

    enable_validations: bool = True             #corre analisis semantico
    generate_detailed_report: bool = True       #incluye detalles en el reporte final
    enable_grammar_correction: bool = True     #usa LLM para corregir errores gramaticales
    llm_provider: str = "openai"              #proveedor LLM para corrección


class AnalysisPipeline:
    """Facade that exposes a simple `run` method."""    """ FACADE: ocualta toda la complejidad interna detras de una interfaz simple """

# Este constructor permite **inyectar componentes personalizados** (por ejemplo, un `Reporter` que imprima en consola o uno que guarde en JSON).

    def __init__(
        self,
        engine: ComplexityEngine | None = None,
        reporter: Reporter | None = None,
        validators: ValidatorSuite | None = None,
        config: PipelineConfig | None = None,
        grammar_corrector: GrammarCorrector | None = None,
    ) -> None:
        self._engine = engine or ComplexityEngine()
        self._reporter = reporter or Reporter()
        self._validators = validators or ValidatorSuite.default()
        self._config = config or PipelineConfig()
        self._grammar_corrector = grammar_corrector

    def run(self, source: str) -> AnalysisReport:
        """Execute the full pipeline on the given pseudocode."""
        original_source = source
        corrected_source = source
        correction_info = None
        
        # Intentar parsear
        try:
            parser = Parser(corrected_source, ParserConfig())
            program = parser.parse()
        except (ParserError, LexerError) as e:
            # Si hay error y la corrección está habilitada, intentar corregir
            if self._config.enable_grammar_correction and self._grammar_corrector is not None:
                try:
                    # Solo intentar corrección si tenemos un corrector disponible
                    correction_result = self._grammar_corrector.correct_grammar(
                        pseudocode=original_source,
                        error_message=str(e),
                    )
                    
                    if correction_result["confidence"] > 0.5:
                        corrected_source = correction_result["corrected_code"]
                        correction_info = {
                            "corrected": True,
                            "explanation": correction_result["explanation"],
                            "confidence": correction_result["confidence"],
                        }
                        
                        # Intentar parsear de nuevo con el código corregido
                        parser = Parser(corrected_source, ParserConfig())
                        program = parser.parse()
                    else:
                        # Si la confianza es baja, lanzar el error original
                        raise e
                except Exception as correction_error:
                    # Si la corrección falla, lanzar el error original sin intentar crear el corrector
                    # (para evitar errores de inicialización que bloqueen el análisis)
                    raise e
            else:
                # Si la corrección está deshabilitada o no hay corrector, lanzar el error original
                raise
        
        # Depuración: imprimir el AST generado para inspección
        #print("\n--- AST GENERADO POR EL PARSER ---")
        #print(program)
        #print("--- FIN AST ---\n")
        if self._config.enable_validations:
            self._validators.validate(program)
        # Usar el extractor como única fuente: nos devuelve la recurrencia y
        # la estimación estructural (ComplexityResult). Esto unifica rutas.
        extraction = extract_generic_recurrence(program)
        result = extraction.structural
        report = self._reporter.build(program, result)
        
        # Agregar información de corrección si aplica
        if correction_info:
            report.annotations["grammar_correction"] = correction_info["explanation"]
            report.annotations["correction_confidence"] = str(correction_info["confidence"])
        
        return report
