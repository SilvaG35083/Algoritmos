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

  const stepsOrder = ["lexer", "parser", "line_costs", "extraction", "solution"];
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