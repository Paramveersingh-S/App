"use client";

import React, { useState, useEffect } from "react";
import Map, { ViewState } from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import { Color } from "@deck.gl/core";
import "maplibre-gl/dist/maplibre-gl.css";

// --- CONSTANTS ---
const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// The initial camera position, zoomed out to show a global view
const INITIAL_VIEW_STATE: ViewState = {
  longitude: 20, // A more central longitude to see both datasets
  latitude: 35,
  zoom: 1.5, // Zoomed out to see both North America and India
  pitch: 30,
  bearing: 0,
  padding: { top: 0, right: 0, bottom: 0, left: 0 }
};

// A beautiful color range for the heatmap visualization
const HEATMAP_COLOR_RANGE: Color[] = [
    [76, 175, 80, 0], [76, 175, 80, 180], [255, 235, 59, 200],
    [255, 152, 0, 220], [244, 67, 54, 240], [156, 39, 176, 255]
];

export default function TempoMapPage() {
  const [viewState, setViewState] = useState<ViewState>(INITIAL_VIEW_STATE);
  const [mapData, setMapData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch the combined data from our new, unified backend endpoint
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/maps/combined_view");
        const data = await response.json();
        setMapData(data);
      } catch (error) {
        console.error("Failed to fetch combined map data:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // Use the HeatmapLayer to create a smooth, blended visualization
  const layers = [
    new HeatmapLayer({
      id: 'combined-heatmap-layer',
      data: mapData,
      getPosition: (d: any) => [d.lon, d.lat],
      getWeight: (d: any) => d.aqi,
      radiusPixels: 60,
      intensity: 1.2,
      colorRange: HEATMAP_COLOR_RANGE,
    }),
  ];

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <DeckGL
        layers={layers}
        viewState={viewState}
        onViewStateChange={e => setViewState(e.viewState)}
        controller={true}
      >
        <Map mapStyle={MAP_STYLE} reuseMaps />
      </DeckGL>
      
      <div className="absolute bottom-4 left-4 bg-black/50 text-white p-4 rounded-lg text-sm shadow-lg">
        <p className="font-bold text-lg">Global Air Quality View</p>
        <p>Source: NASA TEMPO & Ground Stations</p>
      </div>

      {isLoading && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white text-xl bg-black/50 p-4 rounded-lg">
            Loading Combined Air Quality Data...
        </div>
      )}
    </div>
  );
}

