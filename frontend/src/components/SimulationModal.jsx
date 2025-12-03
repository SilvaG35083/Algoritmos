import { useState } from "react";
import RecursionTree from "./RecursionTree.jsx";
import "./SimulationModal.css";

export function SimulationModal({ isOpen, onClose, pseudocode, onSimulate }) {
  const [inputs, setInputs] = useState("");
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
            <small className="section-eyebrow">Simulación y Visualización</small>
            <h3>Árbol de Recursión</h3>
          </div>
          <button className="close-btn" onClick={handleClose}>
            &times;
          </button>
        </div>

        {/* Body con dos columnas */}
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
            <h4>Árbol de Ejecución</h4>
            {treeData ? (
              <div className="tree-container">
                <RecursionTree treeData={treeData} />
              </div>
            ) : (
              <div className="empty-tree-state">
                {loading
                  ? "Generando árbol de recursión..."
                  : "Ingresa los inputs y genera el árbol para visualizar la ejecución"}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
