export const mockAnalysisResult = {
  success: true,
  steps: {
    lexer: {
      title: "Análisis Léxico",
      description: "Convertimos el código crudo en una secuencia de tokens.",
      data: ["KEYWORD: begin", "KEYWORD: if", "SYMBOL: (", "ID: low", "SYMBOL: <", "ID: high", "SYMBOL: )", "KEYWORD: then", "KEYWORD: begin", "ID: pivot", "SYMBOL: <-", "ID: A"]
    },
    parser: {
      title: "Análisis Sintáctico (AST)",
      description: "Estructuramos los tokens en un Árbol de Sintaxis Abstracta.",
      data: `Program
  ├── IfStatement (low < high)
  │   ├── PartitionLoop (Cost: n)
  │   │   └── SwapLogic
  │   ├── RecursiveCall (self, low, i)
  │   └── RecursiveCall (self, i+2, high)`
    },
    extraction: {
      title: "Modelado Matemático",
      description: "Traducimos el AST a una ecuación de recurrencia.",
      equation: "T(n) = 2T(n/2) + n",
      explanation: "Identificamos 2 llamadas recursivas sobre la mitad del input (n/2) y un costo lineal (n) por el particionado."
    },
    solution: {
      title: "Resolución (Teorema Maestro)",
      description: "Aplicamos el Teorema Maestro para hallar la cota asintótica.",
      complexity: "Θ(n log n)",
      // AQUÍ ESTÁ LO NUEVO: EL PASO A PASO MATEMÁTICO
      math_steps: [
        { label: "1. Identificar coeficientes", value: "a = 2, b = 2, f(n) = n" },
        { label: "2. Calcular exponente crítico", value: "log_b(a) = log_2(2) = 1" },
        { label: "3. Comparar con f(n)", value: "n^1 vs f(n) = n^1" },
        { label: "4. Conclusión", value: "Como son iguales, aplica el Caso 2: Θ(n^1 * log n)" }
      ]
    }
  }
};