import React, { useState } from "react";
import "./AnalysisModal.css"; 

export function AnalysisModal({ isOpen, onClose, result }) {
  const [currentStep, setCurrentStep] = useState(0);

  // Si no está abierto, retornamos null (no se renderiza nada)
  if (!isOpen || !result) return null;

  if (result.success === false || result.error) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content error-state" onClick={(e) => e.stopPropagation()}>
           <div className="modal-header">
              <h3>Error en el Análisis</h3>
              <button className="close-btn" onClick={onClose}>&times;</button>
           </div>
           <div className="modal-body">
             <p>Ocurrió un problema al procesar el algoritmo:</p>
             <pre className="error-pre">
               {result.error || "Error desconocido"}
             </pre>
           </div>
           <div className="modal-footer">
             <button className="btn btn-secondary" onClick={onClose}>Cerrar</button>
           </div>
        </div>
      </div>
    );
  }

  if (!result.steps) {
     return null; 
  }

  // Orden de pasos: incluir recursion_tree y dynamic_programming si existen
  const availableSteps = Object.keys(result.steps || {});
  const baseOrder = ["lexer", "parser", "line_costs", "extraction", "recursion_tree", "dynamic_programming", "solution"];
  const stepsOrder = baseOrder.filter(step => availableSteps.includes(step));
  const stepKey = stepsOrder[currentStep];
  const stepData = result.steps[stepKey];

  // Reiniciar el paso al cerrar (MOVER ANTES de usar)
  const handleClose = () => {
      setCurrentStep(0);
      onClose();
  }

  // Safety check: if stepData doesn't exist, skip to next step or show error
  if (!stepData) {
    return (
      <div className="modal-overlay" onClick={handleClose}>
        <div className="modal-content error-state" onClick={(e) => e.stopPropagation()}>
           <div className="modal-header">
              <h3>Paso no disponible</h3>
              <button className="close-btn" onClick={handleClose}>&times;</button>
           </div>
           <div className="modal-body">
             <p>El paso "{stepKey}" no está disponible en los resultados.</p>
           </div>
           <div className="modal-footer">
             <button className="btn btn-secondary" onClick={handleClose}>Cerrar</button>
           </div>
        </div>
      </div>
    );
  }

  // Funciones de navegación
  const handleNext = () => {
    if (currentStep < stepsOrder.length - 1) setCurrentStep((prev) => prev + 1);
  };
  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep((prev) => prev - 1);
  };
  
  // Renderizado del contenido dinámico
  const renderContent = () => {
    switch (stepKey) {
      case "lexer":
        return (
          <div className="token-container">
            {stepData.data?.map((token, i) => (
              <span key={i} className="token-badge">{token}</span>
            )) || "No hay tokens disponibles"}
          </div>
        );
      case "parser":
        return (
          <pre>
            {stepData.data}
          </pre>
        );
      
      case "line_costs":
        const lineCosts = stepData.line_costs || [];
        return (
          <div className="line-costs-table">
            <div className="line-costs-description">
              <p><strong>{stepData.description || "Análisis de costo por línea"}</strong></p>
            </div>
            {/* Cabecera de la tabla */}
            <div className="line-costs-header">
              <div className="line-costs-header-cell scope">Ámbito</div>
              <div className="line-costs-header-cell line-number">Línea</div>
              <div className="line-costs-header-cell code">Código</div>
              <div className="line-costs-header-cell cost">Costo</div>
              <div className="line-costs-header-cell explanation">Explicación</div>
              <div className="line-costs-header-cell source">Fuente</div>
            </div>

            {/* Filas de datos */}
            {lineCosts.length > 0 ? lineCosts.map((cost, idx) => (
              <div key={idx} className="line-costs-row">
                <div className="line-costs-cell scope">{cost.scope || "Algoritmo"}</div>
                <div className="line-costs-cell line-number">{cost.line_number || idx + 1}</div>
                <div className="line-costs-cell code">
                  <code>{cost.line_code || "\u00A0"}</code>
                </div>
                <div className="line-costs-cell cost">
                  <span className={`cost-badge ${
                    cost.cost?.includes('^') ? 'polynomial' : 
                    cost.cost?.includes('n') ? 'linear' : 
                    'constant'
                  }`}>
                    {cost.cost || "O(1)"}
                  </span>
                </div>
                <div className="line-costs-cell explanation">
                  <small>{cost.explanation || cost.source || ""}</small>
                </div>
                <div className="line-costs-cell source">
                  <small>{cost.source || "-"}</small>
                </div>
              </div>
            )) : <p className="no-data-message">No hay datos de líneas disponibles.</p>}
            
            {stepData.total_cost && (
              <div className="line-costs-total">
                <strong>Costo Total: {stepData.total_cost}</strong>
              </div>
            )}
          </div>
        );
      
      case "extraction":
        return (
          <div className="extraction-content">
            <h2 className="extraction-equation">{stepData.equation}</h2>
            <p className="extraction-explanation">{stepData.explanation}</p>
            {stepData.base_case && (
              <p className="extraction-base-case"><strong>Caso base:</strong> {stepData.base_case}</p>
            )}
            {stepData.source && (
              <p className="extraction-source"><small><strong>Fuente:</strong> {stepData.source}</small></p>
            )}
          </div>
        );
      
      case "recursion_tree":
        const treeLevels = stepData.levels || [];
        const treeStructure = stepData.structure;
        const renderTreeNode = (node) => {
          if (!node) return null;
          return (
            <div className="tree-node">
              <div className="tree-node-card">
                <span className="tree-node-label">{node.label}</span>
                <span className="tree-node-cost">{node.cost}</span>
              </div>
              {node.children && node.children.length > 0 && (
                <div className="tree-children">
                  {node.children.map((child, idx) => (
                    <div key={idx} className="tree-branch">
                      <span className="tree-connector-line" />
                      {renderTreeNode(child)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        };
        const treeHeight = stepData.max_level || 0;
        return (
          <div className="recursion-tree-content">
            <h3>{stepData.title || "Árbol de Recursión"}</h3>
            <p className="tree-description">{stepData.description || "Visualización del árbol de recursión"}</p>
            
            {/* Información del árbol */}
            {treeHeight > 0 && (
              <div className="tree-info-box">
                <div className="tree-info-item">
                  <strong>Altura del árbol:</strong> <span>{treeHeight} niveles</span>
                </div>
                <div className="tree-info-item">
                  <strong>Costo total:</strong> <span className="tree-cost-badge">{stepData.total_cost || "N/A"}</span>
                </div>
              </div>
            )}
            
            {treeStructure && treeStructure.label ? (
              <div className="tree-visualization">
                {renderTreeNode(treeStructure)}
              </div>
            ) : treeLevels.length > 0 ? (
              <>
                <div className="tree-levels-resume">
                  <h4 className="tree-levels-title">Desglose por Niveles</h4>
                  {treeLevels.map((level, idx) => (
                    <div key={idx} className="tree-level-card">
                      <div className="tree-level-header">
                        <strong className="tree-level-number">Nivel {level.level}</strong>
                        <span className="tree-level-cost-badge">Costo: {level.cost}</span>
                      </div>
                      <div className="tree-level-nodes">
                        {level.nodes.map((node, nodeIdx) => (
                          <span key={nodeIdx} className="tree-node-badge">{node}</span>
                        ))}
                      </div>
                      {level.total_cost && (
                        <div className="tree-level-total">
                          <small>Costo acumulado: {level.total_cost}</small>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="tree-total">
                  <strong>💰 Costo Total del Árbol: {stepData.total_cost || "N/A"}</strong>
                </div>
              </>
            ) : (
              <p className="no-recursion-message">Este algoritmo no es recursivo o no se pudo construir el árbol.</p>
            )}
          </div>
        );
      case "solution":
        const mathSteps = stepData.math_steps || [];
        const bestCase = stepData.cases?.best || stepData.lower_bound || "?";
        const averageCase = stepData.cases?.average || stepData.complexity || "?";
        const worstCase = stepData.cases?.worst || stepData.upper_bound || "?";
        return (
          <div className="solution-content">
            
            {/* --- SECCIÓN 1: TITULAR --- */}
            <div className="solution-header">
              <h4 className="solution-label">Complejidad Final</h4>
              <h1 className="solution-main-result">{stepData.complexity || stepData.main_result || "?"}</h1>
              
              <div className="solution-bounds">
                {stepData.upper_bound && (
                  <span className="solution-badge upper">O: {stepData.upper_bound}</span>
                )}
                {stepData.lower_bound && (
                  <span className="solution-badge lower">Ω: {stepData.lower_bound}</span>
                )}
                {stepData.complexity && (
                  <span className="solution-badge theta">Θ: {stepData.complexity}</span>
                )}
              </div>
              
              <p className="solution-desc">
                {stepData.description || stepData.details || "Sin descripción disponible"}
              </p>
              
              {stepData.equation_source && (
                <p className="solution-source">
                  <small><strong>Método:</strong> {stepData.equation_source}</small>
                </p>
              )}
            </div>
            
            {/* --- SECCIÓN: PASOS MATEMÁTICOS --- */}
            {mathSteps.length > 0 && (
              <div className="math-steps-section">
                <h4>Pasos del Cálculo</h4>
                <div className="math-steps-list">
                  {mathSteps.map((step, idx) => (
                    <div key={idx} className="math-step-item">
                      <div className="math-step-label">{step.label || `Paso ${idx + 1}`}</div>
                      <div className="math-step-value">{step.value || ""}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* --- SECCIÓN 2: TARJETAS DE CASOS (GRID) --- */}
            <div className="solution-cases-grid">
              {/* Mejor Caso */}
              <div className="case-card best">
                <span className="case-title">Mejor Caso (Ω)</span>
                <strong className="case-value">{bestCase}</strong>
              </div>

              {/* Caso Promedio (Destacado) */}
              <div className="case-card average active">
                <span className="case-title">Promedio (Θ)</span>
                <strong className="case-value">{averageCase}</strong>
              </div>

              {/* Peor Caso */}
              <div className="case-card worst">
                <span className="case-title">Peor Caso (O)</span>
                <strong className="case-value">{worstCase}</strong>
              </div>
            </div>

            {/* --- SECCIÓN 3: DESGLOSE MATEMÁTICO --- */}
            <div className="solution-math">
              <h4 className="math-title">🔍 Análisis Matemático</h4>
              
              <p className="solution-justification">
                <strong>Justificación: </strong> {stepData.justification}
              </p>

              <ul className="math-steps-list">
                {stepData.math_steps?.map((step, idx) => (
                  <li key={idx} className="math-step-item">
                    <span className="step-arrow">➜</span>
                    <span>
                      <strong className="step-label">{step.label}:</strong> {step.value}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        );
      
      case "dynamic_programming":
        const dpData = stepData;
        if (!dpData.is_dp) {
          return (
            <div className="dp-content">
              <p className="no-dp-message">{dpData.description}</p>
            </div>
          );
        }

        const tables = dpData.tables || {};

        const renderDPTable = (table) => {
          if (!table || !table.dimensions || table.dimensions.length === 0) {
            return null;
          }

          const dims = table.dimensions;
          const getKey = (coords) => `[${coords.join(", ")}]`;
          const getValue = (coords) => {
            if (!table.data) return "";
            return table.data[getKey(coords)] ?? "";
          };

          if (dims.length === 1) {
            const length = Math.min(dims[0], 12);
            return (
              <table className="dp-table">
                <thead>
                  <tr>
                    <th>Índice</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length }).map((_, i) => (
                    <tr key={i}>
                      <td>{i}</td>
                      <td>{getValue([i])}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            );
          }

          const rows = Math.min(dims[0], 10);
          const cols = Math.min(dims[1], 10);
          return (
            <table className="dp-table">
              <thead>
                <tr>
                  <th></th>
                  {Array.from({ length: cols }).map((_, j) => (
                    <th key={j}>j={j}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: rows }).map((_, i) => (
                  <tr key={i}>
                    <th>i={i}</th>
                    {Array.from({ length: cols }).map((_, j) => (
                      <td key={j}>{getValue([i, j])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          );
        };

        return (
          <div className="dp-content">
            <h3>{dpData.title}</h3>
            <div className="dp-info">
              <p className="dp-description">{dpData.description}</p>
              <div className="dp-metadata">
                <div className="dp-metadata-item">
                  <strong>Enfoque:</strong> {dpData.approach === "top_down" ? "Top-Down (Memoization)" : "Bottom-Up"}
                </div>
                <div className="dp-metadata-item">
                  <strong>Modelo:</strong> {dpData.model_type}
                </div>
                <div className="dp-metadata-item">
                  <strong>Complejidad Espacial:</strong> {dpData.space_complexity}
                </div>
              </div>
            </div>

            {dpData.explanation && (
              <div className="dp-explanation">
                <h4>Explicación del Enfoque</h4>
                <pre className="dp-explanation-text">{dpData.explanation}</pre>
              </div>
            )}

            {/* Tabla de Óptimos */}
            {tables.optimos && (
              <div className="dp-table-section">
                <h4>📊 {tables.optimos.name}</h4>
                <p className="table-description">{tables.optimos.description}</p>
                <div className="table-info">
                  <span><strong>Dimensiones:</strong> {tables.optimos.dimensions?.join(" × ") || "N/A"}</span>
                  <span><strong>Enfoque:</strong> {tables.optimos.approach || dpData.approach}</span>
                  {tables.optimos.initialization && (
                    <span><strong>Inicialización:</strong> {tables.optimos.initialization}</span>
                  )}
                </div>
                <div className="table-preview">
                  {renderDPTable(tables.optimos)}
                </div>
              </div>
            )}

            {/* Tabla de Caminos */}
            {tables.caminos && (
              <div className="dp-table-section">
                <h4>🛤️ {tables.caminos.name}</h4>
                <p className="table-description">{tables.caminos.description}</p>
                <div className="table-info">
                  <span><strong>Dimensiones:</strong> {tables.caminos.dimensions?.join(" × ") || "N/A"}</span>
                </div>
                <div className="table-preview">
                  {renderDPTable(tables.caminos)}
                </div>
              </div>
            )}

            {/* Vector SOA */}
            {tables.soa && (
              <div className="dp-table-section">
                <h4>📦 {tables.soa.name}</h4>
                <p className="table-description">{tables.soa.description}</p>
                <div className="table-preview">
                  {Array.isArray(tables.soa.data) ? (
                    <ul className="soa-list">
                      {tables.soa.data.length === 0 && <li>Vector vacío (se llena en la reconstrucción)</li>}
                      {tables.soa.data.map((value, idx) => (
                        <li key={idx}>
                          <strong>Posición {idx}:</strong> {JSON.stringify(value)}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    renderDPTable({ ...tables.soa, dimensions: [tables.soa.data?.length || 0] })
                  )}
                </div>
              </div>
            )}

            {/* Pasos de Reconstrucción */}
            {dpData.reconstruction_steps && dpData.reconstruction_steps.length > 0 && (
              <div className="dp-reconstruction">
                <h4>🔧 Pasos de Reconstrucción de la Solución</h4>
                <ol className="reconstruction-steps-list">
                  {dpData.reconstruction_steps.map((step, idx) => (
                    <li key={idx} className="reconstruction-step">{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        );
      
      default: return null;
    }
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* CABECERA */}
        <div className="modal-header">
          <div>
            <small>Paso {currentStep + 1} / {stepsOrder.length}</small>
            <h3>{stepData.title}</h3>
          </div>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>

        {/* CUERPO */}
        <div className="modal-body">
            <p>{stepData.description}</p>
            {renderContent()}
        </div>

        {/* PIE DE PAGINA (BOTONES) */}
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={handlePrev} 
            disabled={currentStep === 0}
            style={{ opacity: currentStep === 0 ? 0.5 : 1 }}
          >
            Anterior
          </button>
          
          <div className="step-indicators">
            {stepsOrder.map((_, idx) => (
              <div key={idx} className={`dot ${idx === currentStep ? "active" : ""}`} />
            ))}
          </div>

          <button 
            className="btn btn-primary" 
            onClick={currentStep === stepsOrder.length - 1 ? handleClose : handleNext}
          >
            {currentStep === stepsOrder.length - 1 ? "Finalizar" : "Siguiente"}
          </button>
        </div>
      </div>
    </div>
  );
}