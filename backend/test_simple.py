"""Script de prueba simple para el analizador."""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from parsing import Parser, ParserConfig
from services.analysis_service import analyze_algorithm_flow


def test_simple_analysis():
    """Prueba el análisis de un algoritmo simple."""
    source = """
Algoritmo SUMA
begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + A[i]
    end
    return suma
end
"""
    try:
        result = analyze_algorithm_flow(source)
        if result.get("success"):
            print("✓ Análisis completado correctamente")
            print(f"  Pasos: {list(result.get('steps', {}).keys())}")
            return True
        else:
            print(f"✗ Error en análisis: {result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"✗ Excepción: {e}")
        return False


def test_parser_only():
    """Prueba solo el parser."""
    source = """
begin
    x 🡨 10
    y 🡨 x + 5
end
"""
    try:
        parser = Parser(source, ParserConfig())
        program = parser.parse()
        print("✓ Parser funcionó correctamente")
        return True
    except Exception as e:
        print(f"✗ Error en parser: {e}")
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("=" * 60)
    print("Pruebas Simples")
    print("=" * 60)
    
    results = []
    results.append(("Parser", test_parser_only()))
    results.append(("Análisis completo", test_simple_analysis()))
    
    print("\n" + "=" * 60)
    print("Resumen")
    print("=" * 60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

