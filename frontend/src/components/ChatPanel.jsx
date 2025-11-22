import { useState, useRef, useEffect } from "react";
import "./ChatPanel.css";

const API_BASE = typeof __API_BASE__ !== "undefined" ? __API_BASE__ : "http://localhost:8000";

export function ChatPanel({ onAlgorithmGenerated }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [provider, setProvider] = useState("openai");
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: inputValue.trim(),
      timestamp: Date.now() / 1000,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);
    setError(null);

    try {
      // Preparar historial de conversación: convertir contenido a string si es objeto
      const conversationHistory = messages.map((m) => {
        let contentStr = m.content;
        // Si el contenido es un objeto (respuesta del asistente), convertirlo a string
        if (typeof m.content === "object" && m.content !== null) {
          // Extraer el resumen o pseudocódigo como representación del mensaje
          if (m.content.summary) {
            contentStr = m.content.summary;
          } else if (m.content.pseudocode) {
            contentStr = m.content.pseudocode;
          } else {
            contentStr = JSON.stringify(m.content);
          }
        }
        return {
          role: m.role,
          content: contentStr,
          timestamp: m.timestamp,
        };
      });

      const response = await fetch(`${API_BASE}/api/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_history: conversationHistory,
          provider: provider,
        }),
      });

      if (!response.ok) {
        throw new Error("Error al comunicarse con el asistente LLM");
      }

      const data = await response.json();

      const assistantMessage = {
        role: "assistant",
        content: data,
        timestamp: Date.now() / 1000,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Si hay pseudocódigo generado, notificar al componente padre
      if (data.pseudocode && onAlgorithmGenerated) {
        onAlgorithmGenerated(data.pseudocode);
      }
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        role: "assistant",
        content: {
          pseudocode: "",
          summary: `Error: ${err.message}`,
          steps: [],
        },
        isError: true,
        timestamp: Date.now() / 1000,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="chat-panel glass-card">
      <div className="chat-header">
        <div>
          <p className="section-eyebrow">Asistente LLM</p>
          <h3>Chat Interactivo</h3>
          <p className="text-muted">
            Pide algoritmos en lenguaje natural y obtén pseudocódigo con análisis detallado
          </p>
        </div>
        <div className="chat-controls">
          <select
            className="provider-select"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            disabled={loading}
          >
            <option value="openai">ChatGPT</option>
            <option value="gemini">Gemini</option>
          </select>
          <button className="btn btn-ghost" onClick={handleClear} disabled={loading}>
            Limpiar
          </button>
        </div>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p className="text-muted">
              👋 Hola! Puedo ayudarte a generar algoritmos en pseudocódigo y analizar su complejidad.
            </p>
            <p className="text-muted">Ejemplos de peticiones:</p>
            <ul className="chat-examples">
              <li>"Genera un algoritmo de merge sort y analiza su complejidad"</li>
              <li>"Crea un algoritmo de búsqueda binaria recursiva"</li>
              <li>"Dame un algoritmo de quicksort con análisis detallado"</li>
            </ul>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))
        )}
        {loading && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-avatar">🤖</div>
            <div className="chat-bubble">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        {error && <div className="chat-error">{error}</div>}
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu petición aquí... (Enter para enviar, Shift+Enter para nueva línea)"
            rows={2}
            disabled={loading}
          />
          <button
            className="btn btn-primary chat-send-btn"
            onClick={handleSend}
            disabled={loading || !inputValue.trim()}
          >
            {loading ? "..." : "Enviar"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ChatMessage({ message }) {
  const { role, content, isError } = message;

  if (role === "user") {
    return (
      <div className="chat-message chat-message-user">
        <div className="chat-bubble chat-bubble-user">
          <p>{content}</p>
        </div>
        <div className="chat-avatar">👤</div>
      </div>
    );
  }

  // Mensaje del asistente
  const data = typeof content === "object" ? content : { summary: content, steps: [] };

  return (
    <div className={`chat-message chat-message-assistant ${isError ? "chat-error-message" : ""}`}>
      <div className="chat-avatar">🤖</div>
      <div className="chat-bubble chat-bubble-assistant">
        {data.pseudocode && (
          <div className="chat-pseudocode">
            <div className="chat-section-title">📝 Pseudocódigo Generado</div>
            <pre className="chat-code-block">{data.pseudocode}</pre>
          </div>
        )}

        {data.summary && (
          <div className={`chat-summary ${data.error || isError ? "chat-error-summary" : ""}`}>
            <div className="chat-section-title">
              {data.error || isError ? "⚠️ Error" : "📊 Resumen"}
            </div>
            <p style={{ whiteSpace: "pre-line" }}>{data.summary}</p>
            {data.error && (
              <div className="chat-error-suggestion">
                <p><strong>Sugerencias:</strong></p>
                <ul>
                  <li>Cambia a Gemini (gratis) usando el selector de proveedor arriba</li>
                  <li>Verifica tu configuración de API keys</li>
                  <li>Recarga créditos en tu cuenta de OpenAI</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {data.method && (
          <div className="chat-method">
            <span className="chat-tag">Método: {data.method}</span>
          </div>
        )}

        {data.complexity_analysis && (
          <div className="chat-complexity">
            <div className="chat-section-title">⚡ Complejidad</div>
            <div className="complexity-grid">
              <div className="complexity-item">
                <span className="complexity-label">Mejor caso:</span>
                <span className="complexity-value">{data.complexity_analysis.best_case}</span>
              </div>
              <div className="complexity-item">
                <span className="complexity-label">Peor caso:</span>
                <span className="complexity-value">{data.complexity_analysis.worst_case}</span>
              </div>
              <div className="complexity-item">
                <span className="complexity-label">Promedio:</span>
                <span className="complexity-value">{data.complexity_analysis.average_case}</span>
              </div>
              {data.complexity_analysis.space_complexity && (
                <div className="complexity-item">
                  <span className="complexity-label">Espacio:</span>
                  <span className="complexity-value">{data.complexity_analysis.space_complexity}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {data.equations && data.equations.length > 0 && (
          <div className="chat-equations">
            <div className="chat-section-title">📐 Ecuaciones de Recurrencia</div>
            {data.equations.map((eq, idx) => (
              <div key={idx} className="equation-item">
                <div className="equation-formula">{eq.equation}</div>
                <p className="equation-explanation">{eq.explanation}</p>
                {eq.solution && (
                  <div className="equation-solution">Solución: {eq.solution}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {data.recursion_tree && (
          <div className="chat-recursion-tree">
            <div className="chat-section-title">🌳 Árbol de Recursión</div>
            <p className="tree-description">{data.recursion_tree.description}</p>
            <div className="tree-levels">
              {data.recursion_tree.levels.map((level, idx) => (
                <div key={idx} className="tree-level">
                  <div className="tree-level-label">Nivel {level.level}</div>
                  <div className="tree-nodes">
                    {level.nodes.map((node, nodeIdx) => (
                      <span key={nodeIdx} className="tree-node">{node}</span>
                    ))}
                  </div>
                  <div className="tree-level-cost">Costo: {level.cost}</div>
                </div>
              ))}
            </div>
            <div className="tree-total-cost">
              <strong>Costo total: {data.recursion_tree.total_cost}</strong>
            </div>
          </div>
        )}

        {data.steps && data.steps.length > 0 && (
          <div className="chat-steps">
            <div className="chat-section-title">🔍 Análisis Línea por Línea</div>
            <div className="steps-list">
              {data.steps.map((step, idx) => (
                <div key={idx} className="step-item">
                  <div className="step-header">
                    <strong>{step.title}</strong>
                    {step.line_number && (
                      <span className="step-line-number">Línea {step.line_number}</span>
                    )}
                  </div>
                  {step.line && (
                    <div className="step-code">
                      <code>{step.line}</code>
                    </div>
                  )}
                  <p className="step-detail">{step.detail}</p>
                  <div className="step-meta">
                    {step.cost && <span className="step-chip">Costo: {step.cost}</span>}
                    {step.method_used && (
                      <span className="step-chip">Método: {step.method_used}</span>
                    )}
                    {step.recurrence && (
                      <span className="step-chip">Recurrencia: {step.recurrence}</span>
                    )}
                  </div>
                  {step.explanation && (
                    <p className="step-explanation">{step.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {(data.tokens_used || data.latency_ms) && (
          <div className="chat-metrics">
            {data.tokens_used && <span className="metric">Tokens: {data.tokens_used}</span>}
            {data.latency_ms && (
              <span className="metric">Latencia: {data.latency_ms}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
