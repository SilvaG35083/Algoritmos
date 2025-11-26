"""Utility script to validate that all bundled pseudocode samples parse successfully."""

from __future__ import annotations

import sys
from typing import Iterable, Tuple

sys.path.insert(0, "src")

from analyzer.samples import load_samples  # noqa: E402
from parsing import Parser, ParserConfig, ParserError  # noqa: E402


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _sanitize(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


def _parse_snippet(name: str, code: str) -> Tuple[bool, str]:
    try:
        Parser(code, ParserConfig()).parse()
        return True, "OK"
    except ParserError as exc:
        return False, f"ParserError: {_sanitize(str(exc))}"
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, f"Unexpected: {_sanitize(str(exc))}"


def main() -> None:
    _print_header("Validando algoritmos de muestra")
    failures = []
    for sample in load_samples():
        success, message = _parse_snippet(sample.name, sample.pseudocode)
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {sample.name}: {message}")
        if not success:
            failures.append(sample.name)

    custom_cases: Iterable[Tuple[str, str]] = [
        (
            "QuickSort Usuario",
            """Algoritmo QUICKSORT(A, p, r)
begin
    if (p < r) then
    begin
        q 🡨 CALL PARTITION(A, p, r)
        CALL QUICKSORT(A, p, q - 1)
        CALL QUICKSORT(A, q + 1, r)
    end
end

PARTITION(A, p, r)
begin
    x 🡨 A[r]
    i 🡨 p - 1
    for j 🡨 p to r - 1 do
    begin
        if (A[j] <= x) then
        begin
            i 🡨 i + 1
            CALL INTERCAMBIAR(A, i, j)
        end
    end
    CALL INTERCAMBIAR(A, i + 1, r)
    return i + 1
end

INTERCAMBIAR(A, i, j)
begin
    temp 🡨 A[i]
    A[i] 🡨 A[j]
    A[j] 🡨 temp
end""",
        ),
        (
            "Fibonacci DP",
            """Algoritmo FIBONACCI_DP(n)
begin
    memo 🡨 new Array(n + 1)
    for i 🡨 0 to n do
    begin
        memo[i] 🡨 -1
    end
    fib_n 🡨 CALL FIB(n, memo)
    return fib_n
end

Procedimiento FIB(n, memo)
begin
    if (n ≤ 1) then
    begin
        return n
    end
    if (memo[n] ≠ -1) then
    begin
        return memo[n]
    end
    result 🡨 CALL FIB(n-1, memo) + CALL FIB(n-2, memo)
    memo[n] 🡨 result
    return result
end""",
        ),
    ]

    _print_header("Validando casos personalizados")
    for name, code in custom_cases:
        success, message = _parse_snippet(name, code)
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {name}: {message}")

    if failures:
        _print_header("RESUMEN")
        print("Algunos algoritmos fallaron al parsearse:")
        for name in failures:
            print(f"  - {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

