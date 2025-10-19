"""Interfaz grafica basica para ejecutar el Analizador de Complejidades."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from analyzer import AnalysisPipeline


SUMMARY_LABELS: dict[str, str] = {
    "best_case": "Mejor caso",
    "worst_case": "Peor caso",
    "average_case": "Caso promedio",
}

ANNOTATION_LABELS: dict[str, str] = {
    "pattern_summary": "Patrones detectados",
    "heuristica": "Heurística aplicada",
    "nota": "Nota",
    "statement_count": "Cantidad de sentencias",
}


class AnalyzerGUI(tk.Tk):
    """Ventana principal del analizador."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Analizador de Complejidades")
        self.geometry("960x640")
        self._pipeline = AnalysisPipeline()
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Construye los elementos de la interfaz."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entrada de pseudocodigo
        input_label = ttk.Label(main_frame, text="Pseudocódigo de entrada:")
        input_label.pack(anchor=tk.W)

        self.input_text = tk.Text(main_frame, height=18, wrap=tk.NONE, font=("Consolas", 11))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.input_text.insert(tk.END, "begin\n    ► Pegue aquí su algoritmo\nend")

        # Botones de accion
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        analyze_button = ttk.Button(button_frame, text="Analizar complejidad", command=self.on_analyze_clicked)
        analyze_button.pack(side=tk.LEFT)

        clear_button = ttk.Button(button_frame, text="Limpiar", command=self.on_clear_clicked)
        clear_button.pack(side=tk.LEFT, padx=(10, 0))

        # Zona de resultados
        result_label = ttk.Label(main_frame, text="Resultado:")
        result_label.pack(anchor=tk.W)

        self.result_text = tk.Text(main_frame, height=12, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 11))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(8, 0))

        self.status_var = tk.StringVar(value="Listo.")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)

    def on_analyze_clicked(self) -> None:
        """Analiza el pseudocodigo introducido por el usuario."""
        source = self.input_text.get("1.0", tk.END).strip()
        if not source:
            messagebox.showinfo("Analizador de Complejidades", "Ingrese un algoritmo en pseudocódigo.")
            return
            self.status_var.set("Analizando...")
        self.update_idletasks()
        try:
            report = self._pipeline.run(source)
            self._display_report(report)
            self.status_var.set("Análisis completado.")
        except Exception as exc:  # pragma: no cover - feedback directo en GUI
            messagebox.showerror("Error durante el análisis", str(exc))
            self.status_var.set("Error durante el análisis.")

    def on_clear_clicked(self) -> None:
        """Limpia los campos."""
        self.input_text.delete("1.0", tk.END)
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.configure(state=tk.DISABLED)
        self.status_var.set("Listo.")

    def _display_report(self, report) -> None:
        """Muestra el reporte estructurado en el panel de resultados."""
        lines: list[str] = []
        lines.append("=== Resumen de Complejidad ===")
        for key, value in report.summary.items():
            label = SUMMARY_LABELS.get(key, key)
            lines.append(f"{label}: {value}")
        lines.append("")
        lines.append("=== Anotaciones ===")
        for key, value in report.annotations.items():
            label = ANNOTATION_LABELS.get(key, key)
            lines.append(f"{label}: {value}")

        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))
        self.result_text.configure(state=tk.DISABLED)


def run_app() -> None:
    """Lanza la aplicación gráfica."""
    app = AnalyzerGUI()
    app.mainloop()


if __name__ == "__main__":
    run_app()
