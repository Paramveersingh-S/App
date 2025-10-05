"use client";

import { useState } from 'react';
import { Play, Trash2, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { usePodcast } from '@/contexts/PodcastContext';
import PodcastPlayer from './PodcastPlayer';

export default function PodcastList() {
  const { podcasts, removePodcast } = usePodcast();
  const [selectedPodcast, setSelectedPodcast] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (confirm('Delete this podcast?')) {
      try {
        await fetch(`http://localhost:3001/podcast/${id}`, { method: 'DELETE' });
        removePodcast(id);
      } catch (error) {
        console.error('Error deleting podcast:', error);
      }
    }
  };

  if (podcasts.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        No podcasts generated yet
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {podcasts.map(podcast => (
          <div key={podcast.id} className="bg-gray-700 p-4 rounded-lg flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                {podcast.status === 'generating' && <Loader2 size={16} className="animate-spin text-blue-400" />}
                {podcast.status === 'completed' && <CheckCircle size={16} className="text-green-400" />}
                {podcast.status === 'failed' && <XCircle size={16} className="text-red-400" />}
                <span className="font-medium">{new Date(podcast.created_at).toLocaleString()}</span>
              </div>
              {podcast.progress !== undefined && podcast.status === 'generating' && (
                <div className="mt-2 bg-gray-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${podcast.progress}%` }}
                  />
                </div>
              )}
              {podcast.topics && podcast.topics.length > 0 && (
                <div className="flex gap-2 mt-2">
                  {podcast.topics.slice(0, 3).map((topic, idx) => (
                    <span key={idx} className="text-xs bg-blue-600/50 px-2 py-1 rounded">
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              {podcast.status === 'completed' && (
                <button
                  onClick={() => setSelectedPodcast(podcast.id)}
                  className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded"
                >
                  <Play size={18} />
                </button>
              )}
              <button
                onClick={() => handleDelete(podcast.id)}
                className="bg-red-600 hover:bg-red-700 text-white p-2 rounded"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedPodcast && (
        <PodcastPlayer
          podcastId={selectedPodcast}
          onClose={() => setSelectedPodcast(null)}
        />
      )}
    </>
  );
}
