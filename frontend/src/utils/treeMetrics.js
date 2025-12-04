/**
 * Recorre el árbol recursivamente para extraer métricas exactas.
 * @param {Object} rootNode - El nodo raíz del JSON (execution_tree)
 * @returns {Object} { totalSteps, maxDepth }
 */
export const calculateTreeMetrics = (rootNode) => {
  if (!rootNode) return { totalSteps: 0, maxDepth: 0 };

  let totalSteps = 1; // Contamos el nodo actual
  let maxChildDepth = 0;

  if (rootNode.children && rootNode.children.length > 0) {
    rootNode.children.forEach(child => {
      const childMetrics = calculateTreeMetrics(child);
      totalSteps += childMetrics.totalSteps;
      // La profundidad es el máximo de los hijos
      maxChildDepth = Math.max(maxChildDepth, childMetrics.maxDepth);
    });
  }

  return {
    totalSteps,
    maxDepth: 1 + maxChildDepth // 1 (actual) + la profundidad más honda encontrada
  };
};
