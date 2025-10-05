"use client";

import { useState, useEffect } from 'react';
import { Mic, Loader2, X, RefreshCw } from 'lucide-react';
import { useUser } from '@/contexts/UserContext';
import { usePodcast } from '@/contexts/PodcastContext';

interface PodcastGeneratorProps {
  onClose: () => void;
}

export default function PodcastGenerator({ onClose }: PodcastGeneratorProps) {
  const { user } = useUser();
  const { addPodcast, updatePodcast, podcasts } = usePodcast();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [showList, setShowList] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);

  useEffect(() => {
    console.log('Podcasts in component:', podcasts);
  }, [podcasts]);

  useEffect(() => {
    const checkPodcasts = async () => {
      for (const podcast of podcasts) {
        if (podcast.status === 'generating') {
          try {
            const response = await fetch(`http://localhost:3001/status/${podcast.id}`);
            const data = await response.json();
            if (data.status === 'COMPLETED') {
              const podcastResponse = await fetch(`http://localhost:3001/get-podcast/${podcast.id}`);
              const podcastData = await podcastResponse.json();
              updatePodcast(podcast.id, {
                status: 'completed',
                progress: 100,
                topics: podcastData.topics || [],
                duration: podcastData.duration
              });
            } else if (data.status === 'FAILED') {
              updatePodcast(podcast.id, { status: 'failed', progress: 100 });
            } else {
              pollStatus(podcast.id);
            }
          } catch (error) {
            console.error('Error checking podcast status:', error);
          }
        } else if (podcast.status === 'completed' && !podcast.topics) {
          try {
            const response = await fetch(`http://localhost:3001/get-podcast/${podcast.id}`);
            const data = await response.json();
            updatePodcast(podcast.id, {
              topics: data.topics || [],
              duration: data.duration
            });
          } catch (error) {
            console.error('Error fetching podcast metadata:', error);
          }
        }
      }
    };
    checkPodcasts();
  }, []);

  const handleGenerate = async () => {
    if (!user) return;

    setIsGenerating(true);
    setError('');

    try {
      console.log('User data:', user);
      const payload = {
        user_preferences: {
          tone: user.persona || 'casual',
          name: user.name
        },
        interests: user.podcast_keywords || [],
        home_location: user.home_location,
        work_location: user.work_location,
        extra: {
          health_conditions: user.healthConditions,
          personalization: user.personalization
        }
      };
      console.log('Payload being sent:', payload);

      const response = await fetch('http://localhost:3001/generate-podcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to generate podcast');

      const data = await response.json();
      console.log('Response from API:', data);
      
      const newPodcast = {
        id: data.id,
        created_at: new Date().toISOString(),
        status: 'generating' as const,
        progress: 0
      };
      console.log('Adding new podcast:', newPodcast);
      addPodcast(newPodcast);
      console.log('Podcast added, starting poll');

      // Start polling for status
      pollStatus(data.id);
      setShowList(true);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const pollStatus = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:3001/status/${jobId}`);
        const data = await response.json();

        updatePodcast(jobId, {
          status: data.status === 'COMPLETED' ? 'completed' : data.status === 'FAILED' ? 'failed' : 'generating',
          progress: data.progress
        });

        if (data.status === 'COMPLETED') {
          clearInterval(interval);
          const podcastResponse = await fetch(`http://localhost:3001/get-podcast/${jobId}`);
          const podcastData = await podcastResponse.json();
          updatePodcast(jobId, {
            topics: podcastData.topics || [],
            duration: podcastData.duration
          });
        } else if (data.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    }, 3000);
  };

  const handleRefresh = async (podcastId: string) => {
    setRefreshing(podcastId);
    try {
      const response = await fetch(`http://localhost:3001/status/${podcastId}`);
      const data = await response.json();
      if (data.status === 'COMPLETED') {
        const podcastResponse = await fetch(`http://localhost:3001/get-podcast/${podcastId}`);
        const podcastData = await podcastResponse.json();
        updatePodcast(podcastId, {
          status: 'completed',
          progress: 100,
          topics: podcastData.topics || [],
          duration: podcastData.duration
        });
      } else if (data.status === 'FAILED') {
        updatePodcast(podcastId, { status: 'failed', progress: 100 });
      } else {
        updatePodcast(podcastId, {
          status: 'generating',
          progress: data.progress
        });
      }
    } catch (error) {
      console.error('Error refreshing podcast:', error);
    } finally {
      setRefreshing(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-gray-800 text-white p-8 rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold">Podcasts</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={28} />
          </button>
        </div>

        {showList ? (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-gray-300">Your generated podcasts</p>
              <button
                onClick={() => setShowList(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center gap-2"
              >
                <Mic size={18} />
                Generate New
              </button>
            </div>
            
            {podcasts.length === 0 ? (
              <div className="text-center text-gray-400 py-8">
                <p>No podcasts yet</p>
                <button
                  onClick={() => setShowList(false)}
                  className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md"
                >
                  Generate Your First Podcast
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {podcasts.map(podcast => (
                  <div key={podcast.id} className="bg-gray-700 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium">{new Date(podcast.created_at).toLocaleString()}</p>
                        <p className="text-sm text-gray-400 capitalize">{podcast.status}</p>
                        {podcast.progress !== undefined && podcast.status === 'generating' && (
                          <div className="mt-2 bg-gray-600 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all"
                              style={{ width: `${podcast.progress}%` }}
                            />
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleRefresh(podcast.id)}
                        disabled={refreshing === podcast.id}
                        className="ml-3 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-white p-2 rounded"
                        title="Refresh status"
                      >
                        <RefreshCw size={18} className={refreshing === podcast.id ? 'animate-spin' : ''} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <button
              onClick={() => setShowList(true)}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              ← Back to list
            </button>
            
            <p className="text-gray-300">
              Generate a personalized podcast based on your profile, interests, and current air quality conditions.
            </p>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button
              onClick={handleGenerate}
              disabled={isGenerating || !user}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-3 rounded-md flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Mic size={20} />
                  Generate Podcast Now
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
