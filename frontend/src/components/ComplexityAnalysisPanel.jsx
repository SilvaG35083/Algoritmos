import React, { useState } from 'react';

const ComplexityAnalysisPanel = ({ analysisData }) => {
  const [showExplanation, setShowExplanation] = useState(false);
  
  console.log("📐 ComplexityAnalysisPanel - analysisData recibido:", analysisData);
  
  // Si no hay datos de análisis matemático (ej. versiones viejas del backend), no mostramos nada
  if (!analysisData) return null;

  const { 
    recurrence_relation, 
    technique_used, 
    technique_explanation, 
    complexity 
  } = analysisData;

  console.log("📐 Datos extraídos:");
  console.log("  - recurrence_relation:", recurrence_relation);
  console.log("  - technique_used:", technique_used);
  console.log("  - technique_explanation:", technique_explanation);
  console.log("  - complexity:", complexity);

  return (
    <div style={{ marginTop: '1rem' }}>
      <h5 style={{ 
        fontSize: '0.75rem', 
        fontWeight: 'bold', 
        color: '#a1a1aa', 
        textTransform: 'uppercase', 
        marginBottom: '0.75rem',
        letterSpacing: '0.5px'
      }}>
        📐 Fundamentación Matemática
      </h5>

      {/* 1. Grid de Casos - Estilo compacto como métricas reales */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        {/* Mejor Caso */}
        <div style={{
          padding: '1rem',
          background: 'rgba(9, 10, 18, 0.5)',
          borderRadius: '8px',
          borderLeft: '3px solid #22c55e',
          transition: 'transform 0.2s ease, box-shadow 0.2s ease'
        }}>
          <h4 style={{ 
            color: '#a1a1aa', 
            fontSize: '0.75rem', 
            textTransform: 'uppercase', 
            fontWeight: 'bold', 
            margin: '0 0 0.5rem',
            letterSpacing: '0.5px'
          }}>
            Mejor Caso (Ω)
          </h4>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            lineHeight: '1.2',
            color: '#4ade80',
            fontFamily: 'monospace'
          }}>
            {complexity?.best_case || "-"}
          </div>
          <p style={{ 
            fontSize: '0.8rem', 
            color: '#71717a', 
            margin: '0.5rem 0 0',
            lineHeight: '1.4'
          }}>
            Escenario óptimo
          </p>
        </div>

        {/* Caso Promedio */}
        <div style={{
          padding: '1rem',
          background: 'rgba(9, 10, 18, 0.5)',
          borderRadius: '8px',
          borderLeft: '3px solid #3b82f6',
          transition: 'transform 0.2s ease, box-shadow 0.2s ease'
        }}>
          <h4 style={{ 
            color: '#a1a1aa', 
            fontSize: '0.75rem', 
            textTransform: 'uppercase', 
            fontWeight: 'bold', 
            margin: '0 0 0.5rem',
            letterSpacing: '0.5px'
          }}>
            Promedio (Θ)
          </h4>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            lineHeight: '1.2',
            color: '#60a5fa',
            fontFamily: 'monospace'
          }}>
            {complexity?.average_case || "-"}
          </div>
          <p style={{ 
            fontSize: '0.8rem', 
            color: '#71717a', 
            margin: '0.5rem 0 0',
            lineHeight: '1.4'
          }}>
            Caso típico
          </p>
        </div>

        {/* Peor Caso */}
        <div style={{
          padding: '1rem',
          background: 'rgba(9, 10, 18, 0.5)',
          borderRadius: '8px',
          borderLeft: '3px solid #ef4444',
          transition: 'transform 0.2s ease, box-shadow 0.2s ease'
        }}>
          <h4 style={{ 
            color: '#a1a1aa', 
            fontSize: '0.75rem', 
            textTransform: 'uppercase', 
            fontWeight: 'bold', 
            margin: '0 0 0.5rem',
            letterSpacing: '0.5px'
          }}>
            Peor Caso (O)
          </h4>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            lineHeight: '1.2',
            color: '#f87171',
            fontFamily: 'monospace'
          }}>
            {complexity?.worst_case || "-"}
          </div>
          <p style={{ 
            fontSize: '0.8rem', 
            color: '#71717a', 
            margin: '0.5rem 0 0',
            lineHeight: '1.4'
          }}>
            Límite superior
          </p>
        </div>
      </div>

      {/* 2. Botón de Explicación - Estilo coherente */}
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          style={{
            padding: '0.65rem 1.5rem',
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '12px',
            fontSize: '0.9rem',
            fontWeight: '600',
            color: '#f4f4f5',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'}
        >
          <span>{showExplanation ? '📖' : '📚'}</span>
          {showExplanation ? 'Ocultar Explicación' : 'Ver Explicación Detallada'}
          <span style={{ fontSize: '0.75rem' }}>{showExplanation ? '▲' : '▼'}</span>
        </button>
      </div>

      {/* 3. Panel de Explicación (Colapsable) */}
      {showExplanation && (
        <div style={{
          background: 'rgba(9, 10, 18, 0.5)',
          borderRadius: '8px',
          padding: '1rem',
          border: '1px solid #27272a',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <span style={{ 
              fontSize: '0.75rem', 
              color: '#a1a1aa', 
              fontWeight: 'bold', 
              display: 'block', 
              marginBottom: '0.5rem' 
            }}>
              📝 Relación de Recurrencia:
            </span>
            <code style={{ 
              color: '#fbbf24', 
              fontFamily: 'monospace', 
              fontSize: '0.9rem', 
              display: 'block', 
              background: '#0b0d14', 
              padding: '0.75rem', 
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              {recurrence_relation || "No aplica"}
            </code>
          </div>
          
          <div>
            <span style={{ 
              fontSize: '0.75rem', 
              color: '#60a5fa', 
              fontWeight: 'bold', 
              display: 'block', 
              marginBottom: '0.5rem' 
            }}>
              🔧 Técnica Identificada: <span style={{ color: '#93c5fd' }}>{technique_used}</span>
            </span>
            <p style={{ 
              fontSize: '0.85rem', 
              color: '#d4d4d8', 
              marginTop: '0.5rem', 
              lineHeight: '1.6',
              background: '#0b0d14', 
              padding: '0.75rem', 
              borderRadius: '6px',
              fontStyle: 'italic',
              borderLeft: '3px solid #3b82f6'
            }}>
              "{technique_explanation}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplexityAnalysisPanel;