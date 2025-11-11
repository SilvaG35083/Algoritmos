import PropTypes from "prop-types";

export function ResultPanel({ summary, annotations, loading }) {
  if (loading) {
    return (
      <section className="result-panel glass-card">
        <p className="text-muted">Analizando algoritmo...</p>
      </section>
    );
  }

  if (!summary) {
    return (
      <section className="result-panel glass-card">
        <p className="text-muted">
          Ingrese un pseudocodigo o cargue un ejemplo para ver el resultado.
        </p>
      </section>
    );
  }

  return (
    <section className="result-panel glass-card">
      <h3>Resumen de Complejidad</h3>
      <div style={{ display: "grid", gap: ".75rem", marginTop: ".75rem" }}>
        <SummaryItem label="Mejor caso" value={summary.best_case} />
        <SummaryItem label="Peor caso" value={summary.worst_case} />
        <SummaryItem label="Caso promedio" value={summary.average_case} />
      </div>

      <h4 style={{ marginTop: "1.8rem" }}>Anotaciones</h4>
      <ul style={{ paddingLeft: "1.25rem", color: "#cbd5f5" }}>
        {Object.entries(annotations || {}).map(([key, value]) => (
          <li key={key}>
            <strong>{formatearClave(key)}:</strong> {value}
          </li>
        ))}
      </ul>
    </section>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div
      style={{
        padding: ".75rem 1rem",
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.08)",
        display: "flex",
        justifyContent: "space-between",
      }}
    >
      <span className="text-muted">{label}</span>
      <span style={{ fontWeight: 600, color: "#fff" }}>{value}</span>
    </div>
  );
}

SummaryItem.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
};

ResultPanel.propTypes = {
  summary: PropTypes.shape({
    best_case: PropTypes.string,
    worst_case: PropTypes.string,
    average_case: PropTypes.string,
  }),
  annotations: PropTypes.object,
  loading: PropTypes.bool,
};

ResultPanel.defaultProps = {
  summary: undefined,
  annotations: undefined,
  loading: false,
};

function formatearClave(key) {
  return key.replace("_", " ");
}
