"""High level pipeline coordinating parsing, analysis and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from analysis.complexity_engine import ComplexityEngine, ComplexityResult
from analysis.extractor import extract_generic_recurrence
from parsing.parser import Parser, ParserConfig
from .reporter import AnalysisReport, Reporter
from .validators import ValidatorSuite


@dataclass(slots=True)
class PipelineConfig:
    """Controls which stages are executed."""  """ activa o desativa fases especificas. Decide que tan profundo analizar el code"""

    enable_validations: bool = True             #corre analisis semantico
    generate_detailed_report: bool = True       #incluye detalles en el reporte final


class AnalysisPipeline:
    """Facade that exposes a simple `run` method."""    """ FACADE: ocualta toda la complejidad interna detras de una interfaz simple """

# Este constructor permite **inyectar componentes personalizados** (por ejemplo, un `Reporter` que imprima en consola o uno que guarde en JSON).

    def __init__(
        self,
        engine: ComplexityEngine | None = None,
        reporter: Reporter | None = None,
        validators: ValidatorSuite | None = None,
        config: PipelineConfig | None = None,
    ) -> None:
        self._engine = engine or ComplexityEngine()
        self._reporter = reporter or Reporter()
        self._validators = validators or ValidatorSuite.default()
        self._config = config or PipelineConfig()

    def run(self, source: str) -> AnalysisReport:
        """Execute the full pipeline on the given pseudocode."""
        parser = Parser(source, ParserConfig())
        program = parser.parse()
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
        return report
