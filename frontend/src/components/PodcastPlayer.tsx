"use client";

import { useState, useEffect, useRef } from 'react';
import { Play, Pause, X, Download, Loader2 } from 'lucide-react';
import { usePodcast } from '@/contexts/PodcastContext';

interface Question {
  timestamp: number;
  question: string;
}

interface PodcastPlayerProps {
  podcastId?: string;
  onClose: () => void;
  latitude?: number;
  longitude?: number;
}

export default function PodcastPlayer({ podcastId: propPodcastId, onClose }: PodcastPlayerProps) {
  const { updatePodcast, podcasts } = usePodcast();
  const [podcastId, setPodcastId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [audioUrl, setAudioUrl] = useState('');
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const id = propPodcastId || podcasts.find(p => p.status === 'completed')?.id;
    if (id) {
      setPodcastId(id);
      loadPodcast(id);
    } else {
      setLoading(false);
    }
  }, [propPodcastId, podcasts]);

  const loadPodcast = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:3001/get-podcast/${id}`);
      const data = await response.json();

      console.log('Podcast data:', data);
      if (data.questions) {
        console.log('Questions loaded:', data.questions);
        setQuestions(data.questions);
      }

      setAudioUrl(`http://localhost:3001/get-full-audio/${id}`);
      setLoading(false);
    } catch (error) {
      console.error('Error loading podcast:', error);
      setLoading(false);
    }
  };

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentQuestions = () => {
    return Array.isArray(questions) ? questions.filter(q => Math.abs(q.timestamp - currentTime) < 10) : [];
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <div className="bg-gray-800 text-white p-8 rounded-lg">
          <Loader2 size={40} className="animate-spin" />
        </div>
      </div>
    );
  }

  if (!podcastId) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-gray-800 text-white p-8 rounded-lg text-center" onClick={e => e.stopPropagation()}>
          <p className="text-gray-300 mb-4">No completed podcasts available</p>
          <button onClick={onClose} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md">
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-pink-900 z-50 flex flex-col">
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Header */}
      <div className="flex justify-between items-center p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
            <Play size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">AURA Podcast</h1>
            <p className="text-sm text-gray-300">Your personalized audio experience</p>
          </div>
        </div>
        <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
          <X size={32} />
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 pb-20">
        {/* Album Art / Visualizer */}
        <div className="w-80 h-80 rounded-3xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-xl border border-white/10 mb-12 flex items-center justify-center shadow-2xl">
          <div className={`w-32 h-32 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center ${isPlaying ? 'animate-pulse' : ''}`}>
            {isPlaying ? <Pause size={48} className="text-white" /> : <Play size={48} className="text-white ml-2" />}
          </div>
        </div>

        {/* Time Display */}
        <div className="text-center mb-8">
          <div className="text-6xl font-bold text-white mb-2">{formatTime(currentTime)}</div>
          <div className="text-xl text-gray-300">of {formatTime(duration)}</div>
        </div>

        {/* Progress Bar */}
        <div className="w-full max-w-3xl mb-8">
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-2 bg-white/20 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:cursor-pointer [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-white [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
          />
        </div>

        {/* Controls */}
        <div className="flex items-center gap-6 mb-12">
          <button
            onClick={togglePlay}
            className="w-20 h-20 rounded-full bg-white text-purple-900 hover:scale-110 transition-transform shadow-2xl flex items-center justify-center"
          >
            {isPlaying ? <Pause size={36} /> : <Play size={36} className="ml-1" />}
          </button>
          <a
            href={`http://localhost:3001/download-podcast/${podcastId}`}
            className="w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-xl text-white transition-all flex items-center justify-center"
          >
            <Download size={24} />
          </a>
        </div>

        {/* Questions */}
        {Array.isArray(questions) && questions.length > 0 && (
          <div className="w-full max-w-3xl bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">💡 Questions ({getCurrentQuestions().length > 0 ? 'Current' : 'All'})</h3>
            <div className="space-y-3">
              {(getCurrentQuestions().length > 0 ? getCurrentQuestions() : (Array.isArray(questions) ? questions.slice(0, 3) : [])).map((q, idx) => (
                <div key={idx} className="text-white/90 text-lg bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-colors">
                  <div className="text-xs text-white/60 mb-1">@{formatTime(q.timestamp)}</div>
                  {q.question}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
