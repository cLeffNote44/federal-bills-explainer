'use client';

import { FormEvent } from 'react';

export interface FilterValues {
  status?: string;
  congress?: string;
  billType?: string;
  dateFrom?: string;
  dateTo?: string;
  hasPublicLaw?: boolean;
  sortBy?: string;
  sortOrder?: string;
}

interface FilterPanelProps {
  values: FilterValues;
  onChange: (values: FilterValues) => void;
  onApply: () => void;
  onReset: () => void;
  className?: string;
}

export default function FilterPanel({
  values,
  onChange,
  onApply,
  onReset,
  className = '',
}: FilterPanelProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onApply();
  };

  const updateValue = (key: keyof FilterValues, value: any) => {
    onChange({ ...values, [key]: value });
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`} data-testid="filter-panel">
      <form onSubmit={handleSubmit}>
        <h3 className="text-lg font-semibold mb-4">Filters</h3>

        <div className="space-y-4">
          {/* Status Filter */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              value={values.status || ''}
              onChange={(e) => updateValue('status', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
            >
              <option value="">All Statuses</option>
              <option value="introduced">Introduced</option>
              <option value="passed">Passed</option>
              <option value="enacted">Enacted</option>
              <option value="became-law">Became Law</option>
            </select>
          </div>

          {/* Congress Number */}
          <div>
            <label htmlFor="congress" className="block text-sm font-medium text-gray-700 mb-1">
              Congress
            </label>
            <select
              id="congress"
              value={values.congress || ''}
              onChange={(e) => updateValue('congress', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
            >
              <option value="">All Congresses</option>
              <option value="118">118th Congress (2023-2025)</option>
              <option value="117">117th Congress (2021-2023)</option>
              <option value="116">116th Congress (2019-2021)</option>
              <option value="115">115th Congress (2017-2019)</option>
            </select>
          </div>

          {/* Bill Type */}
          <div>
            <label htmlFor="billType" className="block text-sm font-medium text-gray-700 mb-1">
              Bill Type
            </label>
            <select
              id="billType"
              value={values.billType || ''}
              onChange={(e) => updateValue('billType', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
            >
              <option value="">All Types</option>
              <option value="hr">House Bill (HR)</option>
              <option value="s">Senate Bill (S)</option>
              <option value="hjres">House Joint Resolution (HJRes)</option>
              <option value="sjres">Senate Joint Resolution (SJRes)</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Introduced Date Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <input
                  type="date"
                  placeholder="From"
                  value={values.dateFrom || ''}
                  onChange={(e) => updateValue('dateFrom', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue text-sm"
                />
              </div>
              <div>
                <input
                  type="date"
                  placeholder="To"
                  value={values.dateTo || ''}
                  onChange={(e) => updateValue('dateTo', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue text-sm"
                />
              </div>
            </div>
          </div>

          {/* Public Law Filter */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={values.hasPublicLaw === true}
                onChange={(e) => updateValue('hasPublicLaw', e.target.checked ? true : undefined)}
                className="rounded border-gray-300 text-fed-blue focus:ring-fed-blue"
              />
              <span className="ml-2 text-sm text-gray-700">Only show bills that became law</span>
            </label>
          </div>

          {/* Sort Options */}
          <div>
            <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <div className="grid grid-cols-2 gap-2">
              <select
                id="sortBy"
                value={values.sortBy || 'date'}
                onChange={(e) => updateValue('sortBy', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
              >
                <option value="date">Date</option>
                <option value="congress">Congress</option>
                <option value="number">Number</option>
              </select>
              <select
                id="sortOrder"
                value={values.sortOrder || 'desc'}
                onChange={(e) => updateValue('sortOrder', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
              >
                <option value="desc">Newest First</option>
                <option value="asc">Oldest First</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              className="flex-1 bg-fed-blue text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-fed-blue"
            >
              Apply Filters
            </button>
            <button
              type="button"
              onClick={onReset}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              Reset
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
