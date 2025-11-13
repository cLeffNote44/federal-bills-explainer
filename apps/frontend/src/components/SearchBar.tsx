'use client';

import { FormEvent } from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search bills...',
  disabled = false,
  className = '',
}: SearchBarProps) {
  return (
    <form onSubmit={onSubmit} className={`${className}`} data-testid="search-bar">
      <div className="flex gap-4 max-w-2xl">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-fed-blue disabled:bg-gray-100 disabled:cursor-not-allowed"
          data-testid="search-input"
        />
        <button
          type="submit"
          disabled={disabled}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          data-testid="search-button"
        >
          Search
        </button>
      </div>
    </form>
  );
}
