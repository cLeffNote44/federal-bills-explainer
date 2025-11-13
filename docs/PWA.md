# Progressive Web App (PWA) Documentation

This document describes the Progressive Web App implementation for the Federal Bills Explainer.

## Overview

The Federal Bills Explainer is a fully-featured Progressive Web App that works offline, can be installed on devices, and provides a native app-like experience.

## Features

### 1. Installable

Users can install the app on their devices (desktop and mobile) for quick access:

- **Desktop**: Install via browser's "Install" button in address bar
- **Mobile**: Install via "Add to Home Screen" prompt
- **Automatic prompts**: App will suggest installation after 30 seconds of use

### 2. Offline Support

The app works offline with cached content:

- **Service Worker**: Caches essential assets and API responses
- **Offline Page**: Custom offline page when network is unavailable
- **Background Sync**: Syncs data when connection is restored
- **Cache Strategy**:
  - Network-first for API requests
  - Cache-first for static assets
  - 5-minute cache TTL for API data

### 3. Mobile-Optimized

Fully responsive with mobile-first design:

- **Touch Gestures**: Swipe, tap, long-press support
- **Bottom Sheet**: Mobile-friendly filter panel
- **Mobile Navigation**: Hamburger menu with slide-out drawer
- **Optimized Layouts**: Breakpoint-specific designs

### 4. Native Features

Utilizes native device capabilities:

- **Web Share API**: Share bills natively
- **Push Notifications**: (Optional) Bill update notifications
- **App Shortcuts**: Quick access to common actions
- **Full-screen Mode**: Immersive app experience

## Installation

### For Users

#### Mobile (iOS)

1. Open the app in Safari
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" to confirm

#### Mobile (Android)

1. Open the app in Chrome
2. Tap the menu (three dots)
3. Tap "Install app" or "Add to Home Screen"
4. Tap "Install" to confirm

#### Desktop (Chrome/Edge)

1. Open the app in Chrome or Edge
2. Click the install icon in the address bar
3. Click "Install" in the popup

### For Developers

The PWA is automatically configured. To customize:

```bash
# Edit manifest
nano apps/frontend/public/manifest.json

# Edit service worker
nano apps/frontend/public/sw.js

# Update PWA provider
nano apps/frontend/src/app/pwa-provider.tsx
```

## Architecture

### Service Worker (`public/sw.js`)

The service worker handles:

- **Install**: Pre-caches essential assets
- **Activate**: Cleans up old caches
- **Fetch**: Serves from cache with network fallback
- **Background Sync**: Syncs when online
- **Push Notifications**: Handles push events

**Cache Strategy:**
```javascript
// API requests: Network-first, cache fallback
if (url.pathname.startsWith('/api')) {
  return handleApiRequest(request);
}

// Static assets: Cache-first, network fallback
return handleStaticRequest(request);
```

### Manifest (`public/manifest.json`)

Defines app metadata:

- **Name**: "Federal Bills Explainer"
- **Theme Color**: `#1e40af` (fed-blue)
- **Display Mode**: `standalone`
- **Icons**: 8 sizes from 72x72 to 512x512
- **Shortcuts**: Search, Recent Bills
- **Share Target**: Enables sharing to the app

### PWA Utilities (`lib/pwa.ts`)

React hooks and utilities:

```typescript
// Install prompt hook
const { canInstall, isInstalled, installApp } = useInstallPrompt();

// Online status hook
const isOnline = useOnlineStatus();

// Register service worker
await registerServiceWorker();

// Clear cache
await clearCache();

// Show notification
await showNotification('Title', { body: 'Message' });

// Share content
await shareContent({ title, text, url });
```

## Components

### InstallPrompt

Prompts users to install the app:

```tsx
import { InstallPrompt } from '@/components';

// Automatically shown after 30 seconds
<InstallPrompt />
```

**Features:**
- Shows only if app is installable
- Dismissible (remembers preference)
- Auto-shows after 30 seconds
- Styled notification

