"use client";

import { useState, useEffect, useMemo } from "react";
import { X, TestTube2, LineChart as LineChartIcon, Info } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

interface ForecastModalProps {
  onClose: () => void;
  lat: number;
  lon: number;
}

interface ForecastDataPoint {
  hour: string;
  predicted_aqi: number;
}

const POLLUTANT_COLORS: { [key: string]: string } = {
  predicted_aqi: '#8884d8',
  pm25: '#facc15',
  no2: '#fb923c',
  o3: '#60a5fa',
  pm10: '#fca5a5',
};

export default function ForecastModal({ onClose, lat, lon }: ForecastModalProps) {
  const [forecastData, setForecastData] = useState<ForecastDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const generateForecast = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/forecast/point?lat=${lat}&lon=${lon}`);
        const data = await response.json();

        // --- THIS IS THE KEY FIX ---
        // Check if the API returned an error or if the data is not an array
        if (data.error || !Array.isArray(data)) {
          throw new Error(data.error || "Invalid data format received from server.");
        }
        // --- END OF FIX ---

        setForecastData(data);
      } catch (err: any) {
        setError(err.message || "Unknown error occurred while fetching forecast.");
      } finally {
        setIsLoading(false);
      }
    };

    generateForecast();
  }, [lat, lon]);

  // Calculate summary statistics for "at a glance" info
  const summaryStats = useMemo(() => {
    if (!forecastData || forecastData.length === 0) return null;
    const aqiValues = forecastData.map(d => d.predicted_aqi);
    return {
        max: Math.max(...aqiValues),
        min: Math.min(...aqiValues),
        avg: (aqiValues.reduce((acc, d) => acc + d.predicted_aqi, 0) / forecastData.length).toFixed(0),
    };
  }, [forecastData]);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-gray-800 text-white p-8 rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col" 
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
          <div className="flex items-center space-x-3">
            <TestTube2 size={32} className="text-blue-400" />
            <h2 className="text-3xl font-bold tracking-tight">Live 48-Hour Forecast</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={28} />
          </button>
        </div>

        {/* Summary Bar */}
        <div className="flex space-x-8 justify-center pb-4 text-gray-300">
          {summaryStats && (
            <>
              <div className="flex items-center space-x-2">
                <LineChartIcon size={20} className="text-red-400" />
                <span><span className="font-medium text-white">Peak AQI</span>: {summaryStats.max}</span>
              </div>
              <div className="flex items-center space-x-2">
                <LineChartIcon size={20} className="text-green-400" />
                <span><span className="font-medium text-white">Lowest AQI</span>: {summaryStats.min}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Info size={20} className="text-yellow-400" />
                <span><span className="font-medium text-white">Average AQI</span>: {summaryStats.avg}</span>
              </div>
            </>
          )}
        </div>

        {/* Main Display */}
        <div className="flex-1 flex items-center justify-center">
          {isLoading && (
            <p className="text-blue-300 animate-pulse text-lg">Generating live forecast...</p>
          )}
          {error && (
            <p className="text-red-400 text-lg font-semibold text-center">Error: {error}</p>
          )}
          {!isLoading && !error && forecastData.length > 0 && (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData} margin={{ top: 10, right: 30, left: 20, bottom: 15 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
                <XAxis dataKey="hour" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9ca3af" domain={[0, 'dataMax + 20']} tick={{ fontSize: 14 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', borderColor: '#4a5568', borderRadius: '0.5rem' }} 
                  labelStyle={{ color: '#c9c9c9', fontWeight: 500 }}
                />
                <Legend />
                
                {/* Dynamically render a line for each pollutant in the data */}
                {Object.keys(POLLUTANT_COLORS).map(pollutant => {
                  if (forecastData.some(d => d[pollutant] !== undefined)) {
                    return (
                      <Line 
                        key={pollutant}
                        type="monotone" 
                        dataKey={pollutant} 
                        name={pollutant === 'predicted_aqi' ? 'Overall AQI' : pollutant.toUpperCase()} 
                        stroke={POLLUTANT_COLORS[pollutant]} 
                        strokeWidth={pollutant === 'predicted_aqi' ? 3 : 2}
                        dot={false}
                        activeDot={{ r: 5 }} 
                      />
                    );
                  }
                  return null;
                })}
              </LineChart>
            </ResponsiveContainer>
          )}
          {!isLoading && !error && forecastData.length === 0 && (
            <p>No forecast data available for this location.</p>
          )}
        </div>
      </div>
    </div>
  );
}

