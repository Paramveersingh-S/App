# /backend/lib/mockData.py

mockLocationForecast = {
  "placeName": "Connaught Place, New Delhi",
  "date": "September 26, 2025",
  "time": "7:54 PM",
  "currentAQI": 162,
  "primaryPollutant": "PM2.5",
  "healthAdvisory": "Unhealthy: Everyone may begin to experience health effects.",
  "weather": {
    "temp": 29,
    "humidity": 75,
    "wind": 8,
  },
  
  # This property is for the multi-line forecast chart
  "pollutantForecast": [
    { "time": "9 PM", "AQI": 165, "NO2": 88, "O3": 45 },
    { "time": "10 PM", "AQI": 168, "NO2": 92, "O3": 42 },
    { "time": "11 PM", "AQI": 170, "NO2": 95, "O3": 40 },
    { "time": "12 AM", "AQI": 166, "NO2": 90, "O3": 48 },
    { "time": "1 AM", "AQI": 161, "NO2": 85, "O3": 52 },
    { "time": "2 AM", "AQI": 158, "NO2": 82, "O3": 55 },
  ],

  # This property is for the pollutant composition pie chart
  "pollutantComposition": [
    { "name": 'PM2.5', "value": 60, "fill": '#ef4444' }, # red
    { "name": 'NO2', "value": 25, "fill": '#fb923c' }, # orange
    { "name": 'O3', "value": 10, "fill": '#60a5fa' }, # blue
    { "name": 'Other', "value": 5, "fill": '#9ca3af' }, # gray
  ]
}