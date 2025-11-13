'use client';

import { useState } from 'react';
import BottomSheet from './BottomSheet';
import { FilterValues } from './FilterPanel';

interface MobileFilterSheetProps {
  isOpen: boolean;
  onClose: () => void;
  values: FilterValues;
  onChange: (values: FilterValues) => void;
  onApply: () => void;
  onReset: () => void;
}

export default function MobileFilterSheet({
  isOpen,
  onClose,
  values,
  onChange,
  onApply,
  onReset,
}: MobileFilterSheetProps) {
  const [localValues, setLocalValues] = useState<FilterValues>(values);

  const handleChange = (field: keyof FilterValues, value: any) => {
    const newValues = { ...localValues, [field]: value };
    setLocalValues(newValues);
  };

  const handleApply = () => {
    onChange(localValues);
    onApply();
    onClose();
  };

  const handleReset = () => {
    const resetValues: FilterValues = {
      sortBy: 'date',
      sortOrder: 'desc',
    };
    setLocalValues(resetValues);
    onChange(resetValues);
    onReset();
    onClose();
  };

  return (
    <BottomSheet isOpen={isOpen} onClose={onClose} title="Filter Bills">
      <div className="space-y-6 pb-6">
        {/* Status Filter */}
        <div>
          <label htmlFor="mobile-status" className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            id="mobile-status"
            value={localValues.status || ''}
            onChange={(e) => handleChange('status', e.target.value || undefined)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue text-base"
          >
            <option value="">All Statuses</option>
            <option value="introduced">Introduced</option>
            <option value="passed">Passed</option>
            <option value="enacted">Enacted</option>
            <option value="became-law">Became Law</option>
          </select>
        </div>

        {/* Congress Filter */}
        <div>
          <label htmlFor="mobile-congress" className="block text-sm font-medium text-gray-700 mb-2">
            Congress
          </label>
          <select
            id="mobile-congress"
            value={localValues.congress || ''}
            onChange={(e) => handleChange('congress', e.target.value || undefined)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue text-base"
          >
            <option value="">All Congresses</option>
            <option value="118">118th Congress (2023-2025)</option>
            <option value="117">117th Congress (2021-2023)</option>
            <option value="116">116th Congress (2019-2021)</option>
            <option value="115">115th Congress (2017-2019)</option>
          </select>
        </div>

        {/* Bill Type Filter */}
        <div>
          <label htmlFor="mobile-bill-type" className="block text-sm font-medium text-gray-700 mb-2">
            Bill Type
          </label>
          <select
            id="mobile-bill-type"
            value={localValues.billType || ''}
            onChange={(e) => handleChange('billType', e.target.value || undefined)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue text-base"
          >
            <option value="">All Types</option>
            <option value="hr">House Bill (HR)</option>
            <option value="s">Senate Bill (S)</option>
            <option value="hjres">House Joint Resolution (HJRES)</option>
            <option value="sjres">Senate Joint Resolution (SJRES)</option>
          </select>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="mobile-date-from" className="block text-sm font-medium text-gray-700 mb-2">
              From Date
            </label>
            <input
              type="date"
              id="mobile-date-from"
              value={localValues.dateFrom || ''}
              onChange={(e) => handleChange('dateFrom', e.target.value || undefined)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue text-base"
            />
          </div>
          <div>
            <label htmlFor="mobile-date-to" className="block text-sm font-medium text-gray-700 mb-2">
              To Date
            </label>
            <input
              type="date"
              id="mobile-date-to"
              value={localValues.dateTo || ''}
              onChange={(e) => handleChange('dateTo', e.target.value || undefined)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue text-base"
            />
          </div>
        </div>

        {/* Public Law Filter */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="mobile-public-law"
            checked={localValues.hasPublicLaw || false}
            onChange={(e) => handleChange('hasPublicLaw', e.target.checked || undefined)}
            className="h-5 w-5 text-fed-blue border-gray-300 rounded focus:ring-fed-blue"
          />
          <label htmlFor="mobile-public-law" className="ml-3 text-sm font-medium text-gray-700">
            Bills that became law
          </label>
        </div>

        {/* Sort Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sort By
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['date', 'congress', 'number'].map((sort) => (
              <button
                key={sort}
                onClick={() => handleChange('sortBy', sort)}
                className={`
                  px-4 py-3 rounded-lg border text-sm font-medium transition-colors
                  ${
                    localValues.sortBy === sort
                      ? 'border-fed-blue bg-fed-blue text-white'
                      : 'border-gray-300 text-gray-700 hover:border-fed-blue'
                  }
                `}
              >
                {sort.charAt(0).toUpperCase() + sort.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Sort Order */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sort Order
          </label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'desc', label: 'Newest First' },
              { value: 'asc', label: 'Oldest First' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => handleChange('sortOrder', option.value)}
                className={`
                  px-4 py-3 rounded-lg border text-sm font-medium transition-colors
                  ${
                    localValues.sortOrder === option.value
                      ? 'border-fed-blue bg-fed-blue text-white'
                      : 'border-gray-300 text-gray-700 hover:border-fed-blue'
                  }
                `}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            className="px-6 py-3 border border-gray-300 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleApply}
            className="px-6 py-3 bg-fed-blue text-white rounded-lg text-base font-medium hover:bg-blue-700 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </BottomSheet>
  );
}
