"use client";

import { useState, useRef, useEffect } from 'react';
import { Mic, X, Rewind } from 'lucide-react';
// 1. Import the specific button components from your buttons library
import { PlayPauseButton, GeneratePodcastButton, PlayerControlButton } from './Buttons';

interface PodcastPlayerProps {
  onClose: () => void;
  latitude: number;
  longitude: number;
}

interface TranscriptLine {
  timestamp: number; // in seconds
  text: string;
}

export default function PodcastPlayer({ onClose, latitude, longitude }: PodcastPlayerProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [script, setScript] = useState<TranscriptLine[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Helper function to parse the script with timestamps from Gemini
  const parseScript = (rawScript: string): TranscriptLine[] => {
    return rawScript.split('\n').map(line => {
      const match = line.match(/\[(\d{2}):(\d{2})\]/);
      if (match) {
        const minutes = parseInt(match[1], 10);
        const seconds = parseInt(match[2], 10);
        const text = line.replace(/\[\d{2}:\d{2}\]\s*/, '').trim();
        return { timestamp: minutes * 60 + seconds, text };
      }
      return { timestamp: -1, text: line.trim() };
    }).filter(line => line.text !== '');
  };

  // Function to call the backend and generate the podcast
  const generatePodcast = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/podcast/generate", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: 1, lat: latitude, lon: longitude, question: "" }),
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      
      setAudioUrl(data.audio_url);
      setScript(parseScript(data.script));
    } catch (err: any) {
      console.error("Failed to generate podcast:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };
  
  const handleRewind = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
    }
  };

  const handleTimestampClick = (timestamp: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = timestamp;
      if (!isPlaying) {
        audioRef.current.play();
      }
    }
  };
  
  // Effect to listen for time updates from the audio player to highlight the transcript
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const timeUpdateHandler = () => setCurrentTime(audio.currentTime);
    audio.addEventListener('timeupdate', timeUpdateHandler);
    
    return () => audio.removeEventListener('timeupdate', timeUpdateHandler);
  }, [audioUrl]);


  return (
    <div className="fixed bottom-24 right-6 bg-gray-800 text-white rounded-lg shadow-2xl w-96 h-[70vh] flex flex-col z-40">
      <div className="flex justify-between items-center p-4 border-b border-gray-700">
        <h3 className="font-bold text-lg">Your Daily Briefing</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={24} /></button>
      </div>

      {error ? (
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-center">
            <p className="text-red-400">Error: {error}</p>
        </div>
      ) : isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Use the GeneratePodcastButton to show loading state */}
          <GeneratePodcastButton onClick={() => {}} isLoading={true} />
        </div>
      ) : audioUrl ? (
        <>
          <audio 
            ref={audioRef} 
            src={audioUrl} 
            onPlay={() => setIsPlaying(true)} 
            onPause={() => setIsPlaying(false)} 
            onEnded={() => setIsPlaying(false)} 
          />
          <div className="p-4 flex items-center justify-center space-x-8 border-b border-gray-700">
            {/* 2. Use the imported button components */}
            <PlayerControlButton onClick={handleRewind} ariaLabel="Rewind 10 seconds">
                <Rewind size={28} />
            </PlayerControlButton>
            <PlayPauseButton onClick={togglePlayPause} isPlaying={isPlaying} />
            <div className="w-8"></div> {/* Spacer */}
          </div>
          <div className="flex-1 p-4 space-y-3 overflow-y-auto">
            <h4 className="font-bold text-gray-200">Transcript</h4>
            {script.map((line, index) => {
              const nextTimestamp = script[index + 1]?.timestamp ?? Infinity;
              const isActive = currentTime >= line.timestamp && currentTime < nextTimestamp;
              
              return (
                <p 
                  key={index} 
                  onClick={() => line.timestamp !== -1 && handleTimestampClick(line.timestamp)} 
                  className={`transition-colors ${line.timestamp !== -1 ? 'cursor-pointer hover:text-blue-300' : ''} ${isActive ? 'text-blue-400 font-semibold' : 'text-gray-300'}`}
                >
                  {line.timestamp !== -1 && <span className="mr-2 text-gray-500 font-mono">{new Date(line.timestamp * 1000).toISOString().substr(14, 5)}</span>}
                  {line.text}
                </p>
              );
            })}
          </div>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <Mic size={48} className="mb-4 text-gray-500"/>
          <h4 className="text-xl font-semibold">Ready for your briefing?</h4>
          <p className="text-gray-400 mb-4">Get a personalized audio summary of today's air quality based on your profile and interests.</p>
          <GeneratePodcastButton onClick={generatePodcast} isLoading={isLoading} />
        </div>
      )}
    </div>
  );
}

