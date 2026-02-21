'use client';

import { useRef, useCallback, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

interface Node {
  id: string;
  label: string;
}

interface Link {
  source: string;
  target: string;
}

interface EvolutionTreeProps {
  nodes: Node[];
  links: Link[];
}

export default function EvolutionTree({ nodes, links }: EvolutionTreeProps) {
  const fgRef = useRef<any>();

  // Auto-rotate the graph
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.cameraPosition({ z: 200 });
      
      // Auto-rotate
      let angle = 0;
      const rotate = () => {
        if (fgRef.current) {
          fgRef.current.cameraPosition({
            x: 200 * Math.sin(angle),
            z: 200 * Math.cos(angle),
          });
          angle += 0.002;
        }
      };
      const interval = setInterval(rotate, 30);
      return () => clearInterval(interval);
    }
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    if (fgRef.current) {
      // Zoom to node
      const distance = 60;
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
      fgRef.current.cameraPosition(
        {
          x: node.x * distRatio,
          y: node.y * distRatio,
          z: node.z * distRatio,
        },
        node,
        1000
      );
    }
  }, []);

  // Transform data for the graph
  const graphData = {
    nodes: nodes.map((n) => ({
      id: n.id,
      name: n.label,
      color: n.id === 'base' ? '#06b6d4' : '#8b5cf6',
    })),
    links: links.map((l) => ({
      source: l.source,
      target: l.target,
    })),
  };

  if (nodes.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-400">
        <span className="text-4xl mb-2">🧬</span>
        <p>No evolution data yet</p>
        <p className="text-sm">Run tasks and trigger evolution to see the lineage</p>
      </div>
    );
  }

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={graphData}
      nodeLabel="name"
      nodeColor={(node: any) => node.color}
      nodeOpacity={0.9}
      nodeResolution={16}
      linkColor={() => 'rgba(99, 102, 241, 0.5)'}
      linkWidth={2}
      linkOpacity={0.6}
      backgroundColor="rgba(0, 0, 0, 0)"
      onNodeClick={handleNodeClick}
      nodeThreeObject={(node: any) => {
        // Create a glowing sphere
        const THREE = require('three');
        const group = new THREE.Group();
        
        // Core sphere
        const geometry = new THREE.SphereGeometry(5, 32, 32);
        const material = new THREE.MeshPhongMaterial({
          color: node.color,
          emissive: node.color,
          emissiveIntensity: 0.5,
          transparent: true,
          opacity: 0.9,
        });
        const sphere = new THREE.Mesh(geometry, material);
        group.add(sphere);
        
        // Glow effect
        const glowGeometry = new THREE.SphereGeometry(7, 32, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
          color: node.color,
          transparent: true,
          opacity: 0.2,
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        group.add(glow);
        
        return group;
      }}
      warmupTicks={50}
      cooldownTicks={100}
    />
  );
}