### MobileNav

Mobile navigation menu:

```tsx
import { MobileNav } from '@/components';

<MobileNav />
```

**Features:**
- Hamburger menu icon
- Slide-out drawer
- Active route highlighting
- Touch-optimized (44px min touch targets)

### BottomSheet

Mobile-friendly modal:

```tsx
import { BottomSheet } from '@/components';

<BottomSheet
  isOpen={isOpen}
  onClose={onClose}
  title="Filters"
>
  {/* Content */}
</BottomSheet>
```

**Features:**
- Swipe to dismiss
- Snap points
- Backdrop
- Touch-optimized

### MobileFilterSheet

Mobile filter panel:

```tsx
import { MobileFilterSheet } from '@/components';

<MobileFilterSheet
  isOpen={isOpen}
  onClose={onClose}
  values={filters}
  onChange={setFilters}
  onApply={handleApply}
  onReset={handleReset}
/>
```

## Touch Gestures

Custom touch gesture hooks:

### Swipe

```tsx
import { useSwipe } from '@/lib/touch-gestures';

useSwipe({
  onSwipeLeft: () => console.log('Swiped left'),
  onSwipeRight: () => console.log('Swiped right'),
  onSwipeUp: () => console.log('Swiped up'),
  onSwipeDown: () => console.log('Swiped down'),
  threshold: 50, // pixels
});
```

### Long Press

```tsx
import { useLongPress } from '@/lib/touch-gestures';

const longPressHandlers = useLongPress(
  () => console.log('Long pressed'),
  {
    threshold: 500, // ms
    onStart: () => console.log('Started'),
    onFinish: () => console.log('Finished'),
    onCancel: () => console.log('Cancelled'),
  }
);

<button {...longPressHandlers}>Press and hold</button>
```

### Pull to Refresh

```tsx
import { usePullToRefresh } from '@/lib/touch-gestures';

usePullToRefresh(
  async () => {
    // Refresh data
    await fetchBills();
  },
  {
    threshold: 80,
    enabled: true,
  }
);
```

### Double Tap

```tsx
import { useTap } from '@/lib/touch-gestures';

const tapHandlers = useTap(
  () => console.log('Single tap'),
  () => console.log('Double tap'),
  300 // delay ms
);

<div {...tapHandlers}>Tap me</div>
```

## Offline Functionality

### Offline Page

Custom offline experience at `/offline`:

- Clear messaging about offline status
- List of available features
- Try again button
- Automatically redirects when back online

### Caching Strategy

**Static Assets:**
- HTML, CSS, JS files
- Images and fonts
- Cache-first with background update

**API Responses:**
- Bills list
- Bill details
- Search results
- 5-minute TTL
- Network-first with cache fallback

**Excluded from Cache:**
- Admin endpoints
- Authentication endpoints
- Real-time data

### Background Sync

Automatically syncs when connection restored:

```javascript
// Register background sync
navigator.serviceWorker.ready.then(registration => {
  return registration.sync.register('sync-bills');
});
```

## Performance Optimizations

### Lazy Loading

Heavy components are lazy-loaded:

```tsx
// FilterPanel and ExportButton are lazy-loaded
const FilterPanel = dynamic(() => import('@/components/FilterPanel'), {
  loading: () => <LoadingSkeleton />,
  ssr: false,
});
```

### Code Splitting

Automatic code splitting for:
- Routes (Next.js automatic)
- Components (via dynamic import)
- Libraries (webpack optimization)

### Asset Optimization

- **Images**: AVIF/WebP with fallback
- **Fonts**: Subset and preload
- **Bundle**: Tree-shaking and minification

## Testing PWA Features

### Local Testing

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Test service worker
open http://localhost:3000
# Open DevTools > Application > Service Workers
```

### Lighthouse Audit

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse http://localhost:3000 --view

# Check PWA score
# Target: 90+ for all categories
```

### Manual Testing Checklist

