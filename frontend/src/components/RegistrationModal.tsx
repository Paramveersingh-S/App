"use client";

import React, { useState } from 'react';
import { Briefcase, Mail, Calendar, MapPin, Sun, Moon, Sparkles } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

interface RegistrationModalProps {
  onClose: () => void;
}

export default function RegistrationModal({ onClose }: RegistrationModalProps) {
  // --- STATE FOR ALL FORM FIELDS ---
  const [name, setName] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [persona, setPersona] = useState('');
  const [healthConditions, setHealthConditions] = useState<string[]>([]);
  const [workLocation, setWorkLocation] = useState('');
  const [scheduleDays, setScheduleDays] = useState<string[]>([]);
  const [scheduleTime, setScheduleTime] = useState('');
  const [podcastKeywords, setPodcastKeywords] = useState('');
  
  // --- STATE FOR UI CONTROL ---
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false); // Manages the two-step flow

  const handleCheckboxChange = (condition: string, list: string[], setList: Function) => {
    setList((prev: string[]) =>
      prev.includes(condition) ? prev.filter(c => c !== condition) : [...prev, condition]
    );
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    // In a real app, you would geocode the workLocation string to get lat/lon
    const userProfile = {
      name,
      age_group: ageGroup,
      persona,
      healthConditions,
      work_location: { lat: 28.61, lon: 77.20 }, // Placeholder for now
      outdoor_schedule: { days: scheduleDays, time: scheduleTime },
      podcast_keywords: podcastKeywords.split(',').map(k => k.trim()).filter(Boolean),
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/users/register", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userProfile),
      });
      if (!response.ok) throw new Error("Failed to save profile. Please try again.");

      const result = await response.json();
      console.log("Profile saved successfully:", result);
      setProfileSaved(true); // Switch to the Google Sign-In view

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handler for when Google Sign-In is successful
  const handleGoogleSuccess = async (credentialResponse: any) => {
    console.log("Google Sign-In Success, sending code to backend...");
    const authCode = credentialResponse.code;
    
    try {
        // Send the authorization code to your backend's callback endpoint
        const response = await fetch(`http://127.0.0.1:8000/api/v1/auth/google/callback?code=${authCode}`);
        if (!response.ok) throw new Error("Failed to verify Google authentication with backend.");

        console.log("Backend successfully processed Google auth code.");
        onClose(); // Close the modal after everything is done

    } catch (err: any) {
        console.error("Google callback error:", err);
        setError("Could not link Google account. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-800 text-white p-8 rounded-lg shadow-2xl w-full max-w-md">
        
        {profileSaved ? (
          // --- STEP 2: GOOGLE SIGN-IN ---
          <div className="text-center">
             <h2 className="text-3xl font-bold mb-2">Personalize Your Experience</h2>
             <p className="text-gray-400 mb-6">Connect your Google account to enable hyper-personalized features like calendar-aware alerts and podcast topics based on your interests.</p>
             <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => {
                  console.error('Google Login Failed');
                  setError("Google Sign-In failed. Please try again.");
                }}
                flow="auth-code" // This flow is required to get a code for your backend
                scope="https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/gmail.readonly"
              />
            </div>
            {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
             <button onClick={onClose} className="text-gray-400 text-sm mt-6 hover:text-white">Skip for now</button>
          </div>
        ) : (
          // --- STEP 1: INITIAL PROFILE FORM ---
          <>
            <h2 className="text-3xl font-bold mb-6">Create Your AURA Profile</h2>
            <form onSubmit={handleProfileSubmit} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                <input type="text" id="name" value={name} onChange={e => setName(e.target.value)} required className="w-full bg-gray-700 p-2 rounded-md"/>
              </div>
              
              <div>
                <label htmlFor="age-group" className="block text-sm font-medium text-gray-300 mb-1">Age Group</label>
                <select id="age-group" value={ageGroup} onChange={e => setAgeGroup(e.target.value)} className="w-full bg-gray-700 p-2 rounded-md">
                  <option value="">Select...</option>
                  <option value="Under 18">Under 18</option>
                  <option value="18-35">18-35</option>
                  <option value="36-55">36-55</option>
                  <option value="Over 55">Over 55</option>
                </select>
              </div>

              <div>
                <label htmlFor="persona" className="block text-sm font-medium text-gray-300 mb-1">Your Persona</label>
                <select id="persona" value={persona} onChange={e => setPersona(e.target.value)} className="w-full bg-gray-700 p-2 rounded-md">
                  <option value="">Select...</option>
                  <option value="Concerned Citizen">Concerned Citizen</option>
                  <option value="Athlete / Health Enthusiast">Athlete / Health Enthusiast</option>
                  <option value="Parent">Parent</option>
                  <option value="Policy Maker / Researcher">Policy Maker / Researcher</option>
                </select>
              </div>

              <div>
                <label htmlFor="work-location" className="block text-sm font-medium text-gray-300 mb-1">Primary Work/Home Location</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18}/>
                  <input type="text" id="work-location" value={workLocation} onChange={e => setWorkLocation(e.target.value)} className="w-full bg-gray-700 rounded-md pl-10 pr-3 py-2" placeholder="e.g., Connaught Place, New Delhi" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Typical Outdoor Activity Time</label>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  {['Weekdays', 'Weekends'].map(day => (
                    <label key={day} className="flex items-center space-x-2 cursor-pointer">
                      <input type="checkbox" onChange={() => handleCheckboxChange(day, scheduleDays, setScheduleDays)} className="h-4 w-4 rounded bg-gray-700 text-blue-500"/>
                      <span>{day}</span>
                    </label>
                  ))}
                </div>
                <select value={scheduleTime} onChange={e => setScheduleTime(e.target.value)} className="w-full bg-gray-700 p-2 rounded-md">
                  <option value="">Select time of day...</option>
                  <option value="morning">Morning (6am-12pm)</option>
                  <option value="afternoon">Afternoon (12pm-6pm)</option>
                  <option value="evening">Evening (6pm-10pm)</option>
                </select>
              </div>

              <div>
                <label htmlFor="podcast-keywords" className="block text-sm font-medium text-gray-300 mb-1">Podcast Interests</label>
                <div className="relative">
                  <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18}/>
                  <input type="text" id="podcast-keywords" value={podcastKeywords} onChange={e => setPodcastKeywords(e.target.value)} className="w-full bg-gray-700 rounded-md pl-10 pr-3 py-2" placeholder="e.g., technology, running, finance" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Health Sensitivities (Optional)</label>
                <div className="space-y-2">
                  {['Asthma', 'Allergies', 'Heart Condition', 'Pregnancy'].map(condition => (
                    <label key={condition} className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" onChange={() => handleCheckboxChange(condition, healthConditions, setHealthConditions)} className="h-5 w-5 rounded bg-gray-700 text-blue-500"/>
                      <span>{condition}</span>
                    </label>
                  ))}
                </div>
              </div>

              {error && <p className="text-red-400 text-sm text-center">{error}</p>}
              <button type="submit" disabled={isSubmitting} className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-3 rounded-md transition-colors mt-2">
                {isSubmitting ? 'Saving...' : 'Save & Continue to Personalize'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

