// /frontend/src/lib/mockData.ts

export const mockLocationForecast = {
"placeName": "Central Park, New York",
  "date": "September 26, 2025",
  "time": "7:48 PM",
  currentAQI: 85,
  primaryPollutant: "PM2.5",
  healthAdvisory: "Moderate: Unhealthy for Sensitive Groups.",
  weather: {
    temp: 22,
    humidity: 65,
    wind: 10,
  },
  
  // This property is for the multi-line forecast chart
  pollutantForecast: [
    { time: "9 PM", AQI: 88, NO2: 45, O3: 30 },
    { time: "10 PM", AQI: 92, NO2: 50, O3: 28 },
    { time: "11 PM", AQI: 95, NO2: 55, O3: 25 },
    { time: "12 AM", AQI: 91, NO2: 52, O3: 29 },
    { time: "1 AM", AQI: 87, NO2: 48, O3: 32 },
    { time: "2 AM", AQI: 82, NO2: 42, O3: 35 },
  ],

  // This property is for the pollutant composition pie chart
  pollutantComposition: [
    { name: 'PM2.5', value: 45, fill: '#facc15' }, // yellow
    { name: 'NO2', value: 30, fill: '#fb923c' }, // orange
    { name: 'O3', value: 20, fill: '#60a5fa' }, // blue
    { name: 'Other', value: 5, fill: '#9ca3af' }, // gray
  ]
};

// This mock data is for the main map's heatmap layer
export const mockGridData = [
  { lat: 40.78, lon: -73.96, aqi: 85 },
  { lat: 40.79, lon: -73.95, aqi: 95 },
  { lat: 40.77, lon: -73.97, aqi: 75 },
  { lat: 34.05, lon: -118.24, aqi: 110 },
  { lat: 34.06, lon: -118.25, aqi: 120 },
  { lat: 28.61, lon: 77.20, aqi: 180 }, // Data point for India
  { lat: 28.65, lon: 77.23, aqi: 195 }, // Data point for India
];