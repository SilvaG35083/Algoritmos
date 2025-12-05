import React, { useEffect, useCallback } from 'react';
import ReactFlow, { 
  useNodesState, 
  useEdgesState, 
  Controls, 
  Background,
  MiniMap 
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css'; // Estilos obligatorios

// --- 1. CONFIGURACIÓN DEL LAYOUT AUTOMÁTICO (DAGRE) ---
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 60;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// --- 2. FUNCIÓN PARA APLANAR JSON ---
const parseTreeToGraph = (node, parentId = null, nodes = [], edges = []) => {
  if (!node) return;

  // Creamos el nodo visual
  nodes.push({
    id: node.id,
    data: { 
      label: (
        <div style={{ padding: '10px', textAlign: 'center' }}>
          <strong style={{ display:'block', fontSize: '14px' }}>{node.call}</strong>
          <span style={{ fontSize: '12px', color: '#666' }}>Retorna: {node.result}</span>
        </div>
      ) 
    },
    position: { x: 0, y: 0 }, // Dagre calculará esto después
    style: { 
        background: '#fff', 
        border: '1px solid #777', 
        borderRadius: '8px',
        width: 170
    },
  });

  // Si tiene padre, creamos la conexión (flecha)
  if (parentId) {
    edges.push({
      id: `e-${parentId}-${node.id}`,
      source: parentId,
      target: node.id,
      animated: true, // Flecha animada
      style: { stroke: '#555' },
    });
  }

  // Recursión para los hijos
  if (node.children && node.children.length > 0) {
    node.children.forEach((child) => {
      parseTreeToGraph(child, node.id, nodes, edges);
    });
  }

  return { nodes, edges };
};

// --- 3. COMPONENTE PRINCIPAL ---
export default function RecursionTree({ treeData }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (treeData && treeData.execution_tree) {
      // 1. Convertir JSON jerárquico a listas planas
      const { nodes: rawNodes, edges: rawEdges } = parseTreeToGraph(treeData.execution_tree);
      
      // 2. Calcular posiciones con Dagre
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        rawNodes,
        rawEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [treeData, setNodes, setEdges]);

  if (!treeData) {
    return <div className="text-gray-500 p-4">Esperando simulación...</div>;
  }

  return (
    // El contenedor debe tener altura definida para que ReactFlow se vea
    <div style={{ width: '100%', height: '500px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-right"
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}