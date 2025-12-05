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
            name="Algoritmo de ordenamiento por inserción",
            category="Iterativo",
            description="Busca la ubicación correcta del segundo elemento con respecto a los elementos que los preceden",
            pseudocode="""Insertar(temporal[n], valor, tam)
begin
    if (tam = 0) then
    begin
        temporal[0] ← valor
    end
    else
    begin
        x ← 0
        while (temporal[x] < valor and x < tam) do
        begin
            x ← x + 1
        end

        ► IMPORTANTE: El algoritmo original hace un for decremental (y--).
        ► usamos WHILE para simular el retroceso.
        y ← tam
        while (y > x) do
        begin
            temporal[y] ← temporal[y - 1]
            y ← y - 1
        end

        temporal[x] ← valor
    end
end

ordenar3(arreglo[n], n)
begin

    temporal[n] 🡨 0

    for x 🡨 0 to n - 1 do
    begin
        CALL Insertar(temporal, arreglo[x], x)
    end

    for x 🡨 0 to n - 1 do
    begin
        arreglo[x] ← temporal[x]
    end
end""",
            expected_complexity="O(n^2)",
        ),
        SampleAlgorithm(
            name="Torres de Hanoi", 
            category="Recursivo",
            description="Mueve discos entre tres postes siguiendo reglas específicas.",
            pseudocode="""TorresHanoi(n, origen, auxiliar, destino)
begin
    if (n = 1) then
    begin
        CALL Imprimir("Mover disco de " + origen + " a " + destino)
    end
    else
    begin
        CALL TorresHanoi(n - 1, origen, destino, auxiliar)
        CALL Imprimir("Mover disco " + n + " de " + origen + " a " + destino)
        CALL TorresHanoi(n - 1, auxiliar, origen, destino)
    end
end""",
            expected_complexity="O(2^n)",
        ),
        SampleAlgorithm(
            name="QuickSort",
            category="Recursivo",
            description="Divide y conquistarás con particionamiento en dos subproblemas.",
            pseudocode="""
    QuickSort(A[n], p, r)
    begin
        if (p < r) then
        begin
            q 🡨 CALL Particion(A, p, r)
            
            izq 🡨 q - 1
            CALL QuickSort(A, p, izq)
            
            der 🡨 q + 1
            CALL QuickSort(A, der, r)
        end
    end
    
    Particion(A[n], p, r)
    begin
        pivote 🡨 A[p]
        i 🡨 p
        j 🡨 r
        
        while (i < j) do
        begin
            while (A[i] <= pivote and i <= r) do
            begin
                i 🡨 i + 1
            end
            
            while (A[j] > pivote and j >= p) do
            begin
                j 🡨 j - 1
            end
            
            if (i < j) then
            begin
                temp 🡨 A[i]
                A[i] 🡨 A[j]
                A[j] 🡨 temp
            end
        end
        
        temp 🡨 A[p]
        A[p] 🡨 A[j]
        A[j] 🡨 temp
        
        return j
    end""",
            expected_complexity="O(n^2)",
        ),

        SampleAlgorithm(
            name="Busqueda Binaria",
            category="Recursivo/Iterativo",
            description="Divide el espacio de busqueda a la mitad cada vez.",
            pseudocode="""busquedaBinaria(A[n], valor)      
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
""",
            expected_complexity="O(log n)",
        ),
        SampleAlgorithm(
            name="Fibonacci",
            category="Recursivo",
            description="Definicion recursiva directa del n-esimo Fibonacci.",
            pseudocode="""Fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    else
    begin
        temp1 🡨 n - 1
        val1 🡨 0
        CALL Fibonacci(temp1)
        
        temp2 🡨 n - 2
        val2 🡨 0
        CALL Fibonacci(temp2)
        
        resultado 🡨 val1 + val2
        return resultado
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
        )
    ]
