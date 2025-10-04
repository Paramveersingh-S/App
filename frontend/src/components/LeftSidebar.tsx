"use client";

import { User, Layers3, TowerControl, ShieldAlert, Globe } from "lucide-react";

// Define the types for the component's props
interface LeftSidebarProps {
  activeLayer: string;
  onLayerChange: (layerId: string) => void;
  onProfileClick: () => void;
}

// A helper component to render the correct icon based on the layer name
const LayerIcon = ({ name }: { name: string }) => {
  if (name.includes('Global')) return <Globe size={20} />;
  if (name.includes('Live Stations')) return <TowerControl size={20} />;
  if (name.includes('Citizen')) return <ShieldAlert size={20} />;
  // Default icon for AQI Heatmap
  return <Layers3 size={20} />;
};

export default function LeftSidebar({ activeLayer, onLayerChange, onProfileClick }: LeftSidebarProps) {
  
  // --- THIS IS THE KEY FIX ---
  // A static list of layer options with a specific 'action' for each button.
  const layerOptions = [
    { 
      id: 'aqi', 
      name: 'TEMPO Heatmap', 
      icon: <Layers3 size={20} />, 
      action: () => window.open('/tempo-map', '_blank') // Opens the dedicated map in a new tab
    },
    { 
      id: 'stations', 
      name: 'Live Stations', 
      icon: <TowerControl size={20} />, 
      action: () => onLayerChange('stations') // Switches the layer on the main map
    },
    { 
      id: 'global_stations', 
      name: 'Global Stations', 
      icon: <Globe size={20} />, 
      action: () => onLayerChange('global_stations') 
    },
    { 
      id: 'citizen', 
      name: 'Citizen Reports', 
      icon: <ShieldAlert size={20} />, 
      action: () => onLayerChange('citizen') 
    },
  ];

  return (
    <div className="absolute top-4 left-4 z-10 flex flex-col space-y-4">
      {/* Profile Button */}
      <button 
        onClick={onProfileClick}
        className="bg-gray-800 p-3 rounded-full text-white shadow-lg hover:bg-gray-700 transition-colors"
        aria-label="Open Profile"
      >
        <User size={24} />
      </button>

      {/* Simplified Layer Selector */}
      <div className="bg-gray-800 p-2 rounded-lg text-white shadow-lg space-y-1">
        {layerOptions.map(layer => (
          <button
            key={layer.id}
            onClick={layer.action} // Use the specific action for each button
            className={`flex items-center space-x-3 w-full text-left p-2 rounded-md transition-colors ${
              activeLayer === layer.id
                ? 'bg-blue-600'
                : 'hover:bg-gray-700'
            }`}
          >
            <LayerIcon name={layer.name} />
            <span className="font-medium">{layer.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

