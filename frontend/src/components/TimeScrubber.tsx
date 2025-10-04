// /frontend/src/components/TimeScrubber.tsx
"use client";

interface TimeScrubberProps {
  timeOffset: number;
  onTimeChange: (offset: number) => void;
}

export default function TimeScrubber({ timeOffset, onTimeChange }: TimeScrubberProps) {
  const getLabel = (offset: number) => {
    if (offset === 0) return "Now";
    if (offset > 0) return `+${offset}h`;
    return `${offset}h`;
  };

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 w-1/2 max-w-2xl">
      <div className="bg-gray-800/80 backdrop-blur-sm p-4 rounded-lg shadow-lg text-white">
        <label htmlFor="time-scrubber" className="block text-center mb-2 font-medium">
          Forecast: {getLabel(timeOffset)}
        </label>
        <input
          id="time-scrubber"
          type="range"
          min="-24"
          max="48"
          step="1"
          value={timeOffset}
          onChange={e => onTimeChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>-24h</span>
          <span>Now</span>
          <span>+48h</span>
        </div>
      </div>
    </div>
  );
}