import PropTypes from "prop-types";

export function AlgorithmCard({ sample, onSelect }) {
  return (
    <article className="sample-card" onClick={() => onSelect(sample)}>
      <header className="sample-card-header">
        <small className="text-muted">{sample.category}</small>
        <h3 className="sample-card-title">{sample.name}</h3>
      </header>
      <p className="text-muted sample-card-description">
        {sample.description}
      </p>
      <footer className="sample-card-footer">
        Complejidad esperada:{" "}
        <span className="sample-card-complexity">
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
