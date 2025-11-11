"""Coleccion de algoritmos de ejemplo que se usan para pruebas y la API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class SampleAlgorithm:
    name: str
    category: str
    description: str
    pseudocode: str
    expected_complexity: str


def load_samples() -> List[SampleAlgorithm]:
    """Devuelve al menos diez algoritmos representativos."""
    return [
        SampleAlgorithm(
            name="Busqueda Lineal",
            category="Iterativo",
            description="Recorre el arreglo completo para encontrar un elemento.",
            pseudocode="""begin
    i 🡨 1
    while (i <= n) do
    begin
        if (A[i] = objetivo) then
        begin
            return i
        end
        i 🡨 i + 1
    end
    return -1
end""",
            expected_complexity="O(n)",
        ),
        SampleAlgorithm(
            name="Suma de Prefijos",
            category="Iterativo",
            description="Calcula sumas parciales con un for simple.",
            pseudocode="""begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + A[i]
    end
end""",
            expected_complexity="O(n)",
        ),
        SampleAlgorithm(
            name="Producto de Matrices",
            category="Iterativo",
            description="Triple bucle clasico para multiplicar matrices cuadradas.",
            pseudocode="""begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            C[i, j] 🡨 0
            for k 🡨 1 to n do
            begin
                C[i, j] 🡨 C[i, j] + A[i, k] * B[k, j]
            end
        end
    end
end""",
            expected_complexity="O(n^3)",
        ),
        SampleAlgorithm(
            name="QuickSort Basico",
            category="Recursivo",
            description="Divide y venceras con particionamiento en dos subproblemas.",
            pseudocode="""begin
    if (low < high) then
    begin
        pivot 🡨 A[high]
        i 🡨 low - 1
        for j 🡨 low to high - 1 do
        begin
            if (A[j] <= pivot) then
            begin
                i 🡨 i + 1
                temp 🡨 A[i]
                A[i] 🡨 A[j]
                A[j] 🡨 temp
            end
        end
        temp 🡨 A[i + 1]
        A[i + 1] 🡨 A[high]
        A[high] 🡨 temp
        CALL self(A, low, i)
        CALL self(A, i + 2, high)
    end
end""",
            expected_complexity="O(n log n)",
        ),
        SampleAlgorithm(
            name="MergeSort",
            category="Recursivo",
            description="Divide el arreglo en mitades y las mezcla ordenadamente.",
            pseudocode="""begin
    if (length(A) <= 1) then
    begin
        return
    end
    mid 🡨 length(A) div 2
    CALL self(A[1..mid])
    CALL self(A[mid+1..length(A)])
    CALL merge(A, mid)
end""",
            expected_complexity="O(n log n)",
        ),
        SampleAlgorithm(
            name="Conteo de Inversiones",
            category="Divide y venceras",
            description="Cuenta inversiones con recursion y mezcla.",
            pseudocode="""begin
    if (length(A) <= 1) then
    begin
        return 0
    end
    mid 🡨 length(A) div 2
    izquierda 🡨 CALL self(A[1..mid])
    derecha 🡨 CALL self(A[mid+1..length(A)])
    cruces 🡨 CALL mergeCount(A, mid)
    return izquierda + derecha + cruces
end""",
            expected_complexity="O(n log n)",
        ),
        SampleAlgorithm(
            name="Busqueda Binaria",
            category="Recursivo/Iterativo",
            description="Divide el espacio de busqueda a la mitad cada vez.",
            pseudocode="""begin
    low 🡨 1
    high 🡨 n
    while (low <= high) do
    begin
        mid 🡨 (low + high) div 2
        if (A[mid] = objetivo) then
        begin
            return mid
        end
        else if (A[mid] < objetivo) then
        begin
            low 🡨 mid + 1
        end
        else
        begin
            high 🡨 mid - 1
        end
    end
    return -1
end""",
            expected_complexity="O(log n)",
        ),
        SampleAlgorithm(
            name="Fibonacci Recursivo",
            category="Recursivo",
            description="Definicion recursiva directa del n-esimo Fibonacci.",
            pseudocode="""begin
    if (n <= 1) then
    begin
        return n
    end
    else
    begin
        return CALL self(n - 1) + CALL self(n - 2)
    end
end""",
            expected_complexity="O(2^n)",
        ),
        SampleAlgorithm(
            name="Factorial",
            category="Recursivo",
            description="Calcula n! con recursion simple.",
            pseudocode="""begin
    if (n <= 1) then
    begin
        return 1
    end
    return n * CALL self(n - 1)
end""",
            expected_complexity="O(n)",
        ),
        SampleAlgorithm(
            name="Dijkstra Simplificado",
            category="Grafos",
            description="Explora un grafo usando cola de prioridad.",
            pseudocode="""begin
    inicializarDistancias()
    while (cola no esta vacia) do
    begin
        u 🡨 extraerMin(cola)
        for cada v en Adyacentes(u) do
        begin
            if (dist[u] + peso(u, v) < dist[v]) then
            begin
                dist[v] 🡨 dist[u] + peso(u, v)
                actualizar(cola, v)
            end
        end
    end
end""",
            expected_complexity="O((n + m) log n)",
        ),
        SampleAlgorithm(
            name="Multiplicacion de Strassen",
            category="Divide y venceras",
            description="Ejemplo de algoritmo avanzado para matrices.",
            pseudocode="""begin
    if (n = 1) then
    begin
        return A[1,1] * B[1,1]
    end
    dividirMatrices()
    CALL self(A11, B11)
    CALL self(A22, B22)
    CALL self(A11, B22)
    CALL self(A22, B11)
    combinarResultados()
end""",
            expected_complexity="O(n^log7)",
        ),
    ]
