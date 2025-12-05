import { useState, useMemo, useEffect } from "react";
import RecursionTree from "./RecursionTree.jsx";
import MetricsPanel from "./MetricsPanel.jsx";
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

const inputGuides = [
  {
    match: /factorial/i,
    hint: "n entero >= 0. Ej: {\"n\": 5}",
    placeholder: '{"n": 5}'
  },
  {
    match: /fibonacci/i,
    hint: "n entero >= 0. Ej: {\"n\": 6}",
    placeholder: '{"n": 6}'
  },
  {
    match: /hanoi/i,
    hint: "n discos y nombres de postes. Ej: {\"n\": 3, \"origen\": \"A\", \"auxiliar\": \"B\", \"destino\": \"C\"}",
    placeholder: '{"n": 3, "origen": "A", "auxiliar": "B", "destino": "C"}'
  },
  {
    match: /burbuja|merge|quick|ordenamiento|sort/i,
    hint: "Arreglo y tamaño n. Ej: {\"arr\": [5,3,1,4], \"n\": 4}",
    placeholder: '{"arr": [5,3,1,4], "n": 4}'
  },
  {
    match: /busqueda.*sec|secuencial/i,
    hint: "Arreglo, tamaño n y valor x. Ej: {\"arr\": [7,2,9], \"n\": 3, \"x\": 2}",
    placeholder: '{"arr": [7,2,9], "n": 3, "x": 2}'
  },
  {
    match: /busqueda.*bin/i,
    hint: "Arreglo ORDENADO, tamaño n y valor x. Ej: {\"arr\": [1,3,5,7], \"n\": 4, \"x\": 5}",
    placeholder: '{"arr": [1,3,5,7], "n": 4, "x": 5}'
  },
  {
    match: /suma.*gauss/i,
    hint: "n entero > 0. Ej: {\"n\": 10}",
    placeholder: '{"n": 10}'
  },
  {
    match: /suma.*arreglo|sumar.*elementos/i,
    hint: "Arreglo y tamaño n. Ej: {\"arr\": [2,4,6], \"n\": 3}",
    placeholder: '{"arr": [2,4,6], "n": 3}'
  }
];

function resolveInputGuide(pseudocode) {
  if (!pseudocode) return { hint: "Define tus parámetros en JSON.", placeholder: '{"n": 5}' };
  const guide = inputGuides.find((g) => g.match.test(pseudocode));
  return (
    guide || {
      hint: "Define los parámetros en JSON. Ej: {\"n\": 5}",
      placeholder: '{"n": 5}'
    }
  );
}

