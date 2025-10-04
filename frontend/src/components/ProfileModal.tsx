"use client";

import { X } from "lucide-react";

// The component receives an 'onClose' function as a prop to handle closing itself
interface ProfileModalProps {
  onClose: () => void;
}

// In a real app, this data would come from your backend or a state management store
const mockUserData = {
  name: 'Paramveer',
  healthConditions: ['Asthma'],
};

export default function ProfileModal({ onClose }: ProfileModalProps) {
  return (
    // The outer div is a semi-transparent backdrop that closes the modal when clicked
    <div 
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" 
      onClick={onClose}
    >
      {/* This inner div is the modal content. 
        e.stopPropagation() prevents a click inside the modal from closing it.
      */}
      <div 
        className="bg-gray-800 text-white p-8 rounded-lg shadow-2xl w-full max-w-md" 
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold">Your Profile</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Close profile"
          >
            <X size={28} />
          </button>
        </div>
        
        <div className="space-y-6">
          <div>
            <p className="text-sm text-gray-400">Name</p>
            <p className="text-lg font-medium">{mockUserData.name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Health Sensitivities</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {mockUserData.healthConditions.length > 0 ? (
                mockUserData.healthConditions.map(condition => (
                  <span key={condition} className="bg-blue-600/50 text-blue-100 px-3 py-1 rounded-full text-sm font-medium">
                    {condition}
                  </span>
                ))
              ) : (
                <p className="text-gray-500 italic">None specified.</p>
              )}
            </div>
          </div>
        </div>
        
        <button className="mt-8 w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-md transition-colors">
          Edit Profile
        </button>
      </div>
    </div>
  );
}