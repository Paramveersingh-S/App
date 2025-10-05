"use client";

import { useState } from 'react';
import { X, Plus, Trash2, Upload } from 'lucide-react';

interface PersonalizationEntry {
  id: string;
  category: string;
  detail: string;
  relevance: string;
}

interface ChatGPTImportModalProps {
  onClose: () => void;
}

import { useUser } from '@/contexts/UserContext';

export default function ChatGPTImportModal({ onClose }: ChatGPTImportModalProps) {
  const { addPersonalization, user } = useUser();
  const [csvText, setCsvText] = useState('');
  const [entries, setEntries] = useState<PersonalizationEntry[]>(user?.personalization || []);
  const [showInstructions, setShowInstructions] = useState(!user?.personalization || user.personalization.length === 0);
  const [newEntry, setNewEntry] = useState({ category: '', detail: '', relevance: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const parseCSV = () => {
    try {
      const lines = csvText.trim().split('\n').filter(line => line.trim());
      if (lines.length < 2) return;
      
      const parsed: PersonalizationEntry[] = [];
      for (let i = 1; i < lines.length; i++) {
        const match = lines[i].match(/(?:^|,)(?:"([^"]*)"|([^,]*))/g);
        if (match && match.length >= 3) {
          const values = match.map(v => v.replace(/^,?"?|"?$/g, '').trim());
          parsed.push({
            id: `${Date.now()}-${i}`,
            category: values[0] || '',
            detail: values[1] || '',
            relevance: values[2] || ''
          });
        }
      }
      setEntries(parsed);
      setShowInstructions(false);
    } catch (error) {
      alert('Failed to parse CSV. Please check the format.');
    }
  };

  const addEntry = () => {
    if (!newEntry.category || !newEntry.detail) return;
    setEntries([...entries, { ...newEntry, id: `${Date.now()}` }]);
    setNewEntry({ category: '', detail: '', relevance: '' });
  };

  const removeEntry = (id: string) => {
    setEntries(entries.filter(e => e.id !== id));
  };

  const saveToLocalStorage = () => {
    setIsSubmitting(true);
    try {
      const newEntries = entries.filter(e => !user?.personalization.find(p => p.id === e.id));
      addPersonalization(newEntries);
      alert('Personalization data saved successfully!');
      onClose();
    } catch (error) {
      alert('Failed to save personalization data');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-800 text-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold">Import ChatGPT Memory</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {showInstructions && (
            <div className="bg-gray-900 p-4 rounded-lg mb-6">
              <h3 className="font-bold mb-2">Instructions:</h3>
              <ol className="text-sm text-gray-300 space-y-2 list-decimal list-inside">
                <li>Go to ChatGPT and paste this prompt:</li>
              </ol>
              <div className="bg-gray-950 p-3 rounded mt-2 text-xs overflow-x-auto">
                <code className="text-green-400">
                  You are tasked with exporting all stored memories about the user into a CSV file format.
                  <br/><br/>
                  1. Extract only the **relevant personalization data** that would help a podcast generator create content tailored to the user.
                  <br/>- Include preferences, habits, learning style, tone/style preferences, interests, hobbies, important life details, and contextual background.
                  <br/>- Exclude sensitive or non-relevant info (e.g., precise addresses, private identifiers).
                  <br/><br/>
                  2. Output should be **strictly in CSV format**, with no explanations or extra commentary.
                  <br/><br/>
                  3. Use the following column structure for CSV:
                  <br/>"Category","Detail","Relevance_for_Podcast"
                  <br/><br/>
                  4. Ensure proper CSV escaping and every row represents one discrete memory item.
                  <br/><br/>
                  Now, generate the CSV. Do not output anything except the CSV.
                </code>
              </div>
              <ol start={2} className="text-sm text-gray-300 space-y-2 list-decimal list-inside mt-3">
                <li>Copy the CSV response from ChatGPT</li>
                <li>Paste it in the text area below</li>
              </ol>
            </div>
          )}

          {showInstructions ? (
            <div>
              <label className="block text-sm font-medium mb-2">Paste CSV from ChatGPT:</label>
              <textarea
                value={csvText}
                onChange={e => setCsvText(e.target.value)}
                className="w-full bg-gray-700 rounded-md p-3 text-sm font-mono"
                rows={10}
                placeholder='"Category","Detail","Relevance_for_Podcast"&#10;"Personality","Prefers concise explanations","Keep podcast segments brief"'
              />
              <button
                onClick={parseCSV}
                className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md flex items-center gap-2"
              >
                <Upload size={18} />
                Parse CSV
              </button>
            </div>
          ) : (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">Personalization Entries ({entries.length})</h3>
                <button
                  onClick={() => setShowInstructions(true)}
                  className="text-sm text-blue-400 hover:text-blue-300"
                >
                  Import More
                </button>
              </div>

              <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
                {entries.map(entry => (
                  <div key={entry.id} className="bg-gray-700 p-3 rounded-md flex justify-between items-start gap-3">
                    <div className="flex-1">
                      <div className="flex gap-2 items-center mb-1">
                        <span className="bg-blue-600/50 text-blue-100 px-2 py-0.5 rounded text-xs font-medium">
                          {entry.category}
                        </span>
                      </div>
                      <p className="text-sm">{entry.detail}</p>
                      {entry.relevance && (
                        <p className="text-xs text-gray-400 mt-1">{entry.relevance}</p>
                      )}
                    </div>
                    <button
                      onClick={() => removeEntry(entry.id)}
                      className="text-red-400 hover:text-red-300 flex-shrink-0"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>

              <div className="bg-gray-900 p-4 rounded-lg">
                <h4 className="font-bold mb-3 text-sm">Add Custom Entry</h4>
                <div className="grid grid-cols-3 gap-2 mb-2">
                  <input
                    type="text"
                    value={newEntry.category}
                    onChange={e => setNewEntry({ ...newEntry, category: e.target.value })}
                    placeholder="Category"
                    className="bg-gray-700 p-2 rounded text-sm"
                  />
                  <input
                    type="text"
                    value={newEntry.detail}
                    onChange={e => setNewEntry({ ...newEntry, detail: e.target.value })}
                    placeholder="Detail"
                    className="bg-gray-700 p-2 rounded text-sm"
                  />
                  <input
                    type="text"
                    value={newEntry.relevance}
                    onChange={e => setNewEntry({ ...newEntry, relevance: e.target.value })}
                    placeholder="Relevance"
                    className="bg-gray-700 p-2 rounded text-sm"
                  />
                </div>
                <button
                  onClick={addEntry}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm flex items-center gap-2"
                >
                  <Plus size={16} />
                  Add Entry
                </button>
              </div>

              <button
                onClick={saveToLocalStorage}
                disabled={isSubmitting || entries.length === 0}
                className="w-full mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-3 rounded-md"
              >
                {isSubmitting ? 'Saving...' : `Save ${entries.length} Entries`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