function inferInputFields(pseudocode) {
  const text = pseudocode || "";
  // Capturar todas las firmas con begin y elegir la ÚLTIMA (orquestadora)
  const sigRegex = /([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*[\r\n]+\s*begin/gi;
  const signatures = [];
  let m;
  while ((m = sigRegex.exec(text)) !== null) {
    const rawParams = m[2]
      .split(/[,;]/)
      .map((p) => p.trim())
      .filter(Boolean);
    signatures.push({ params: rawParams, index: m.index });
  }

  let params = [];
  if (signatures.length) {
    params = signatures[signatures.length - 1].params;
  } else {
    const firstSig = /([A-Za-z0-9_]+)\s*\(([^)]*)\)/i.exec(text);
    if (firstSig) {
      params = firstSig[2]
        .split(/[,;]/)
        .map((p) => p.trim())
        .filter(Boolean);
    }
  }

  const defaultByName = (name) => {
    const lower = name.toLowerCase();
    if (/(arr|vector|lista|array|a\[|\ba\b)/.test(lower)) return "[10,5,20,3,8]";
    if (/n/.test(lower)) return "5";
    if (/x|valor|key/.test(lower)) return "3";
    if (/origen|from/.test(lower)) return "\"A\"";
    if (/destino|to/.test(lower)) return "\"C\"";
    if (/auxiliar|aux/.test(lower)) return "\"B\"";
    if (/matriz|matrix|tabla|dp/.test(lower)) return "[[1,2],[3,4]]";
    return "1";
  };

  const fields = [];
  const add = (name, label, placeholder) => {
    if (!fields.some((f) => f.name === name)) {
      fields.push({ name, label, placeholder });
    }
  };
  const code = (pseudocode || "").toLowerCase();

  if (params.length) {
    params.forEach((p) => {
      const clean = p.replace(/\[.*?\]/g, "").trim();
      add(clean, clean, defaultByName(clean));
    });
  } else {
    add("n", "n (tamaño/iteraciones)", "5");
    // Solo heurísticas si no hay firma detectada
    if (/arreglo|array|vector|lista|arr\[/i.test(code)) {
      add("arr", "arreglo", "[10,5,20,3,8]");
    }
    if (/busqueda|buscar|valor|x\b/i.test(code)) {
      add("x", "valor a buscar", "3");
    }
    if (/origen/.test(code)) add("origen", "origen", "\"A\"");
    if (/auxiliar/.test(code)) add("auxiliar", "auxiliar", "\"B\"");
    if (/destino/.test(code)) add("destino", "destino", "\"C\"");
    if (/matriz|matrix|tabla|dp/.test(code)) {
      add("matriz", "matriz/tabla", "[[1,2],[3,4]]");
    }
  }

  return fields.length ? fields : [{ name: "n", label: "n", placeholder: "5" }];
}

function parsePlaceholderValue(placeholder) {
  try {
    return JSON.parse(placeholder);
  } catch {
    return placeholder.replace(/^"|"$/g, "");
  }
}

function parseUserValue(raw) {
  if (raw === undefined || raw === null) return raw;
  const val = String(raw).trim();
  if (val === "") return "";
  // JSON object/array literal
  if ((val.startsWith("{") && val.endsWith("}")) || (val.startsWith("[") && val.endsWith("]"))) {
    try {
      return JSON.parse(val);
    } catch {
      // fall through
    }
  }
  // comma separated numbers without brackets -> wrap as array
  if (!val.startsWith("[") && val.includes(",") && /^[0-9,\s.-]+$/.test(val)) {
    try {
      return JSON.parse(`[${val}]`);
    } catch {
      // fall through
    }
  }
  // boolean/null
  if (/^(true|false|null)$/i.test(val)) {
    return JSON.parse(val.toLowerCase());
  }
  // number
  if (!isNaN(Number(val))) {
    return Number(val);
  }
  // default: string
  return val;
}

function buildJsonString(obj) {
  return JSON.stringify(obj, null, 2);
}

export function SimulationModal({ isOpen, onClose, pseudocode, onSimulate, analysisResult }) {
  const [inputs, setInputs] = useState("");
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [structuredInputs, setStructuredInputs] = useState({});

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

  const inputGuide = useMemo(() => resolveInputGuide(pseudocode), [pseudocode]);

  const suggestedFields = useMemo(() => inferInputFields(pseudocode), [pseudocode]);

  const exampleJson = useMemo(() => {
    const exampleObj = {};
    suggestedFields.forEach((f) => {
      exampleObj[f.name] = parsePlaceholderValue(f.placeholder);
    });
    return buildJsonString(exampleObj);
  }, [suggestedFields]);

  useEffect(() => {
    const init = {};
    suggestedFields.forEach((f) => {
      const parsed = parsePlaceholderValue(f.placeholder);
      init[f.name] = typeof parsed === "object" ? JSON.stringify(parsed) : String(parsed);
    });
    setStructuredInputs(init);
    setInputs(exampleJson);
  }, [pseudocode, suggestedFields, exampleJson]);

  const isRecursiveLike = useMemo(
    () =>
      ["recursivo", "divide_y_venceras", "backtracking", "programacion_dinamica"].includes(
        algorithmType
      ),
    [algorithmType]
  );

  const shouldShowTree = Boolean(treeData?.execution_tree) && isRecursiveLike;

  const stepTrace = useMemo(() => {
    if (!treeData) return null;
    return treeData.steps || treeData.trace || treeData.logs || null;
  }, [treeData]);

  const autoTrace = useMemo(() => {
    if (stepTrace) return stepTrace;
    const t = treeData?.execution_tree;
    if (!t) return null;
    const acc = [];
    const walk = (node, depth = 0) => {
      if (!node) return;
      const indent = depth ? "·".repeat(depth) + " " : "";
      const label = `${indent}${node.call || "call"} -> ${node.result ?? ""}`.trim();
      acc.push(label);
      if (Array.isArray(node.children)) {
        node.children.forEach((c) => walk(c, depth + 1));
      }
    };
    walk(t, 0);
    return acc.length ? acc : null;
  }, [stepTrace, treeData]);

  const renderTraceItem = (item, idx) => {
    const isObj = item && typeof item === "object" && !Array.isArray(item);
    const line = isObj ? item.line || item.line_number : null;
    const action = isObj ? item.action || item.detail || item.comparison : item;
    const vars = isObj ? item.vars || item.variables || item.state : null;

    return (
      <div key={idx} className="trace-item-card">
        <div className="trace-item-header">
          <span className="badge badge-green">Paso {idx + 1}</span>
          {line !== undefined && <span className="trace-line">Línea: {line}</span>}
        </div>
        <div className="trace-action">{typeof action === "string" ? action : JSON.stringify(action)}</div>
        {vars && typeof vars === "object" && (
          <div className="trace-vars">
            {Object.entries(vars).map(([k, v]) => (
              <div key={k} className="trace-var">
                <strong>{k}</strong>
                <span>{typeof v === "string" ? v : JSON.stringify(v)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Extraer la complejidad teórica del análisis estático
  const theoreticalComplexity = useMemo(() => {
    console.log("🔍 analysisResult completo:", analysisResult);
    if (!analysisResult?.steps?.solution?.complexity) {
      console.log("⚠️ No se encontró complejidad en analysisResult.steps.solution.complexity");
      return null;
    }
    console.log("✅ Complejidad encontrada:", analysisResult.steps.solution.complexity);
    return analysisResult.steps.solution.complexity;
  }, [analysisResult]);

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
            <small className="section-eyebrow">
              Simulación · Tipo: {algorithmType.replace('_', ' ').toUpperCase()}
            </small>
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
                <p className="text-muted" style={{ fontSize: "0.9rem", marginBottom: "0.35rem" }}>
                  {inputGuide.hint}
                </p>

                <div className="inputs-grid">
                  {suggestedFields.map((field) => (
                    <div key={field.name} className="input-field-group">
                      <small>{field.label}</small>
                      <input
                        type="text"
                        className="input-field"
                        value={structuredInputs[field.name] ?? ""}
                        onChange={(e) =>
                          setStructuredInputs((prev) => {
                            const next = { ...prev, [field.name]: e.target.value };
                            setInputs(buildJsonString(Object.fromEntries(
                              Object.entries(next).map(([k,v]) => [k, parseUserValue(v)])
                            )));
                            return next;
                          })
                        }
                        placeholder={field.placeholder}
                      />
                    </div>
                  ))}
                </div>

                <div className="input-actions">
                  <button
                    className="btn btn-ghost"
                    onClick={() => setInputs(exampleJson)}
                    type="button"
                  >
                    Usar ejemplo sugerido
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      const parsed = Object.fromEntries(
                        Object.entries(structuredInputs).map(([k, v]) => [k, parseUserValue(v)])
                      );
                      setInputs(buildJsonString(parsed));
                    }}
                    type="button"
                  >
                    Actualizar JSON
                  </button>
                </div>

                <textarea
                  className="input-field"
                  style={{ marginTop: "0.5rem", minHeight: "90px", fontFamily: "monospace" }}
                  value={inputs}
                  onChange={(e) => setInputs(e.target.value)}
                  placeholder={inputGuide.placeholder}
                />

                <button
                  className="btn btn-primary"
                  onClick={handleGenerate}
                  disabled={loading}
                  style={{ width: "100%", marginTop: "0.5rem" }}
                >
                  {loading
                    ? "Generando..."
                    : isRecursiveLike
                    ? "Generar árbol y seguimiento"
                    : "Generar seguimiento"}
                </button>
                {error && <p className="error-message">{error}</p>}
              </div>
            </div>

            {/* Columna Derecha: Árbol o aviso */}
            <div className="simulation-right-panel">
              <h4>{shouldShowTree ? typeConfig.treeLabel : "Seguimiento de ejecución"}</h4>
              {treeData ? (
                shouldShowTree ? (
                  <div className="tree-container">
                    <RecursionTree treeData={treeData} />
                  </div>
                ) : (
                  <div className="empty-tree-state" style={{ borderStyle: "solid" }}>
                    Este algoritmo no es recursivo; revisa la traza paso a paso inferior.
                  </div>
                )
              ) : (
                <div className="empty-tree-state">
                  {loading
                    ? "Generando visualización..."
                    : isRecursiveLike
                    ? `Ingresa los inputs y genera el árbol + seguimiento para visualizar la ejecución recursiva`
                    : `Ingresa los inputs y genera el seguimiento para visualizar la ejecución del algoritmo`}
                </div>
              )}
            </div>
          </div>

        {/* Sección de Métricas y Comparación (parte inferior) */}
        {treeData && (
          <div className="metrics-section">
            <div className="metrics-header">
              <h4>Análisis de Complejidad</h4>
              <p className="text-muted">Comparación entre análisis estático y dinámico</p>
            </div>
            
            <div className="metrics-comparison">
              {/* Análisis Estático */}
              <div className="analysis-card static-analysis">
                <div className="card-header">
                  <span className="badge badge-blue">Análisis Estático</span>
                  <h5>Complejidad Teórica</h5>
                </div>
                <div className="card-body">
                  {theoreticalComplexity ? (
                    <>
                      <div className="complexity-value">{theoreticalComplexity}</div>
                      <p className="complexity-desc">
                        Calculada mediante análisis sintáctico del pseudocódigo.
                        {inputN && (
                          <span style={{ display: 'block', marginTop: '0.5rem', color: '#a1a1aa' }}>
                            Para n={inputN}, se espera un comportamiento según esta complejidad.
                          </span>
                        )}
                      </p>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
                      <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
                      <p className="text-muted" style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                        No hay análisis estático disponible
                      </p>
                      <p style={{ fontSize: '0.85rem', color: '#71717a', lineHeight: '1.6' }}>
                        Para obtener una comparación completa:
                        <br/>
                        1. Cierra este modal
                        <br/>
                        2. Haz clic en el botón <strong style={{color: '#60a5fa'}}>"Analizar"</strong> en la pantalla principal
                        <br/>
                        3. Luego regresa a <strong style={{color: '#4ade80'}}>"Simular"</strong>
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Análisis Dinámico */}
              <div className="analysis-card dynamic-analysis">
                <div className="card-header">
                  <span className="badge badge-green">Análisis Dinámico</span>
                  <h5>Métricas Reales</h5>
                </div>
                <div className="card-body">
                  <MetricsPanel 
                    treeData={treeData} 
                    inputN={inputN}
                    theoreticalComplexity={theoreticalComplexity}
                  />
                </div>
              </div>
            </div>
            {autoTrace && Array.isArray(autoTrace) && (
              <div className="panel-section" style={{ marginTop: "1rem" }}>
                <h4>Traza paso a paso</h4>
                <div className="trace-list">
                  {autoTrace.map((item, idx) => renderTraceItem(item, idx))}
                </div>
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