- [ ] App installs successfully
- [ ] App works offline
- [ ] Service worker registers
- [ ] Install prompt appears
- [ ] Offline page shows when disconnected
- [ ] Touch gestures work
- [ ] Mobile navigation works
- [ ] Bottom sheet dismisses on swipe
- [ ] Manifest loads correctly
- [ ] Icons display properly
- [ ] Theme color applies
- [ ] Share functionality works (mobile)
- [ ] App shortcuts work (after install)

## Debugging

### Service Worker

```javascript
// Check service worker status
navigator.serviceWorker.getRegistration().then(reg => {
  console.log('SW registration:', reg);
  console.log('SW state:', reg.active?.state);
});

// Force update service worker
navigator.serviceWorker.getRegistration().then(reg => {
  reg.update();
});

// Unregister service worker
navigator.serviceWorker.getRegistration().then(reg => {
  reg.unregister();
});
```

### Cache

```javascript
// List all caches
caches.keys().then(names => console.log('Caches:', names));

// Clear all caches
caches.keys().then(names => {
  return Promise.all(names.map(name => caches.delete(name)));
});

// Inspect cache contents
caches.open('federal-bills-v1').then(cache => {
  cache.keys().then(requests => {
    console.log('Cached URLs:', requests.map(r => r.url));
  });
});
```

### DevTools

**Chrome DevTools:**
1. Open DevTools (F12)
2. Go to "Application" tab
3. Check:
   - Manifest
   - Service Workers
   - Cache Storage
   - Storage (IndexedDB, LocalStorage)

**Debugging Tips:**
- Use "Bypass for network" checkbox to skip service worker
- Click "Update on reload" to force SW updates
- Use "Clear site data" to reset everything
- Check "Offline" to simulate offline mode

## Best Practices

### Service Worker

- ✅ Keep SW file small and fast
- ✅ Version caches properly
- ✅ Clean up old caches on activate
- ✅ Use appropriate cache strategies
- ✅ Handle failed requests gracefully
- ✅ Test SW updates thoroughly

### Manifest

- ✅ Provide icons for all sizes
- ✅ Use maskable icons for Android
- ✅ Set appropriate theme color
- ✅ Add meaningful shortcuts
- ✅ Include screenshots for install prompt
- ✅ Test on multiple devices

### Mobile Experience

- ✅ Minimum 44x44px touch targets
- ✅ Prevent accidental zooms
- ✅ Support landscape and portrait
- ✅ Test on real devices
- ✅ Optimize for slow connections
- ✅ Provide feedback for actions

## Browser Support

| Feature | Chrome | Safari | Firefox | Edge |
|---------|--------|--------|---------|------|
| Service Worker | ✅ | ✅ | ✅ | ✅ |
| Web App Manifest | ✅ | ✅ | ✅ | ✅ |
| Install Prompt | ✅ | ✅* | ❌ | ✅ |
| Push Notifications | ✅ | ✅** | ✅ | ✅ |
| Background Sync | ✅ | ❌ | ❌ | ✅ |
| Web Share | ✅ | ✅ | ❌*** | ✅ |

\* iOS: Add to Home Screen from Share menu
\** iOS 16.4+
\*** Desktop only

## Troubleshooting

### App won't install
- Check manifest.json is valid
- Ensure HTTPS (required for PWA)
- Verify service worker is registered
- Check browser supports installation

### Service worker not updating
- Hard refresh (Ctrl+Shift+R)
- Clear browser cache
- Check "Update on reload" in DevTools
- Verify SW version changed

### Offline mode not working
- Check service worker is active
- Verify fetch events are captured
- Check cache strategy is correct
- Test with DevTools offline mode first

### Icons not showing
- Verify icon paths are correct
- Check icons exist in public folder
- Ensure proper sizes (192x192, 512x512 minimum)
- Test manifest with Lighthouse

## Resources

- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Workbox](https://developers.google.com/web/tools/workbox) (advanced SW library)
- [PWA Builder](https://www.pwabuilder.com/) (generate assets)
