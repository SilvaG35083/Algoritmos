"""Test script to verify binary search best case detection."""

from parsing.parser import Parser
from analysis.complexity_engine import ComplexityEngine

# Binary search algorithm from user
code = """
busquedaBinaria(A[n], valor)      
begin
    inicio ← 0
    fin ← n - 1
    encontro ← 0
    while (inicio ≤ fin and encontro = 0) do
    begin
        medio ← (inicio + fin) div 2
        if (A[medio] = valor) then
        begin
            encontro ← 1
        end
        else
        begin
            if (A[medio] > valor) then
            begin
                fin ← medio - 1
            end
            else
            begin
                inicio ← medio + 1
            end
        end
    end
    return encontro
end
"""

def test_binary_search_best_case():
    parser = Parser()
    ast = parser.parse(code)
    
    engine = ComplexityEngine()
    result = engine.analyze(ast)
    
    print("=" * 60)
    print("ANÁLISIS DE BÚSQUEDA BINARIA")
    print("=" * 60)
    print(f"Mejor caso:    {result.best_case}")
    print(f"Peor caso:     {result.worst_case}")
    print(f"Caso promedio: {result.average_case}")
    print()
    print("Anotaciones:")
    for key, value in result.annotations.items():
        print(f"  {key}: {value}")
    print()
    
    # Verificar que el mejor caso sea O(1)
    if "Ω(1)" in result.best_case:
        print("✓ CORRECTO: Mejor caso detectado correctamente como Ω(1)")
        print("  (El elemento se encuentra en la primera comparación)")
    else:
        print(f"✗ ERROR: Se esperaba Ω(1) pero se obtuvo {result.best_case}")
    
    return result

if __name__ == "__main__":
    test_binary_search_best_case()
