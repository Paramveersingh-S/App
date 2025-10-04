"use client";

import React from 'react';
import { Play, Pause, Rewind, Loader2, Bot } from 'lucide-react';

// --- 1. The Floating Action Button to open the Podcast Player ---
interface AuraGuideButtonProps {
  onClick: () => void;
}

export const AuraGuideButton = ({ onClick }: AuraGuideButtonProps) => (
  <button
    onClick={onClick}
    className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-transform hover:scale-110"
    aria-label="Open AURA Daily Briefing"
  >
    <Bot size={28} />
  </button>
);

// --- 2. A Generic Control Button (used for Rewind) ---
interface PlayerControlButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  ariaLabel: string;
  disabled?: boolean;
}

export const PlayerControlButton = ({ onClick, children, ariaLabel, disabled = false }: PlayerControlButtonProps) => (
  <button
    onClick={onClick}
    className="text-gray-400 hover:text-white disabled:text-gray-600 transition-colors"
    aria-label={ariaLabel}
    disabled={disabled}
  >
    {children}
  </button>
);

// --- 3. The Main Play/Pause Button ---
interface PlayPauseButtonProps {
  onClick: () => void;
  isPlaying: boolean;
  disabled?: boolean;
}

export const PlayPauseButton = ({ onClick, isPlaying, disabled = false }: PlayPauseButtonProps) => (
  <button
    onClick={onClick}
    className="bg-blue-600 text-white p-4 rounded-full shadow-lg transform hover:scale-110 transition-transform disabled:bg-gray-500 disabled:scale-100"
    aria-label={isPlaying ? "Pause podcast" : "Play podcast"}
    disabled={disabled}
  >
    {isPlaying ? <Pause size={32} /> : <Play size={32} className="ml-1" />}
  </button>
);

// --- 4. The "Generate Podcast" Button ---
interface GeneratePodcastButtonProps {
  onClick: () => void;
  isLoading: boolean;
}

export const GeneratePodcastButton = ({ onClick, isLoading }: GeneratePodcastButtonProps) => (
   <button 
      onClick={onClick} 
      className="bg-blue-600 px-6 py-3 rounded-full font-bold hover:bg-blue-700 transition-colors disabled:bg-gray-500 flex items-center justify-center"
      disabled={isLoading}
    >
      {isLoading ? (
        <>
          <Loader2 className="animate-spin mr-2" size={20} />
          Generating...
        </>
      ) : (
        'Generate My Daily Briefing'
      )}
    </button>
);

