import { useState, useMemo } from "react";
import RecursionTree from "./RecursionTree.jsx";
import MetricsPanel from "./MetricsPanel.jsx";
import ComplexityAnalysisPanel from "./ComplexityAnalysisPanel.jsx";
import "./SimulationModal.css";

// Función para detectar el tipo de algoritmo
const detectAlgorithmType = (pseudocode, analysisResult) => {
  if (!pseudocode) return 'secuencial';
  const code = pseudocode.toLowerCase();
  // 1. FUENTE DE VERDAD: Si el Backend ya nos lo dijo, créemosle.
  // (Asegúrate de que tu backend envíe este campo, ver solución 2)
  if (analysisResult?.algorithm_type) {
    return analysisResult.algorithm_type;
  }
  
  // ------------------------------------------------------
  // DETECCIONES ESPECÍFICAS (Alta Prioridad)
  // ------------------------------------------------------

  // 2. Programación Dinámica (Suele tener bucles, por eso va PRIMERO)
  // Buscamos patrones de tablas, memoización o asignaciones a arreglos dp
  if (/dp\[|memo|table\[|tabla\[|matriz\[.*\].*=|dynamic|dinamica/i.test(code)) {
    return 'programacion_dinamica';
  }

  // 3. Grafos (Suelen tener bucles y recursión)
  if (/graph|grafo|nodo|arista|edge|vertex|adyacen|bfs|dfs|dijkstra|visitado/i.test(code)) {
    return 'grafos';
  }

  // 4. Backtracking (Suele ser recursivo + bucle)
  // Buscamos palabras clave de poda o retroceso
  if (/backtrack|retroceso|podar|prune|prometedor|solucion.*parcial/i.test(code)) {
    return 'backtracking';
  }

  // 5. Divide y Vencerás (Suele ser recursivo)
  if (/divide|conquer|venceras|mitad|mid|pivote|partition|merge|mezcla|quicksort/i.test(code)) {
    return 'divide_y_venceras';
  }

  // ------------------------------------------------------
  // DETECCIONES ESTRUCTURALES (Media Prioridad)
  // ------------------------------------------------------

  // 6. Recursión
  // Mejoramos la regex para detectar llamadas a sí mismo sin depender de "function"
  // Intentamos extraer el nombre de la primera palabra seguida de paréntesis "Nombre("
  const functionNameMatch = pseudocode.match(/^\s*(?:function|procedimiento|funcion|algoritmo)?\s*([a-zA-Z0-9_]+)\s*\(/im);
  const functionName = functionNameMatch ? functionNameMatch[1] : null;

  if (functionName) {
    // Buscamos si ese nombre se usa dentro del cuerpo (CALL Nombre o simplemente Nombre() )
    // Excluimos la definición inicial
    const bodyWithoutHeader = pseudocode.replace(functionNameMatch[0], ""); 
    const recursionPattern = new RegExp(`\\b${functionName}\\s*\\(`, 'i');
    
    if (recursionPattern.test(bodyWithoutHeader)) {
      return 'recursivo';
    }
  }
  // Fallback: búsqueda simple de la palabra reservada
  if (/recurs|invocar a s[íi] mismo/i.test(code)) return 'recursivo';

  // ------------------------------------------------------
  // DETECCIONES GENÉRICAS (Baja Prioridad)
  // ------------------------------------------------------

  // 7. Iterativo (Solo si no fue nada de lo anterior)
  const hasLoops = /\b(for|para|while|mientras|repeat|repetir|hasta|do|hacer)\b/i.test(code);
  if (hasLoops) {
    return 'iterativo';
  }
  
  // 8. Por defecto
  return 'secuencial';
};

// Configuración de títulos y descripciones por tipo
const algorithmTypeConfig = {
  recursivo: {
    title: "Árbol de Recursión",
    treeLabel: "Árbol de Llamadas Recursivas",
    description: "Visualización jerárquica de las llamadas recursivas",
    icon: "🌳"
  },
  divide_y_venceras: {
    title: "Árbol de Divide y Vencerás",
    treeLabel: "Descomposición del Problema",
    description: "Visualización de cómo se divide y resuelve el problema",
    icon: "🔀"
  },
  iterativo: {
    title: "Flujo de Ejecución Iterativo",
    treeLabel: "Secuencia de Iteraciones",
    description: "Visualización del flujo de control en bucles",
    icon: "🔄"
  },
  grafos: {
    title: "Exploración del Grafo",
    treeLabel: "Árbol/Grafo de Exploración",
    description: "Visualización del recorrido por el grafo",
    icon: "🕸️"
  },
  programacion_dinamica: {
    title: "Tabla de Programación Dinámica",
    treeLabel: "Árbol de Subproblemas",
    description: "Visualización de subproblemas y memoización",
    icon: "📊"
  },
  backtracking: {
    title: "Árbol de Backtracking",
    treeLabel: "Árbol de Búsqueda con Retroceso",
    description: "Visualización de exploración y retroceso",
    icon: "↩️"
  },
  voraz: {
    title: "Decisiones Voraces",
    treeLabel: "Secuencia de Decisiones",
    description: "Visualización de elecciones localmente óptimas",
    icon: "⚡"
  },
  secuencial: {
    title: "Flujo de Ejecución",
    treeLabel: "Árbol de Ejecución",
    description: "Visualización de la secuencia de ejecución",
    icon: "📝"
  }
};

export function SimulationModal({ isOpen, onClose, pseudocode, onSimulate, analysisResult }) {
  const [inputs, setInputs] = useState("");
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Detectar tipo de algoritmo
  const algorithmType = useMemo(() => {
    // 1. PRIORIDAD MÁXIMA: Si ya simulamos y el Backend nos dijo qué tipo es
    if (treeData?.algorithm_type) {
    return treeData.algorithm_type;
    }
    // 2. FALLBACK: Si no hemos simulado aún, adivinamos con la función auxiliar
    return detectAlgorithmType(pseudocode, analysisResult);
        
   }, [pseudocode, analysisResult, treeData]); 

  // Obtener configuración del tipo
  const typeConfig = useMemo(() => {
    return algorithmTypeConfig[algorithmType] || algorithmTypeConfig.secuencial;
  }, [algorithmType]);

  // Extraer los 3 casos del análisis estático
  const staticAnalysisCases = useMemo(() => {
    console.log("🔍 ANÁLISIS ESTÁTICO - analysisResult completo:", analysisResult);
    console.log("📋 Estructura JSON completa:", JSON.stringify(analysisResult, null, 2));
    
    if (!analysisResult) {
      console.log("⚠️ analysisResult es null o undefined");
      return null;
    }
    
    // Verificar si tiene la estructura nueva (best_case, worst_case, average_case directamente)
    if (analysisResult.average_case || analysisResult.best_case || analysisResult.worst_case) {
      console.log("✅ Estructura NUEVA detectada (con best_case, worst_case, average_case)");
      console.log("  - best_case:", analysisResult.best_case);
      console.log("  - average_case:", analysisResult.average_case);
      console.log("  - worst_case:", analysisResult.worst_case);
      
      return {
        best: analysisResult.best_case,
        average: analysisResult.average_case,
        worst: analysisResult.worst_case,
        title: analysisResult.title,
        description: analysisResult.description
      };
    }
    
    // Verificar estructura vieja (steps.solution.complexity)
    if (analysisResult?.steps?.solution) {
      console.log("✅ Estructura VIEJA detectada (steps.solution)");
      const solution = analysisResult.steps.solution;
      
      return {
        best: solution.cases?.best || solution.complexity,
        average: solution.cases?.average || solution.complexity || solution.main_result,
        worst: solution.cases?.worst || solution.complexity,
        title: solution.title,
        description: solution.description
      };
    }
    
    console.log("⚠️ No se reconoció la estructura de analysisResult");
    return null;
  }, [analysisResult]);

  // Para compatibilidad con MetricsPanel (usa solo el caso promedio)
  const theoreticalComplexity = useMemo(() => {
    return staticAnalysisCases?.average || null;
  }, [staticAnalysisCases]);

  // Extraer el valor de 'n' de los inputs
  const inputN = useMemo(() => {
    try {
      const parsed = JSON.parse(inputs || "{}");
      return parsed.n || null;
    } catch {
      return null;
    }
  }, [inputs]);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    // Validar JSON
    if (inputs.trim()) {
      try {
        JSON.parse(inputs);
      } catch {
        setError("Formato de inputs inválido. Usa JSON válido, ej: {\"n\": 5}");
        return;
      }
    }

    setError(null);
    setLoading(true);
    
    try {
      const result = await onSimulate(inputs.trim() || "{}");
      setTreeData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setInputs("");
    setTreeData(null);
    setError(null);
    onClose();
  };

  return (
    <div className="simulation-modal-overlay" onClick={handleClose}>
      <div className="simulation-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="simulation-modal-header">
          <div>
            <small className="section-eyebrow">Simulación y Visualización · Tipo: {algorithmType.replace('_', ' ').toUpperCase()}</small>
            <h3>{typeConfig.icon} {typeConfig.title}</h3>
            <p className="text-muted" style={{ margin: '0.25rem 0 0', fontSize: '0.85rem' }}>
              {typeConfig.description}
            </p>
          </div>
          <button className="close-btn" onClick={handleClose}>
            &times;
          </button>
        </div>

        {/* Body con dos columnas */}
        <div className="simulation-modal-body-wrapper">
        <div className="simulation-modal-body">
          {/* Columna Izquierda: Algoritmo */}
          <div className="simulation-left-panel">
            <div className="panel-section">
              <h4>Pseudocódigo</h4>
              <pre className="code-display">{pseudocode}</pre>
            </div>

            <div className="panel-section">
              <label>Inputs (JSON):</label>
              <input
                type="text"
                className="input-field"
                value={inputs}
                onChange={(e) => setInputs(e.target.value)}
                placeholder='{"n": 5}'
              />
              <button
                className="btn btn-primary"
                onClick={handleGenerate}
                disabled={loading}
                style={{ width: "100%", marginTop: "0.5rem" }}
              >
                {loading ? "Generando..." : "Generar Árbol"}
              </button>
              {error && <p className="error-message">{error}</p>}
            </div>
          </div>

          {/* Columna Derecha: Árbol */}
          <div className="simulation-right-panel">
            <h4>{typeConfig.treeLabel}</h4>
            {(() => {
              console.log("🌳 Estado del árbol:");
              console.log("  - treeData existe:", !!treeData);
              console.log("  - treeData:", treeData);
              console.log("  - treeData.execution_tree:", treeData?.execution_tree);
              return null;
            })()}
            {treeData ? (
              <div className="tree-container">
                <RecursionTree treeData={treeData} />
              </div>
            ) : (
              <div className="empty-tree-state">
                {loading
                  ? `Generando ${typeConfig.treeLabel.toLowerCase()}...`
                  : `Ingresa los inputs y genera el árbol para visualizar la ejecución del algoritmo ${algorithmType}`}
              </div>
            )}
          </div>
        </div>

{/* Sección de Métricas y Comparación (parte inferior) */}
        {treeData && (
          <div className="metrics-section">
            <div className="metrics-header">
              <h4>Reporte de Ejecución y Análisis</h4>
              <p className="text-muted">Comparativa entre predicción estática, ejecución real y formalización matemática.</p>
            </div>
            
            <div className="metrics-comparison">
              
              {/* --- IZQUIERDA: Análisis Estático (Parser Clásico) --- */}
              <div className="analysis-card static-analysis">
                <div className="card-header">
                  <span className="badge badge-blue">Parser Estático</span>
                  <h5>Predicción Sintáctica</h5>
                </div>
                <div className="card-body">
                  {staticAnalysisCases ? (
                    <>
                      {/* Grid de 3 casos */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                        {/* Mejor Caso */}
                        <div style={{
                          padding: '0.75rem',
                          background: 'rgba(9, 10, 18, 0.5)',
                          borderRadius: '6px',
                          borderLeft: '3px solid #22c55e'
                        }}>
                          <div style={{ 
                            fontSize: '0.7rem', 
                            color: '#a1a1aa', 
                            textTransform: 'uppercase', 
                            fontWeight: 'bold',
                            marginBottom: '0.25rem'
                          }}>
                            Mejor (Ω)
                          </div>
                          <div style={{ 
                            fontSize: '1.1rem', 
                            fontWeight: 'bold', 
                            color: '#4ade80',
                            fontFamily: 'monospace'
                          }}>
                            {staticAnalysisCases.best || "-"}
                          </div>
                        </div>

                        {/* Promedio */}
                        <div style={{
                          padding: '0.75rem',
                          background: 'rgba(9, 10, 18, 0.5)',
                          borderRadius: '6px',
                          borderLeft: '3px solid #3b82f6'
                        }}>
                          <div style={{ 
                            fontSize: '0.7rem', 
                            color: '#a1a1aa', 
                            textTransform: 'uppercase', 
                            fontWeight: 'bold',
                            marginBottom: '0.25rem'
                          }}>
                            Promedio (Θ)
                          </div>
                          <div style={{ 
                            fontSize: '1.1rem', 
                            fontWeight: 'bold', 
                            color: '#60a5fa',
                            fontFamily: 'monospace'
                          }}>
                            {staticAnalysisCases.average || "-"}
                          </div>
                        </div>

                        {/* Peor Caso */}
                        <div style={{
                          padding: '0.75rem',
                          background: 'rgba(9, 10, 18, 0.5)',
                          borderRadius: '6px',
                          borderLeft: '3px solid #ef4444'
                        }}>
                          <div style={{ 
                            fontSize: '0.7rem', 
                            color: '#a1a1aa', 
                            textTransform: 'uppercase', 
                            fontWeight: 'bold',
                            marginBottom: '0.25rem'
                          }}>
                            Peor (O)
                          </div>
                          <div style={{ 
                            fontSize: '1.1rem', 
                            fontWeight: 'bold', 
                            color: '#f87171',
                            fontFamily: 'monospace'
                          }}>
                            {staticAnalysisCases.worst || "-"}
                          </div>
                        </div>
                      </div>

                      <p className="complexity-desc">
                        {staticAnalysisCases.description || "Complejidad estimada analizando la estructura del código (bucles anidados, recursión simple)."}
                        {inputN && (
                          <span style={{ display: 'block', marginTop: '0.5rem', color: '#a1a1aa' }}>
                            Para n={inputN}, se espera un comportamiento asintótico acorde a estas cotas.
                          </span>
                        )}
                      </p>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⚠️</div>
                      <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                        Sin análisis previo.
                      </p>
                      <p style={{ fontSize: '0.8rem', color: '#71717a' }}>
                        Ejecuta el botón "Analizar" primero para comparar.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* --- DERECHA: Análisis Profundo (Simulación + LLM Matemático) --- */}
              <div className="analysis-card dynamic-analysis">
                <div className="card-header">
                  <span className="badge badge-green">Motor IA + Runtime</span>
                  <h5>Simulación y Formalización</h5>
                </div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  
                  {/* 1. Las Métricas Reales (Conteo de pasos) */}
                  <MetricsPanel 
                    treeData={treeData} 
                    inputN={inputN}
                    theoreticalComplexity={theoreticalComplexity}
                  />

                  {/* 2. El Nuevo Análisis Matemático (Teorema Maestro, etc.) */}
                  <ComplexityAnalysisPanel 
                    analysisData={treeData.theoretical_analysis} 
                  />
                  
                </div>
              </div>

            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
