import PropTypes from "prop-types";

export function AlgorithmCard({ sample, onSelect }) {
  return (
    <article className="sample-card" onClick={() => onSelect(sample)}>
      <header style={{ marginBottom: ".35rem" }}>
        <small className="text-muted">{sample.category}</small>
        <h3 style={{ margin: ".15rem 0 0", fontSize: "1.1rem" }}>
          {sample.name}
        </h3>
      </header>
      <p className="text-muted" style={{ fontSize: ".9rem" }}>
        {sample.description}
      </p>
      <footer style={{ marginTop: ".75rem", fontSize: ".85rem" }}>
        Complejidad esperada:{" "}
        <span style={{ color: "#ff6bcb", fontWeight: 600 }}>
          {sample.expected_complexity}
        </span>
      </footer>
    </article>
  );
}

AlgorithmCard.propTypes = {
  sample: PropTypes.shape({
    name: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    pseudocode: PropTypes.string.isRequired,
    expected_complexity: PropTypes.string.isRequired,
  }).isRequired,
  onSelect: PropTypes.func.isRequired,
};
