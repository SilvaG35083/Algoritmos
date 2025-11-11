import "./Header.css";

const accentGradient =
  "linear-gradient(120deg, rgba(255,107,203,1) 0%, rgba(124,91,255,1) 60%)";

export function Header() {
  return (
    <header className="glass-card header-card">
      <div className="header-content">
        <div>
          <p className="label">Proyecto - Analisis y Diseño de Algoritmos</p>
          <h1>
            Analizador de <span style={{ color: "#ff6bcb" }}>Complejidades</span>
          </h1>
          <p className="text-muted">
            Ingresa un algoritmo en pseudocodigo, selecciona un ejemplo o
            consulta recursiones. El backend evaluara la complejidad (O, Ω, Θ) y
            mostrara las anotaciones clave del analisis heuristico.
          </p>
        </div>
        <div className="badge-stack">
          <div className="badge" style={{ background: accentGradient }}>
            Backend · FastAPI
          </div>
          <div className="badge" style={{ background: accentGradient }}>
            Frontend · React
          </div>
          <div className="badge" style={{ background: accentGradient }}>
            LLM Ready
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
