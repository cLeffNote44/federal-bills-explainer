'use client';

import { FormEvent, useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

interface AutocompleteSuggestion {
  congress: number;
  bill_type: string;
  number: number;
  title: string;
  identifier: string;
}

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search bills...',
  disabled = false,
  className = '',
}: SearchBarProps) {
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Fetch autocomplete suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (value.length < 2) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }

      try {
        setIsLoading(true);
        const data = await api
          .get('bills/autocomplete', { searchParams: { q: value } })
          .json<AutocompleteSuggestion[]>();
        setSuggestions(data);
        setShowSuggestions(data.length > 0);
      } catch (error) {
        console.error('Autocomplete error:', error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Debounce the API call
    const timeoutId = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [value]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        if (selectedIndex >= 0) {
          e.preventDefault();
          selectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const selectSuggestion = (suggestion: AutocompleteSuggestion) => {
    onChange(suggestion.title);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    // Trigger search immediately
    setTimeout(() => {
      const form = inputRef.current?.closest('form');
      if (form) {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    }, 0);
  };

  return (
    <form onSubmit={onSubmit} className={`relative ${className}`} data-testid="search-bar">
      <div className="flex gap-4 max-w-2xl">
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              setSelectedIndex(-1);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-fed-blue disabled:bg-gray-100 disabled:cursor-not-allowed"
            data-testid="search-input"
            autoComplete="off"
          />

          {/* Autocomplete Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto"
              data-testid="autocomplete-suggestions"
            >
              {suggestions.map((suggestion, index) => (
                <div
                  key={`${suggestion.congress}-${suggestion.bill_type}-${suggestion.number}`}
                  onClick={() => selectSuggestion(suggestion)}
                  className={`px-4 py-3 cursor-pointer hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                    index === selectedIndex ? 'bg-blue-50' : ''
                  }`}
                  data-testid="autocomplete-item"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-semibold text-fed-blue bg-blue-50 px-2 py-1 rounded">
                      {suggestion.identifier}
                    </span>
                    <span className="text-sm text-gray-700 flex-1 line-clamp-2">
                      {suggestion.title}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Loading indicator */}
          {isLoading && value.length >= 2 && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <svg
                className="animate-spin h-5 w-5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            </div>
          )}
        </div>

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
