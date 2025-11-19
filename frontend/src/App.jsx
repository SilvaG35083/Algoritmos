import { useEffect, useMemo, useRef, useState } from "react";
import { AlgorithmCard } from "./components/AlgorithmCard.jsx";
//import { ResultPanel } from "./components/ResultPanel.jsx";
import { StepViewer } from "./components/StepViewer.jsx";
import { AnalysisModal } from "./PasosAnalisis/AnalysisModal.jsx";
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

  const handleAnalyze = async () => {
    if (!pseudocode.trim()) {
      setError("Por favor ingresa un algoritmo en pseudocodigo.");
      return;
    }
    setError(null);
    setLoadingAnalysis(true);

    // MOCK TEMPORAL 
    setTimeout(() => {
       setResult(mockAnalysisResult);
       setLoadingAnalysis(false);
       setIsModalOpen(true);
     }, 1000);
     return;
    // FIN MOCK TEMPORAL

   /* try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: pseudocode }),
      });
      if (!res.ok) {
        throw new Error("El analizador rechazo la solicitud.");
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingAnalysis(false);
    }
      */
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

  const topSamples = useMemo(() => samples.slice(0, 6), [samples]);

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

      <div className="grid grid--two">
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
            {topSamples.map((sample) => (
              <AlgorithmCard key={sample.name} sample={sample} onSelect={handleSampleSelect} />
            ))}
          </div>
        </section>
      </div>

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
      {/* MODAL COMPONENT  */}
      <AnalysisModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        result={result}
      />

       <div className="grid grid--two">
         {/* ... Samples Panel ... */}
         
         {/* Opcional: Panel placeholder que invite a analizar */}
         <section className="glass-card" style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <p className="text-muted">Los resultados aparecerán en una ventana detallada.</p>
         </section>
       </div>

    </div>
  );
}

export default App;
