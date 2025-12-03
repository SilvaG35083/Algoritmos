// src/components/MetricsPanel.jsx
import React, { useMemo } from 'react';
import { calculateTreeMetrics } from '../utils/treeMetrics';

export default function MetricsPanel({ treeData, inputN, theoreticalComplexity }) {
  
  // 1. Calculamos las métricas reales usando el JSON
  const metrics = useMemo(() => {
    if (!treeData?.execution_tree) return null;
    return calculateTreeMetrics(treeData.execution_tree);
  }, [treeData]);

  if (!metrics) return null;

  // 2. Lógica de Comparación (Opcional: Si tienes la complejidad teórica)
  // Ejemplo: Si el backend dice "O(2^n)" y n=3, esperamos 2^3 = 8 pasos aprox.
  const expectedSteps = theoreticalComplexity === "2^n" ? Math.pow(2, inputN) : "N/A";

  return (
    <div className="grid grid-cols-2 gap-4 mt-6 p-4 bg-gray-900 rounded-lg border border-gray-700 text-white">
      
      {/* TARJETA 1: COSTO TEMPORAL */}
      <div className="p-4 bg-gray-800 rounded border-l-4 border-blue-500">
        <h4 className="text-gray-400 text-sm uppercase font-bold">Costo Temporal Real</h4>
        <div className="text-3xl font-bold mt-1">{metrics.totalSteps} <span className="text-sm font-normal text-gray-400">ops</span></div>
        <p className="text-xs text-gray-500 mt-2">
          Total de llamadas recursivas realizadas.
          {/* Aquí podrías mostrar la comparación */}
           <br/>(Predicción Teórica para n={inputN}: {expectedSteps})
        </p>
      </div>

      {/* TARJETA 2: COSTO ESPACIAL */}
      <div className="p-4 bg-gray-800 rounded border-l-4 border-green-500">
        <h4 className="text-gray-400 text-sm uppercase font-bold">Costo Espacial (Stack)</h4>
        <div className="text-3xl font-bold mt-1">{metrics.maxDepth} <span className="text-sm font-normal text-gray-400">niveles</span></div>
        <p className="text-xs text-gray-500 mt-2">
          Profundidad máxima alcanzada en memoria.
        </p>
      </div>

    </div>
  );
}