'use client';

import { FormEvent, useState, useEffect, useRef } from 'react';

interface SearchBarEnhancedProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  showHistory?: boolean;
}

export default function SearchBarEnhanced({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search bills by title, summary, sponsor...',
  disabled = false,
  className = '',
  showHistory = true,
}: SearchBarEnhancedProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [popularSearches, setPopularSearches] = useState<Array<{ query: string; count: number }>>([]);
  const [recentSearches, setRecentSearches] = useState<Array<{ query: string; timestamp: string }>>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showPopular, setShowPopular] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
        const response = await fetch(`${API_URL}/search/autocomplete?query=${encodeURIComponent(value)}`);
        const data = await response.json();
        setSuggestions(data.suggestions || []);
        setShowSuggestions(data.suggestions && data.suggestions.length > 0);
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

  // Fetch popular and recent searches when input is focused and empty
  useEffect(() => {
    if (showHistory && showPopular && value.length === 0) {
      fetchPopularAndRecentSearches();
    }
  }, [showPopular, showHistory]);

  const fetchPopularAndRecentSearches = async () => {
    try {
      // Fetch popular searches
      const popularResponse = await fetch(`${API_URL}/search/history/popular?limit=5`);
      const popularData = await popularResponse.json();
      setPopularSearches(popularData.popular_searches || []);

      // Fetch recent searches
      const recentResponse = await fetch(`${API_URL}/search/history/my?limit=5`);
      const recentData = await recentResponse.json();
      setRecentSearches(recentData.history || []);
    } catch (error) {
      console.error('Error fetching search history:', error);
    }
  };

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
        setShowPopular(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const allItems = value.length >= 2 ? suggestions : [...recentSearches.map(s => s.query), ...popularSearches.map(p => p.query)];

    if (!showSuggestions && !showPopular) return;
    if (allItems.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < allItems.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        if (selectedIndex >= 0) {
          e.preventDefault();
          selectSuggestion(allItems[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setShowPopular(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const selectSuggestion = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    setShowPopular(false);
    setSelectedIndex(-1);
    // Trigger search immediately
    setTimeout(() => {
      const form = inputRef.current?.closest('form');
      if (form) {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    }, 0);
  };

  const handleInputFocus = () => {
    if (value.length === 0 && showHistory) {
      setShowPopular(true);
      fetchPopularAndRecentSearches();
    } else if (value.length >= 2 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const clearRecentSearches = async () => {
    try {
      await fetch(`${API_URL}/search/history/my`, { method: 'DELETE' });
      setRecentSearches([]);
    } catch (error) {
      console.error('Error clearing search history:', error);
    }
  };

  return (
    <form onSubmit={onSubmit} className={`relative ${className}`}>
      <div className="flex gap-4 w-full">
        <div className="flex-1 relative">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(e) => {
                onChange(e.target.value);
                setSelectedIndex(-1);
                setShowPopular(false);
              }}
              onFocus={handleInputFocus}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fed-blue focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed text-base"
              autoComplete="off"
            />

            {/* Search icon */}
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {isLoading ? (
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
              ) : (
                <svg
                  className="h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              )}
            </div>
          </div>

          {/* Autocomplete Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={dropdownRef}
              className="absolute z-20 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto"
            >
              <div className="p-2">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    onClick={() => selectSuggestion(suggestion)}
                    className={`px-4 py-2 cursor-pointer rounded-md hover:bg-gray-50 ${
                      index === selectedIndex ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span className="text-sm text-gray-700">{suggestion}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Popular and Recent Searches */}
          {showPopular && value.length === 0 && (recentSearches.length > 0 || popularSearches.length > 0) && (
            <div
              ref={dropdownRef}
              className="absolute z-20 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto"
            >
              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <div className="p-3 border-b border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-600 uppercase">Recent Searches</span>
                    <button
                      type="button"
                      onClick={clearRecentSearches}
                      className="text-xs text-fed-blue hover:text-blue-700"
                    >
                      Clear
                    </button>
                  </div>
                  {recentSearches.map((search, index) => (
                    <div
                      key={index}
                      onClick={() => selectSuggestion(search.query)}
                      className="px-3 py-2 cursor-pointer rounded-md hover:bg-gray-50 flex items-center gap-2"
                    >
                      <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-gray-700">{search.query}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Popular Searches */}
              {popularSearches.length > 0 && (
                <div className="p-3">
                  <span className="text-xs font-semibold text-gray-600 uppercase mb-2 block">Popular Searches</span>
                  {popularSearches.map((search, index) => (
                    <div
                      key={index}
                      onClick={() => selectSuggestion(search.query)}
                      className="px-3 py-2 cursor-pointer rounded-md hover:bg-gray-50 flex items-center justify-between gap-2"
                    >
                      <div className="flex items-center gap-2">
                        <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        <span className="text-sm text-gray-700">{search.query}</span>
                      </div>
                      <span className="text-xs text-gray-500">{search.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled}
          className="px-6 py-3 bg-fed-blue text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Search
        </button>
      </div>
    </form>
  );
}
