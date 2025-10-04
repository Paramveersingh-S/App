"use client";

import { LocationData } from "@/app/page";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, PieChart, Pie, Cell } from "recharts";
import { AlertTriangle, ShieldCheck, Siren } from "lucide-react";
import { useMemo } from "react";

interface DataPanelProps {
  locationData: LocationData | null;
}

// Helper to determine color and icon for the alert
const getAlertStyle = (riskLevel?: string) => {
  switch (riskLevel?.toLowerCase()) {
    case 'high':
    case 'very high':
      return { icon: <AlertTriangle size={24} />, color: 'bg-red-500/20 text-red-300 border-red-500/50' };
    case 'moderate':
      return { icon: <AlertTriangle size={24} />, color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50' };
    case 'good':
      return { icon: <ShieldCheck size={24} />, color: 'bg-green-500/20 text-green-300 border-green-500/50' };
    default:
      return { icon: <Siren size={24} />, color: 'bg-gray-500/20 text-gray-300 border-gray-500/50' };
  }
};

const POLLUTANT_COLORS: { [key: string]: string } = {
  pm25: '#facc15', // yellow
  no2: '#fb923c',  // orange
  o3: '#60a5fa',   // blue
  pm10: '#fca5a5', // light red
  so2: '#93c5fd',  // light blue
  co: '#d1d5db',   // gray
};

export default function DataPanel({ locationData }: DataPanelProps) {
  if (!locationData) {
    return (
      <div className="bg-gray-800 text-white p-6 w-96 flex-shrink-0 flex items-center justify-center shadow-lg">
        <p className="text-gray-400 text-center text-lg">
          Click on a map pin to see live station details. 🗺️
        </p>
      </div>
    );
  }
  
  const alertStyle = getAlertStyle(locationData.alert?.risk_level);

  // Memoized data transformation to create a consistent format for the charts
  const chartData = useMemo(() => {
    // 1. Transform data for the Pie Chart (current composition)
    const composition = locationData.pollutantDetails 
      ? Object.entries(locationData.pollutantDetails).map(([key, value]) => ({
          name: key.toUpperCase(),
          value: (value as any).v,
          fill: POLLUTANT_COLORS[key] || '#9ca3af'
        }))
      : [];

    // --- THIS IS THE CORRECTED LOGIC ---
    // 2. Transform the complex forecast data into a simple array for the line chart
    let forecast = null;
    if (locationData.forecast) {
        const forecastByDay: { [key: string]: any } = {};
        const pollutantsInForecast = Object.keys(locationData.forecast);
        
        pollutantsInForecast.forEach(pollutant => {
            if (locationData.forecast[pollutant] && Array.isArray(locationData.forecast[pollutant])) {
                locationData.forecast[pollutant].forEach((dailyData: any) => {
                    const day = dailyData.day.slice(5); // Format day as MM-DD
                    if (!forecastByDay[day]) {
                        forecastByDay[day] = { day };
                    }
                    forecastByDay[day][pollutant] = dailyData.avg;
                });
            }
        });
        forecast = Object.values(forecastByDay).sort((a,b) => a.day.localeCompare(b.day));
    }

    return { composition, forecast };
  }, [locationData]);

  return (
    <div className="bg-gray-800 text-white p-6 w-96 flex-shrink-0 flex flex-col space-y-6 shadow-lg overflow-y-auto">
      {/* Location Name & Time */}
      <div className="border-b border-gray-700 pb-4">
        <h2 className="text-2xl font-bold truncate">{locationData.placeName}</h2>
        <p className="text-sm text-gray-400">{locationData.date} at {locationData.time}</p>
      </div>

      {/* Personalized Alert Section */}
      {locationData.alert && !locationData.alert.error && (
        <div className={`p-4 rounded-lg border flex items-start space-x-3 ${alertStyle.color}`}>
          <div className="flex-shrink-0">{alertStyle.icon}</div>
          <div>
            <h3 className="font-bold">{locationData.alert.risk_level} Risk</h3>
            <p className="text-sm">{locationData.alert.recommendation}</p>
          </div>
        </div>
      )}

      {/* Main AQI Display & Composition Pie Chart */}
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <p className="text-gray-400">Current AQI</p>
          <p className="text-6xl font-bold text-yellow-400">{locationData.currentAQI}</p>
          {locationData.dominantPollutant && <p className="text-gray-400">Dominant: {locationData.dominantPollutant.toUpperCase()}</p>}
        </div>
        
        {chartData.composition.length > 0 && (
          <div className="w-28 h-28 flex-shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', borderColor: '#4a5568', borderRadius: '0.5rem' }} 
                />
                <Pie data={chartData.composition} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={30} outerRadius={45} paddingAngle={5}>
                  {chartData.composition.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* --- FINAL, CORRECTED Daily Forecast Line Chart --- */}
      {chartData.forecast && chartData.forecast.length > 0 && (
        <div className="h-56 flex-shrink-0">
          <h3 className="font-bold mb-2 text-gray-300">Daily Forecast</h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData.forecast} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} domain={[0, 'dataMax + 50']} />
              <Tooltip contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', borderColor: '#4a5568', borderRadius: '0.5rem' }} />
              <Legend wrapperStyle={{fontSize: "12px"}}/>
              {Object.keys(POLLUTANT_COLORS).map(pollutant => {
                // This robust check ensures we render a line for any pollutant that has forecast data
                if (chartData.forecast.some(day => day[pollutant] !== undefined)) {
                  return <Line key={pollutant} type="monotone" dataKey={pollutant} name={pollutant.toUpperCase()} stroke={POLLUTANT_COLORS[pollutant]} strokeWidth={2} dot={false} />
                }
                return null;
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

