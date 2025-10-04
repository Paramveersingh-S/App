"use client";

import { TestTube2, Files, UserCheck } from "lucide-react";

// The component now accepts props for each button's click handler
interface HeaderProps {
    onForecastClick: () => void;
    onPolicyClick: () => void;
    onCitizenClick: () => void;
}

export default function Header({ onForecastClick, onPolicyClick, onCitizenClick }: HeaderProps) {
  return (
    <header className="absolute top-4 right-4 z-10">
      <div className="flex items-center space-x-2 bg-gray-800/80 backdrop-blur-sm p-2 rounded-lg shadow-lg">
        <button 
          onClick={onForecastClick}
          className="flex items-center space-x-2 text-white px-3 py-2 rounded-md hover:bg-gray-700 transition-colors"
          aria-label="Open Forecast Model"
        >
          <TestTube2 size={18} />
          <span className="hidden sm:inline">Forecast Model</span>
        </button>
        <button 
          onClick={onPolicyClick}
          className="flex items-center space-x-2 text-white px-3 py-2 rounded-md hover:bg-gray-700 transition-colors"
          aria-label="Open Policy Simulator"
        >
          <Files size={18} />
          <span className="hidden sm:inline">Policy Simulator</span>
        </button>
        <button 
          onClick={onCitizenClick}
          className="flex items-center space-x-2 text-white px-3 py-2 rounded-md hover:bg-gray-700 transition-colors"
          aria-label="Open Citizen Science"
        >
          <UserCheck size={18} />
          <span className="hidden sm:inline">Citizen Science</span>
        </button>
      </div>
    </header>
  );
}

