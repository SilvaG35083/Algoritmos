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

  const baseSteps = ["lexer", "parser", "line_costs", "extraction", "solution"];
  const dynamicData = result.steps.dynamic_programming;
  // Mostrar PD siempre que el backend envíe la sección, sea caso genérico o especializado (Fibonacci)
  const shouldShowDP = Boolean(dynamicData);
  const stepsOrder = shouldShowDP ? [...baseSteps, "dynamic_programming"] : baseSteps;
  const stepKey = stepsOrder[currentStep];
  const stepData = result.steps[stepKey];
  const displayTitle =
    stepData?.title ||
    (stepKey === "dynamic_programming" ? "Programación Dinámica" : "");
  const displayDescription =
    stepData?.description ||
    (stepKey === "dynamic_programming"
      ? "Modelo recursivo, Tablas de Óptimos/Caminos y Vector SOA."
      : "");

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
        return (
          <div className="line-costs-table">
            {/* Cabecera de la tabla */}
            <div className="line-costs-header">
              <div className="line-costs-header-cell line-number">Nº</div>
              <div className="line-costs-header-cell code">Código</div>
              <div className="line-costs-header-cell cost">Costo</div>
            </div>

            {/* Filas de datos */}
            {stepData.rows?.map((row, idx) => (
              <div key={idx} className="line-costs-row">
                <div className="line-costs-cell line-number">{row.line}</div>
                <div className="line-costs-cell code">{row.code || "\u00A0"}</div>
                <div className="line-costs-cell cost">
                  <span className={`cost-badge ${
                    row.cost.includes('^') ? 'polynomial' : 
                    row.cost.includes('n') ? 'linear' : 
                    'constant'
                  }`}>
                    {row.cost}
                  </span>
                </div>
              </div>
            )) || <p className="no-data-message">No hay datos de líneas disponibles.</p>}
          </div>
        );
      
      case "extraction":
        return (
          <div className="extraction-content">
            <h2 className="extraction-equation">{stepData.equation}</h2>
            <p className="extraction-explanation">{stepData.explanation}</p>
          </div>
        );
      case "solution":
        return (
          <div className="solution-content">
            
            {/* --- SECCIÓN 1: TITULAR --- */}
            <div className="solution-header">
              <h4 className="solution-label">Clase de Complejidad</h4>
              <h1 className="solution-main-result">{stepData.main_result || "?"}</h1>
              
              <span className="solution-badge">
                {stepData.complexity_class || "Desconocida"}
              </span>
              
              <p className="solution-desc">
                "{stepData.complexity_desc || "Sin descripción disponible"}"
              </p>

              <div className="solution-method">
                <strong>Método usado:</strong> {stepData.method_used || "Heurística estructural"}
              </div>
              {stepData.expected && (
                <div className="solution-expected">
                  <p><strong>Referencias esperadas:</strong> {stepData.expected.description}</p>
                  <ul>
                    <li>Mejor caso: {stepData.expected.best}</li>
                    <li>Caso promedio: {stepData.expected.average}</li>
                    <li>Peor caso: {stepData.expected.worst}</li>
                  </ul>
                </div>
              )}
            </div>

            {/* --- SECCIÓN 2: TARJETAS DE CASOS (GRID) --- */}
            <div className="solution-cases-grid">
              {/* Mejor Caso */}
              <div className="case-card best">
                <span className="case-title">Mejor Caso (Ω)</span>
                <strong className="case-value">{stepData.cases?.best || "?"}</strong>
              </div>

              {/* Caso Promedio (Destacado) */}
              <div className="case-card average active">
                <span className="case-title">Promedio (Θ)</span>
                <strong className="case-value">{stepData.cases?.average || "?"}</strong>
              </div>

              {/* Peor Caso */}
              <div className="case-card worst">
                <span className="case-title">Peor Caso (O)</span>
                <strong className="case-value">{stepData.cases?.worst || "?"}</strong>
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
        return (
          <div className="dp-content">
            {/* Modelo recursivo */}
            {stepData.modelo_recursivo && (
              <div className="dp-section">
                <h4>Modelo Recursivo</h4>
                <pre>
                  {Array.isArray(stepData.modelo_recursivo)
                    ? stepData.modelo_recursivo.join("\n")
                    : stepData.modelo_recursivo}
                </pre>
              </div>
            )}

            {/* Pseudocódigo */}
            {stepData.pseudocodigo && (
              <div className="dp-section">
                <h4>Pseudocódigo (Top-Down con memoización)</h4>
                <pre>
                  {Array.isArray(stepData.pseudocodigo)
                    ? stepData.pseudocodigo.join("\n")
                    : stepData.pseudocodigo}
                </pre>
              </div>
            )}

            {/* Modelo genérico */}
            {stepData.model && (
              <div className="dp-section">
                <h4>Modelo extraído</h4>
                <p><strong>Recurrencia:</strong> {stepData.model.recurrence}</p>
                <p><strong>Caso base:</strong> {stepData.model.base_case}</p>
                <p><strong>Fórmula DP:</strong> {stepData.model.dp_formula}</p>
                {stepData.model.modelo_recursivo && (
                  <pre>
                    {Array.isArray(stepData.model.modelo_recursivo)
                      ? stepData.model.modelo_recursivo.join("\n")
                      : stepData.model.modelo_recursivo}
                  </pre>
                )}
              </div>
            )}

            {/* Tabla de óptimos */}
            {stepData.TablaOptimos && (
              <div className="dp-section">
                <h4>Tabla de Óptimos</h4>
                {stepData.TablaOptimos.description && (
                  <p>{stepData.TablaOptimos.description}</p>
                )}
                {stepData.TablaOptimos.values_demo_n7 && (
                  <pre>{JSON.stringify(stepData.TablaOptimos.values_demo_n7)}</pre>
                )}
                {stepData.TablaOptimos.transition && (
                  <p><strong>Transición:</strong> {stepData.TablaOptimos.transition}</p>
                )}
              </div>
            )}

            {/* Tabla de caminos */}
            {stepData.TablaCaminos && (
              <div className="dp-section">
                <h4>Tabla de Caminos</h4>
                {stepData.TablaCaminos.description && (
                  <p>{stepData.TablaCaminos.description}</p>
                )}
                {stepData.TablaCaminos.values_demo_n7 && (
                  <pre>{JSON.stringify(stepData.TablaCaminos.values_demo_n7)}</pre>
                )}
                {stepData.TablaCaminos.update && (
                  <p><strong>Actualización:</strong> {stepData.TablaCaminos.update}</p>
                )}
              </div>
            )}

            {/* Vector SOA */}
            {stepData.VectorSOA && (
              <div className="dp-section">
                <h4>Vector SOA</h4>
                {stepData.VectorSOA.description && (
                  <p>{stepData.VectorSOA.description}</p>
                )}
                {stepData.VectorSOA.values_demo_n7 && (
                  <pre>{JSON.stringify(stepData.VectorSOA.values_demo_n7)}</pre>
                )}
                {stepData.VectorSOA.steps && Array.isArray(stepData.VectorSOA.steps) && (
                  <ul className="dp-steps">
                    {stepData.VectorSOA.steps.map((s, i) => (
                      <li key={i}>• {s}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Observaciones */}
            {stepData.observations && (
              <div className="dp-section">
                <h4>Observaciones</h4>
                <p>{stepData.observations}</p>
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
            <h3>{displayTitle}</h3>
          </div>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>

        {/* CUERPO */}
        <div className="modal-body">
            <p>{displayDescription}</p>
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
     
