import React, { useState } from "react";
import "./AnalysisModal.css"; // <--- IMPORTANTE: Importar el CSS

export function AnalysisModal({ isOpen, onClose, result }) {
  const [currentStep, setCurrentStep] = useState(0);

  // Si no está abierto, retornamos null (no se renderiza nada)
  if (!isOpen || !result) return null;

  if (result.success === false || result.error) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content error-state" onClick={(e) => e.stopPropagation()}>
           <div className="modal-header">
              <h3 style={{color: '#ef4444'}}>Error en el Análisis</h3>
              <button className="close-btn" onClick={onClose}>&times;</button>
           </div>
           <div className="modal-body">
             <p>Ocurrió un problema al procesar el algoritmo:</p>
             <pre style={{background: '#450a0a', color: '#fecaca', padding: '1rem', borderRadius: '8px'}}>
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
     return null; // O podrías mostrar un mensaje de "Datos incompletos"
  }

  const stepsOrder = ["lexer", "parser", "extraction", "solution"];
  const stepKey = stepsOrder[currentStep];
  const stepData = result.steps[stepKey];

  // Funciones de navegación
  const handleNext = () => {
    if (currentStep < stepsOrder.length - 1) setCurrentStep((prev) => prev + 1);
  };
  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep((prev) => prev - 1);
  };
  
  // Reiniciar el paso al cerrar (opcional, para que empiece en 1 siempre)
  const handleClose = () => {
      setCurrentStep(0);
      onClose();
  }

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
          <pre style={{ background: '#18181b', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.9rem', color: '#a5b4fc' }}>
            {stepData.data}
          </pre>
        );
      case "extraction":
        return (
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <h2 style={{ color: '#60a5fa', fontFamily: 'monospace', fontSize: '2rem' }}>{stepData.equation}</h2>
            <p className="text-muted" style={{ marginTop: '1rem' }}>{stepData.explanation}</p>
          </div>
        );
      case "solution":
        return (
          <div style={{ textAlign: 'center' }}>
            <h1 style={{ color: '#4ade80', fontSize: '3.5rem', margin: '0' }}>{stepData.complexity}</h1>
            <p style={{ marginBottom: '2rem', color: '#e4e4e7' }}>{stepData.details}</p>
            
            {/* Desglose Matemático */}
            <div style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ color: '#fff', marginBottom: '0.5rem' }}>Demostración:</h4>
                {stepData.math_steps?.map((step, idx) => (
                    <div key={idx} style={{ marginBottom: '6px', fontSize: '0.9rem', color: '#d4d4d8' }}>
                        <strong style={{ color: '#818cf8' }}>{step.label}:</strong> {step.value}
                    </div>
                ))}
            </div>
          </div>
        );
      default: return null;
    }
  };

  return (
    // El overlay cubre toda la pantalla
    <div className="modal-overlay" onClick={handleClose}>
      
      {/* El stopPropagation evita que se cierre si das clic DENTRO de la tarjeta */}
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        {/* CABECERA */}
        <div className="modal-header">
          <div>
            <small style={{ color: '#a1a1aa', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '1px' }}>
                Paso {currentStep + 1} / 4
            </small>
            <h3 style={{ margin: 0, color: 'white' }}>{stepData.title}</h3>
          </div>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>

        {/* CUERPO */}
        <div className="modal-body">
            <p style={{ color: '#d4d4d8', marginBottom: '1.5rem' }}>{stepData.description}</p>
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
            onClick={currentStep === 3 ? handleClose : handleNext}
          >
            {currentStep === 3 ? "Finalizar" : "Siguiente"}
          </button>
        </div>
      </div>
    </div>
  );
}