"""Script de prueba simple para el parser."""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from parsing import Parser, ParserConfig, ParserError


def test_simple_algorithm():
    """Prueba un algoritmo simple."""
    source = """
Algoritmo TEST
begin
    x 🡨 5
    print(x)
end
"""
    try:
        parser = Parser(source, ParserConfig())
        program = parser.parse()
        print("✓ Algoritmo simple parseado correctamente")
        print(f"  Nombre: {program.name}")
        return True
    except ParserError as e:
        print(f"✗ Error: {e}")
        return False


def test_quicksort():
    """Prueba QuickSort."""
    source = """
Algoritmo QUICKSORT(A, p, r)
begin
    if (p < r) then
    begin
        q 🡨 CALL PARTITION(A, p, r)
        CALL QUICKSORT(A, p, q - 1)
        CALL QUICKSORT(A, q + 1, r)
    end
end
"""
    try:
        parser = Parser(source, ParserConfig())
        program = parser.parse()
        print("✓ QuickSort parseado correctamente")
        print(f"  Nombre: {program.name}")
        return True
    except ParserError as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("=" * 60)
    print("Pruebas del Parser")
    print("=" * 60)
    
    results = []
    results.append(("Algoritmo simple", test_simple_algorithm()))
    results.append(("QuickSort", test_quicksort()))
    
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

