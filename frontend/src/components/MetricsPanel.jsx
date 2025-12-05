import React, { useMemo } from 'react';
import { calculateTreeMetrics } from '../utils/treeMetrics.js';
import './MetricsPanel.css';

export default function MetricsPanel({ treeData, inputN, theoreticalComplexity }) {
  
  console.log("📊 MetricsPanel recibió:");
  console.log("  - treeData:", treeData);
  console.log("  - inputN:", inputN);
  console.log("  - theoreticalComplexity:", theoreticalComplexity);
  
  // 1. Calculamos las métricas reales usando el JSON
  const metrics = useMemo(() => {
    if (!treeData?.execution_tree) return null;
    return calculateTreeMetrics(treeData.execution_tree);
  }, [treeData]);

  if (!metrics) return null;

  // 2. Calcular complejidad esperada basada en la teórica (mejor, promedio, peor caso)
  const calculateExpectedCases = () => {
    console.log("🧮 calculateExpectedCases llamado:");
    console.log("  - theoreticalComplexity:", theoreticalComplexity);
    console.log("  - inputN:", inputN);
    
    if (!theoreticalComplexity || !inputN) {
      console.log("⚠️ Falta theoreticalComplexity o inputN, retornando null");
      return null;
    }
    
    const complexity = theoreticalComplexity.toLowerCase();
    
    // Fibonacci: O(2^n)
    if (complexity.includes("2^n") || complexity === "o(2^n)") {
      const expected = Math.pow(2, inputN);
      return {
        best: Math.round(expected * 0.8),
        average: expected,
        worst: Math.round(expected * 1.2)
      };
    } 
    // O(n^2)
    else if (complexity.includes("n^2") || complexity === "o(n^2)") {
      const expected = Math.pow(inputN, 2);
      return {
        best: expected,
        average: expected,
        worst: expected
      };
    } 
    // O(n log n)
    else if (complexity.includes("n log n") || complexity === "o(n log n)") {
      const expected = Math.round(inputN * Math.log2(inputN));
      return {
        best: expected,
        average: expected,
        worst: expected
      };
    } 
    // O(n)
    else if (complexity === "o(n)" || complexity.includes("lineal")) {
      return {
        best: inputN,
        average: inputN,
        worst: inputN
      };
    } 
    // O(1)
    else if (complexity === "o(1)" || complexity.includes("constante")) {
      return {
        best: 1,
        average: 1,
        worst: 1
      };
    }
    
    return null;
  };

  const expectedCases = calculateExpectedCases();
  const deviation = expectedCases 
    ? Math.abs(metrics.totalSteps - expectedCases.average) 
    : null;

  // Determinar clase de desviación (buena/warning/error)
  const getDeviationClass = () => {
    if (deviation === null) return '';
    if (deviation < 5) return 'good';
    if (deviation < 20) return 'warning';
    return 'error';
  };

  return (
    <div className="metrics-panel">
      
      {/* TARJETA 1: COSTO TEMPORAL */}
      <div className="metric-card temporal">
        <h4 className="metric-title">Costo Temporal Real</h4>
        <div className="metric-value temporal">
          {metrics.totalSteps}
          <span className="metric-unit">llamadas</span>
        </div>
        <p className="metric-description">
          Total de llamadas recursivas realizadas.
          {expectedCases && inputN && (
            <>
              <span className="metric-expected">
                Mejor caso: {expectedCases.best} | Promedio: {expectedCases.average} | Peor caso: {expectedCases.worst}
              </span>
              {deviation !== null && (
                <span className={`metric-deviation ${getDeviationClass()}`}>
                  Desviación del promedio: ±{deviation}
                  {metrics.totalSteps >= expectedCases.best && metrics.totalSteps <= expectedCases.worst && 
                    <span style={{ color: '#4ade80', marginLeft: '0.5rem' }}>✓ Dentro del rango</span>
                  }
                </span>
              )}
            </>
          )}
        </p>
      </div>

      {/* TARJETA 2: COSTO ESPACIAL */}
      <div className="metric-card spatial">
        <h4 className="metric-title">Costo Espacial (Stack)</h4>
        <div className="metric-value spatial">
          {metrics.maxDepth}
          <span className="metric-unit">niveles</span>
        </div>
        <p className="metric-description">
          Profundidad máxima del stack de llamadas.
        </p>
      </div>

    </div>
  );
}