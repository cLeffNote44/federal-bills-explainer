'use client';

import { useState, useEffect } from 'react';
import { AdvancedFilterValues } from './AdvancedFilterPanel';

interface FilterPreset {
  id: string;
  name: string;
  description?: string;
  filters: AdvancedFilterValues;
  created_at: string;
}

interface SavedFilterPresetsProps {
  currentFilters: AdvancedFilterValues;
  onApplyPreset: (filters: AdvancedFilterValues) => void;
}

export default function SavedFilterPresets({
  currentFilters,
  onApplyPreset,
}: SavedFilterPresetsProps) {
  const [presets, setPresets] = useState<FilterPreset[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = () => {
    try {
      const saved = localStorage.getItem('filter_presets');
      if (saved) {
        setPresets(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading presets:', error);
    }
  };

  const savePreset = () => {
    if (!presetName.trim()) return;

    const newPreset: FilterPreset = {
      id: Date.now().toString(),
      name: presetName,
      description: presetDescription,
      filters: currentFilters,
      created_at: new Date().toISOString(),
    };

    const updatedPresets = [...presets, newPreset];
    setPresets(updatedPresets);

    try {
      localStorage.setItem('filter_presets', JSON.stringify(updatedPresets));
    } catch (error) {
      console.error('Error saving preset:', error);
    }

    setPresetName('');
    setPresetDescription('');
    setShowSaveDialog(false);
  };

  const deletePreset = (id: string) => {
    const updatedPresets = presets.filter((p) => p.id !== id);
    setPresets(updatedPresets);

    try {
      localStorage.setItem('filter_presets', JSON.stringify(updatedPresets));
    } catch (error) {
      console.error('Error deleting preset:', error);
    }
  };

  const getFilterSummary = (filters: AdvancedFilterValues): string => {
    const parts: string[] = [];

    if (filters.congress && filters.congress.length > 0) {
      parts.push(`${filters.congress.length} congress`);
    }
    if (filters.bill_type && filters.bill_type.length > 0) {
      parts.push(`${filters.bill_type.length} type`);
    }
    if (filters.status && filters.status.length > 0) {
      parts.push(`${filters.status.length} status`);
    }
    if (filters.sponsor_party && filters.sponsor_party.length > 0) {
      parts.push(`${filters.sponsor_party.length} party`);
    }
    if (filters.has_public_law) {
      parts.push('public law');
    }

    return parts.length > 0 ? parts.join(', ') : 'No filters';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Saved Filters</h2>
        <button
          onClick={() => setShowSaveDialog(true)}
          className="px-3 py-1 bg-fed-blue text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Save Current
        </button>
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Save Filter Preset</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Preset Name *</label>
              <input
                type="text"
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                placeholder="e.g., Recent Healthcare Bills"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fed-blue"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Description (optional)</label>
              <input
                type="text"
                value={presetDescription}
                onChange={(e) => setPresetDescription(e.target.value)}
                placeholder="e.g., Healthcare bills from 118th Congress"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fed-blue"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={savePreset}
                disabled={!presetName.trim()}
                className="flex-1 px-4 py-2 bg-fed-blue text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setShowSaveDialog(false);
                  setPresetName('');
                  setPresetDescription('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Presets List */}
      {presets.length > 0 ? (
        <div className="space-y-3">
          {presets.map((preset) => (
            <div
              key={preset.id}
              className="p-4 rounded-lg border border-gray-200 hover:border-fed-blue transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">{preset.name}</h4>
                  {preset.description && (
                    <p className="text-xs text-gray-600 mt-1">{preset.description}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {getFilterSummary(preset.filters)}
                  </p>
                </div>
                <div className="flex gap-2 ml-3">
                  <button
                    onClick={() => onApplyPreset(preset.filters)}
                    className="px-3 py-1 bg-fed-blue text-white rounded text-xs font-medium hover:bg-blue-700 transition-colors"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => deletePreset(preset.id)}
                    className="px-3 py-1 border border-gray-300 text-gray-700 rounded text-xs font-medium hover:bg-gray-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
          <p className="mt-2 text-sm text-gray-600">No saved filter presets</p>
          <p className="text-xs text-gray-500 mt-1">
            Save your current filters for quick access later
          </p>
        </div>
      )}
    </div>
  );
}
