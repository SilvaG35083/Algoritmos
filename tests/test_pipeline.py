"""Smoke tests for the analysis pipeline."""

from analyzer.pipeline import AnalysisPipeline


def test_pipeline_runs_with_empty_program() -> None:
    pipeline = AnalysisPipeline()
    pseudocode = "begin\nend"
    report = pipeline.run(pseudocode)
    assert report.summary["best_case"] == "Ω(1)"
    assert report.summary["worst_case"] == "O(1)"
    assert report.summary["average_case"] == "Θ(1)"
    assert "pattern_summary" in report.annotations


def test_linear_for_loop_detected() -> None:
    pipeline = AnalysisPipeline()
    pseudocode = """begin
    for i 🡨 1 to n do
    begin
        x 🡨 x + 1
    end
end"""
    report = pipeline.run(pseudocode)
    assert report.summary["worst_case"] == "O(n)"
    assert report.summary["best_case"] == "Ω(n)"
    assert report.summary["average_case"] == "Θ(n)"


def test_recursion_heuristic_applied() -> None:
    pipeline = AnalysisPipeline()
    pseudocode = """begin
    if (n <= 1) then
    begin
        resultado 🡨 1
    end
    else
    begin
        CALL self(n - 1)
        CALL self(n - 2)
    end
end"""
    report = pipeline.run(pseudocode)
    assert report.summary["worst_case"] == "O(n log n)"
    assert report.summary["average_case"] == "Θ(n log n)"
    assert "patron recursivo" in report.annotations["pattern_summary"].lower()
