'use client';

import { useState } from 'react';

interface ShareButtonProps {
  billId: string;
  billTitle: string;
  className?: string;
}

export default function ShareButton({ billId, billTitle, className = '' }: ShareButtonProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [shareLinks, setShareLinks] = useState<any>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const loadShareLinks = async () => {
    if (shareLinks) {
      setShowMenu(!showMenu);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/sharing/link/${billId}`);
      const data = await response.json();
      setShareLinks(data.links);
      setShowMenu(true);
    } catch (error) {
      console.error('Error loading share links:', error);
    }
  };

  const copyToClipboard = async () => {
    if (shareLinks?.copy) {
      await navigator.clipboard.writeText(shareLinks.copy);
      alert('Link copied to clipboard!');
      setShowMenu(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={loadShareLinks}
        className={`flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors ${className}`}
      >
        <svg className="h-4 w-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
          />
        </svg>
        <span className="text-sm font-medium text-gray-700">Share</span>
      </button>

      {showMenu && shareLinks && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <div className="p-2">
            <a
              href={shareLinks.facebook}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span>Facebook</span>
            </a>
            <a
              href={shareLinks.twitter}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span>Twitter</span>
            </a>
            <a
              href={shareLinks.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span>LinkedIn</span>
            </a>
            <a
              href={shareLinks.reddit}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span>Reddit</span>
            </a>
            <button
              onClick={copyToClipboard}
              className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-50 rounded-md transition-colors text-left"
            >
              <span>Copy Link</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
