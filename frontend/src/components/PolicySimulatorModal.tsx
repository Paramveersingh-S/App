"use client";

import { useState, useEffect } from "react";
import { X, Files, LineChart as LineChartIcon } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

interface PolicyModalProps {
  onClose: () => void;
  lat: number;
  lon: number;
}

export default function PolicySimulatorModal({ onClose, lat, lon }: PolicyModalProps) {
  const [pollutant, setPollutant] = useState("no2");
  const [reduction, setReduction] = useState(20);
  const [simulationData, setSimulationData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/forecast/simulate?lat=${lat}&lon=${lon}&pollutant=${pollutant}&reduction=${reduction}`);
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setSimulationData(data);
    } catch (err: any) {
      console.error("Simulation failed:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Run a default simulation when the modal first opens
  useEffect(() => {
    runSimulation();
  }, []);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-gray-800 text-white p-8 rounded-lg shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
          <div className="flex items-center space-x-3">
            <Files size={28} className="text-blue-400" />
            <h2 className="text-3xl font-bold">Policy Impact Simulator</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={28} />
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-center space-x-4 mb-4 p-4 bg-gray-900/50 rounded-lg">
          <span className="font-medium">If we reduce</span>
          <select value={pollutant} onChange={e => setPollutant(e.target.value)} className="bg-gray-700 p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="no2">NO₂ (Traffic Pollution)</option>
            <option value="pm25">PM2.5 (Fine Particulates)</option>
            <option value="so2">SO₂ (Industrial Emissions)</option>
          </select>
          <span className="font-medium">by</span>
          <input type="range" min="0" max="100" value={reduction} onChange={e => setReduction(parseInt(e.target.value))} className="w-48 cursor-pointer"/>
          <span className="font-bold text-lg w-12 text-center">{reduction}%</span>
          <button onClick={runSimulation} className="bg-blue-600 px-5 py-2 rounded-md font-bold hover:bg-blue-700 transition-colors disabled:bg-gray-500" disabled={isLoading}>
            {isLoading ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {/* Chart Area */}
        <div className="flex-1 flex items-center justify-center">
          {isLoading && <p>Generating simulation...</p>}
          {error && <p className="text-red-400 text-center">Error: {error}</p>}
          {!isLoading && !error && simulationData.length > 0 && (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simulationData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
                <XAxis dataKey="hour" stroke="#9ca3af" />
                <YAxis label={{ value: 'Predicted AQI', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} stroke="#9ca3af" domain={[0, 'dataMax + 20']}/>
                <Tooltip contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', borderColor: '#4a5568', borderRadius: '0.5rem' }}/>
                <Legend />
                <Line type="monotone" dataKey="baseline_aqi" name="Baseline Forecast" stroke="#a8a29e" strokeDasharray="5 5" />
                <Line type="monotone" dataKey="simulated_aqi" name="Simulated Outcome" stroke="#4ade80" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

      </div>
    </div>
  );
}

