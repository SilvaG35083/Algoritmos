import { useEffect, useMemo, useRef, useState } from "react";
import { AlgorithmCard } from "./components/AlgorithmCard.jsx";
//import { ResultPanel } from "./components/ResultPanel.jsx";
import { AnalysisModal } from "./PasosAnalisis/AnalysisModal.jsx";
import { SimulationModal } from "./components/SimulationModal.jsx";
import { ChatPanel } from "./components/ChatPanel.jsx";
import {mockAnalysisResult} from "../mockdata.js";
import { Header } from "./components/Header.jsx";

const API_BASE = typeof __API_BASE__ !== "undefined" ? __API_BASE__ : "http://localhost:8000";

function App() {
  const [pseudocode, setPseudocode] = useState("");
  const [samples, setSamples] = useState([]);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploadName, setUploadName] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSimulationModalOpen, setIsSimulationModalOpen] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    async function fetchSamples() {
      try {
        setLoadingSamples(true);
        const res = await fetch(`${API_BASE}/api/samples`);
        if (!res.ok) {
          throw new Error("No fue posible obtener los ejemplos");
        }
        const data = await res.json();
        setSamples(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingSamples(false);
      }
    }
    fetchSamples();
  }, []);

  const handleSimulateClick = () => {
    if (!pseudocode.trim()) {
      setError("Por favor ingresa un algoritmo antes de simular.");
      return;
    }
    setIsSimulationModalOpen(true);
    setError(null);
  };

  const handleSimulate = async (inputsJson) => {
    const payload = { 
      code: pseudocode, 
      inputs: inputsJson
    };
    
    console.log("📤 Enviando al backend:", payload);

    const response = await fetch(`${API_BASE}/api/simulate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("❌ Error del backend:", errorData);
      throw new Error(errorData.detail || errorData.error || "Error en la simulación");
    }

    const data = await response.json();
    console.log("✅ Datos recibidos:", data);
    return data;
  };

  const handleAnalyze = async () => {
    if (!pseudocode.trim()) {
      setError("Por favor ingresa un algoritmo en pseudocodigo.");
      return;
    }
    setError(null);
    setLoadingAnalysis(true);

   try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: pseudocode }),
      });
      
      const data = await res.json();
      
      if (!res.ok || !data.success) {
        // Si hay un error en la respuesta
        const errorMsg = data.error || data.detail || "El analizador rechazó la solicitud.";
        setError(errorMsg);
        // También mostrar el error en el modal si es posible
        setResult({ success: false, error: errorMsg });
        setIsModalOpen(true);
        return;
      }
      
      setResult(data);
      setIsModalOpen(true);
      setError(null);

    } catch (err) {
      setError(err.message);
      // Mostrar error en el modal también
      setResult({ success: false, error: err.message });
      setIsModalOpen(true);
    } finally {
      setLoadingAnalysis(false);
    }

  };

  const handleClear = () => {
    setPseudocode("");
    setResult(null);
    setError(null);
  };

  const handleSampleSelect = (sample) => {
    setPseudocode(sample.pseudocode);
    setError(null);
    setUploadName("");
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const text = loadEvent.target?.result ?? "";
      setPseudocode(String(text));
      setUploadName(file.name);
      setError(null);
    };
    reader.readAsText(file);
  };

  return (
    <div className="app-shell">
      <Header />

      <section className="glass-card input-panel">
          <div className="input-header">
            <div>
              <p className="section-eyebrow">Editor inteligente</p>
              <h2>Pseudocodigo</h2>
              <p className="text-muted">
                Escribe tu algoritmo o carga un archivo `.txt`, `.psc`, `.algo`.
              </p>
            </div>
            <div className="input-toolbar">
              <button className="btn btn-ghost" onClick={handleClear}>
                Limpiar
              </button>
              <button className="btn btn-secondary" onClick={handleFileButtonClick}>
                Cargar archivo
              </button>
              <button className="btn btn-primary" onClick={handleAnalyze} disabled={loadingAnalysis}>
                {loadingAnalysis ? "Analizando..." : "Analizar"}
              </button>
              <button className="btn btn-primary" onClick={handleSimulateClick} disabled={!pseudocode.trim()}>
                Simular
              </button>
              <input
                type="file"
                accept=".txt,.psc,.algo,.md,.json,.py"
                ref={fileInputRef}
                onChange={handleFileChange}
                hidden
              />
            </div>
          </div>
          <textarea
            className="textarea"
            value={pseudocode}
            onChange={(event) => setPseudocode(event.target.value)}
            placeholder="begin&#10;    for i 🡨 1 to n do&#10;    begin&#10;        ...&#10;    end&#10;end"
          />
          <div className="input-footer">
            {uploadName ? (
              <span className="file-indicator">
                Archivo cargado: <strong>{uploadName}</strong>
              </span>
            ) : (
              <span className="text-muted">Puedes pegar texto o subir un archivo.</span>
            )}
            {error && <span className="text-alert">{error}</span>}
          </div>
      </section>

      <section className="glass-card samples-panel">
        <div className="panel-heading">
          <div>
            <p className="section-eyebrow">Dataset de practica</p>
            <h3>Algoritmos de ejemplo</h3>
            <p className="text-muted">Selecciona uno para rellenar el editor.</p>
          </div>
          {loadingSamples && <small className="text-muted">Cargando...</small>}
        </div>
        <div className="samples-grid">
          {samples.map((sample) => (
            <AlgorithmCard key={sample.name} sample={sample} onSelect={handleSampleSelect} />
          ))}
        </div>
      </section>

      <ChatPanel 
        onAlgorithmGenerated={(pseudocode) => {
          setPseudocode(pseudocode);
          setError(null);
        }}
      />

      <section className="info-grid">
        <article className="glass-card info-card">
          <p className="section-eyebrow">LLM Ready</p>
          <h4>Integracion asistida</h4>
          <p className="text-muted">
            El backend expone rutas `/api/analyze` y `/api/analyze-file`, listas para conectar asistentes o pipelines
            automatizados.
          </p>
        </article>
        <article className="glass-card info-card">
          <p className="section-eyebrow">Dataset</p>
          <h4>+10 algoritmos de referencia</h4>
          <p className="text-muted">
            Incluye divide y venceras, iterativos, grafos y casos recursivos para validar el motor.
          </p>
        </article>
        <article className="glass-card info-card">
          <p className="section-eyebrow">Exporta fácil</p>
          <h4>API REST documentada</h4>
          <p className="text-muted">
            Consumo vía JSON para integrar reportes en presentaciones, informes o herramientas de terceros.
          </p>
        </article>
      </section>
      {/* MODAL COMPONENTS */}
      <AnalysisModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        result={result}
      />

      <SimulationModal
        isOpen={isSimulationModalOpen}
        onClose={() => setIsSimulationModalOpen(false)}
        pseudocode={pseudocode}
        onSimulate={handleSimulate}
      />

    </div>
  );
}

export default App;
