'use client';

import { useState, useEffect } from 'react';

export interface AdvancedFilterValues {
  congress?: number[];
  bill_type?: string[];
  status?: string[];
  sponsor_party?: string[];
  sponsor_state?: string[];
  policy_area?: string;
  has_public_law?: boolean;
  date_from?: string;
  date_to?: string;
  sortBy?: string;
  sortOrder?: string;
}

interface AdvancedFilterPanelProps {
  values: AdvancedFilterValues;
  onChange: (values: AdvancedFilterValues) => void;
  onApply: () => void;
  onReset: () => void;
  showFacets?: boolean;
}

interface Facet {
  value: string | number;
  count: number;
}

interface Facets {
  congress?: Facet[];
  bill_type?: Facet[];
  status?: Facet[];
  sponsor_party?: Facet[];
  sponsor_state?: Facet[];
  policy_area?: Facet[];
}

export default function AdvancedFilterPanel({
  values,
  onChange,
  onApply,
  onReset,
  showFacets = true,
}: AdvancedFilterPanelProps) {
  const [facets, setFacets] = useState<Facets>({});
  const [loadingFacets, setLoadingFacets] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch facets when filters change
  useEffect(() => {
    if (showFacets) {
      fetchFacets();
    }
  }, []);

  const fetchFacets = async () => {
    try {
      setLoadingFacets(true);
      const response = await fetch(`${API_URL}/search/facets`);
      const data = await response.json();
      setFacets(data);
    } catch (error) {
      console.error('Error fetching facets:', error);
    } finally {
      setLoadingFacets(false);
    }
  };

  const handleMultiSelectChange = (field: keyof AdvancedFilterValues, value: string | number, checked: boolean) => {
    const currentValues = (values[field] as any[]) || [];
    let newValues: any[];

    if (checked) {
      newValues = [...currentValues, value];
    } else {
      newValues = currentValues.filter(v => v !== value);
    }

    onChange({
      ...values,
      [field]: newValues.length > 0 ? newValues : undefined,
    });
  };

  const isSelected = (field: keyof AdvancedFilterValues, value: string | number): boolean => {
    const fieldValues = values[field] as any[];
    return fieldValues ? fieldValues.includes(value) : false;
  };

  const getActiveFilterCount = (): number => {
    let count = 0;
    if (values.congress && values.congress.length > 0) count++;
    if (values.bill_type && values.bill_type.length > 0) count++;
    if (values.status && values.status.length > 0) count++;
    if (values.sponsor_party && values.sponsor_party.length > 0) count++;
    if (values.sponsor_state && values.sponsor_state.length > 0) count++;
    if (values.policy_area) count++;
    if (values.has_public_law) count++;
    if (values.date_from || values.date_to) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          Filters
          {activeCount > 0 && (
            <span className="ml-2 px-2 py-1 bg-fed-blue text-white text-xs rounded-full">
              {activeCount}
            </span>
          )}
        </h2>
        <button
          onClick={onReset}
          className="text-sm text-fed-blue hover:text-blue-700 font-medium"
        >
          Clear All
        </button>
      </div>

      <div className="space-y-6">
        {/* Congress Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Congress
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {loadingFacets ? (
              <div className="text-sm text-gray-500">Loading...</div>
            ) : facets.congress && facets.congress.length > 0 ? (
              facets.congress.map((facet) => (
                <label key={facet.value} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                  <input
                    type="checkbox"
                    checked={isSelected('congress', facet.value as number)}
                    onChange={(e) => handleMultiSelectChange('congress', facet.value as number, e.target.checked)}
                    className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
                  />
                  <span className="text-sm text-gray-700 flex-1">
                    {facet.value}th Congress
                  </span>
                  <span className="text-xs text-gray-500">{facet.count}</span>
                </label>
              ))
            ) : (
              [118, 117, 116, 115].map((congress) => (
                <label key={congress} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                  <input
                    type="checkbox"
                    checked={isSelected('congress', congress)}
                    onChange={(e) => handleMultiSelectChange('congress', congress, e.target.checked)}
                    className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
                  />
                  <span className="text-sm text-gray-700">{congress}th Congress</span>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Bill Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Bill Type
          </label>
          <div className="space-y-2">
            {[
              { value: 'hr', label: 'House Bill (HR)' },
              { value: 's', label: 'Senate Bill (S)' },
              { value: 'hjres', label: 'House Joint Resolution' },
              { value: 'sjres', label: 'Senate Joint Resolution' },
            ].map((type) => (
              <label key={type.value} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                <input
                  type="checkbox"
                  checked={isSelected('bill_type', type.value)}
                  onChange={(e) => handleMultiSelectChange('bill_type', type.value, e.target.checked)}
                  className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
                />
                <span className="text-sm text-gray-700 flex-1">{type.label}</span>
                {showFacets && facets.bill_type && facets.bill_type.find(f => f.value === type.value) && (
                  <span className="text-xs text-gray-500">
                    {facets.bill_type.find(f => f.value === type.value)?.count}
                  </span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Status
          </label>
          <div className="space-y-2">
            {[
              { value: 'introduced', label: 'Introduced' },
              { value: 'passed', label: 'Passed' },
              { value: 'enacted', label: 'Enacted' },
              { value: 'became-law', label: 'Became Law' },
            ].map((status) => (
              <label key={status.value} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                <input
                  type="checkbox"
                  checked={isSelected('status', status.value)}
                  onChange={(e) => handleMultiSelectChange('status', status.value, e.target.checked)}
                  className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
                />
                <span className="text-sm text-gray-700 flex-1">{status.label}</span>
                {showFacets && facets.status && facets.status.find(f => f.value === status.value) && (
                  <span className="text-xs text-gray-500">
                    {facets.status.find(f => f.value === status.value)?.count}
                  </span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Sponsor Party Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Sponsor Party
          </label>
          <div className="space-y-2">
            {[
              { value: 'D', label: 'Democratic' },
              { value: 'R', label: 'Republican' },
              { value: 'I', label: 'Independent' },
            ].map((party) => (
              <label key={party.value} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                <input
                  type="checkbox"
                  checked={isSelected('sponsor_party', party.value)}
                  onChange={(e) => handleMultiSelectChange('sponsor_party', party.value, e.target.checked)}
                  className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
                />
                <span className="text-sm text-gray-700 flex-1">{party.label}</span>
                {showFacets && facets.sponsor_party && facets.sponsor_party.find(f => f.value === party.value) && (
                  <span className="text-xs text-gray-500">
                    {facets.sponsor_party.find(f => f.value === party.value)?.count}
                  </span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Date Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Introduced Date
          </label>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-600 mb-1 block">From</label>
              <input
                type="date"
                value={values.date_from || ''}
                onChange={(e) => onChange({ ...values, date_from: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fed-blue"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 mb-1 block">To</label>
              <input
                type="date"
                value={values.date_to || ''}
                onChange={(e) => onChange({ ...values, date_to: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fed-blue"
              />
            </div>
          </div>
        </div>

        {/* Public Law Filter */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
            <input
              type="checkbox"
              checked={values.has_public_law || false}
              onChange={(e) => onChange({ ...values, has_public_law: e.target.checked || undefined })}
              className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
            />
            <span className="text-sm font-medium text-gray-700">Bills that became law</span>
          </label>
        </div>

        {/* Sort Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Sort By
          </label>
          <select
            value={values.sortBy || 'relevance'}
            onChange={(e) => onChange({ ...values, sortBy: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fed-blue"
          >
            <option value="relevance">Relevance</option>
            <option value="date">Date Introduced</option>
            <option value="updated">Date Updated</option>
            <option value="cosponsors">Cosponsors</option>
            <option value="congress">Congress</option>
          </select>
        </div>

        {/* Sort Order */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Sort Order
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => onChange({ ...values, sortOrder: 'desc' })}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                values.sortOrder === 'desc' || !values.sortOrder
                  ? 'bg-fed-blue text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Descending
            </button>
            <button
              onClick={() => onChange({ ...values, sortOrder: 'asc' })}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                values.sortOrder === 'asc'
                  ? 'bg-fed-blue text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Ascending
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t border-gray-200 flex gap-3">
          <button
            onClick={onReset}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
          <button
            onClick={onApply}
            className="flex-1 px-4 py-2 bg-fed-blue text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}
