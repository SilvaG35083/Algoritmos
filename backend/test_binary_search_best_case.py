from analysis.complexity_engine import ComplexityEngine
from parsing.parser import Parser

# Binary search algorithm (clean ASCII version)
code = """
busquedaBinaria(A[n], valor)
begin
    inicio := 0
    fin := n - 1
    encontro := 0
    while (inicio <= fin and encontro = 0) do
    begin
        medio := (inicio + fin) div 2
        if (A[medio] = valor) then
        begin
            encontro := 1
        end
        else
        begin
            if (A[medio] > valor) then
            begin
                fin := medio - 1
            end
            else
            begin
                inicio := medio + 1
            end
        end
    end
    return encontro
end
"""


def test_binary_search_best_case() -> None:
    ast = Parser(code).parse()
    engine = ComplexityEngine()
    result = engine.analyze(ast)

    assert result.best_case
    assert "pattern_summary" in result.annotations
