"use client";

import { useState } from "react";
import { ViewState } from "react-map-gl";
import DataPanel from "@/components/DataPanel";
import MapContainer from "@/components/MapContainer";
import RegistrationModal from "@/components/RegistrationModal";
import LeftSidebar from "@/components/LeftSidebar";
import ProfileModal from "@/components/ProfileModal";
import TimeScrubber from "@/components/TimeScrubber";
import { AuraGuideButton } from "@/components/Buttons";
import AuraGuideChat from "@/components/PodcastPlayer";
import Header from "@/components/Header";
import ForecastModal from "@/components/Forecast_modal";
import PolicySimulatorModal from "@/components/PolicySimulatorModal";
import CitizenScienceModal from "@/components/CitizenScienceModal";

// Define a flexible type for our location data to handle different API responses
export type LocationData = any; 

// Define a type for the empty map click event
interface CoordinateClickInfo {
  coordinate: [longitude: number, latitude: number];
}

// Define a type for the station pin click event
interface StationClickInfo {
    uid: number;
}

const INITIAL_VIEW_STATE: ViewState = {
    longitude: 77.2090, latitude: 28.6139,
    zoom: 4, pitch: 0, bearing: 0,
    padding: { top: 0, right: 0, bottom: 0, left: 0 }
};

export default function Home() {
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);
  const [viewState, setViewState] = useState<ViewState>(INITIAL_VIEW_STATE);
  const [activeLayer, setActiveLayer] = useState("aqi");
  const [timeOffset, setTimeOffset] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(true);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isForecastModalOpen, setIsForecastModalOpen] = useState(false);
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const [isCitizenModalOpen, setIsCitizenModalOpen] = useState(false);
  const [reportSubmittedCount, setReportSubmittedCount] = useState(0);

  // This intelligent click handler determines what was clicked and calls the correct API
  const handleMapClick = async (clickedInfo: StationClickInfo | CoordinateClickInfo) => {
    
    // Case 1: A station pin was clicked
    if ('uid' in clickedInfo) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/stations/details/${clickedInfo.uid}`);
        const stationDetails = await response.json();
        const now = new Date();
        setSelectedLocation({
          ...stationDetails,
          date: now.toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" }),
          time: now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true }),
        });
      } catch (error) { console.error("Failed to fetch station details:", error); }
    } 
    // Case 2: The empty map was clicked
    else if ('coordinate' in clickedInfo) {
      const [lon, lat] = clickedInfo.coordinate;
      try {
        // --- THIS IS THE KEY UPGRADE ---
        // Make a single POST request to get all unified context
        const contextResponse = await fetch("http://127.0.0.1:8000/api/v1/context/location", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lat, lon }),
        });
        const contextData = await contextResponse.json();
        
        // Fetch the other necessary data
        const nameResponse = await fetch(`http://127.0.0.1:8000/api/v1/location/name?lat=${lat}&lon=${lon}`);
        const nameData = await nameResponse.json();
        
        const now = new Date();
        const newLocationData: LocationData = {
          ...contextData.air_quality, // Use the air quality data from the context
          weather: contextData.weather, // Use the weather data from the context
          placeName: nameData.name || `Lat: ${lat.toFixed(2)}, Lon: ${lon.toFixed(2)}`,
          date: now.toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" }),
          time: now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true }),
        };
        setSelectedLocation(newLocationData);
      } catch (error) { console.error("Failed to fetch data on map click:", error); }
    }
  };
  
  const handleReportSubmitted = () => {
    setReportSubmittedCount(count => count + 1);
  };
  
  const handlePolicyClick = () => setIsPolicyModalOpen(true);
  const handleCitizenClick = () => setIsCitizenModalOpen(true);
  const handleForecastClick = () => setIsForecastModalOpen(true);

  return (
    <main className="flex h-screen w-screen bg-gray-900 overflow-hidden">
      {isModalOpen && <RegistrationModal onClose={() => setIsModalOpen(false)} />}
      {isProfileOpen && <ProfileModal onClose={() => setIsProfileOpen(false)} />}
      {isForecastModalOpen && <ForecastModal onClose={() => setIsForecastModalOpen(false)} lat={viewState.latitude} lon={viewState.longitude} />}
      {isPolicyModalOpen && <PolicySimulatorModal onClose={() => setIsPolicyModalOpen(false)} lat={viewState.latitude} lon={viewState.longitude} />}
      {isCitizenModalOpen && <CitizenScienceModal onClose={() => setIsCitizenModalOpen(false)} lat={viewState.latitude} lon={viewState.longitude} onReportSubmitted={handleReportSubmitted} />}

      <div className="flex-grow relative">
        <Header 
          onForecastClick={handleForecastClick}
          onPolicyClick={handlePolicyClick}
          onCitizenClick={handleCitizenClick}
        />
        <LeftSidebar
          activeLayer={activeLayer}
          onLayerChange={setActiveLayer}
          onProfileClick={() => setIsProfileOpen(true)}
        />
        <MapContainer
          onMapClick={handleMapClick}
          activeLayer={activeLayer}
          timeOffset={timeOffset}
          viewState={viewState}
          onViewStateChange={setViewState}
          reportSubmittedCount={reportSubmittedCount}
        />
        <TimeScrubber timeOffset={timeOffset} onTimeChange={setTimeOffset} />
      </div>

      <DataPanel locationData={selectedLocation} />

      {!isChatOpen && <AuraGuideButton onClick={() => setIsChatOpen(true)} />}
      {isChatOpen && (
        <AuraGuideChat
          onClose={() => setIsChatOpen(false)}
          latitude={viewState.latitude}
          longitude={viewState.longitude}
        />
      )}
    </main>
  );
}

