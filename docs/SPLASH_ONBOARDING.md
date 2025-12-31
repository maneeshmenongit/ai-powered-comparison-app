# Splash Screen & Onboarding Flow

Complete first-time user experience for Hopwise app.

## Overview

The splash screen and onboarding flow provides a professional first impression and introduces users to key app features.

### Components

1. **Splash Screen** - Shows for 2.5 seconds on every app load
2. **Onboarding Screens** - 3 swipeable screens shown only to first-time users
3. **localStorage Tracking** - Remembers if user has completed onboarding

---

## File Structure

```
frontend/
├── css/
│   └── splash-onboarding.css      # Styles and animations
├── js/
│   └── splash-onboarding.js       # SplashOnboardingManager class
├── assets/
│   └── background/
│       ├── sticker_background_v1.png   # Onboarding Screen 1
│       ├── sticker_background_v2.png   # Onboarding Screen 2
│       └── sticker_background_v3.png   # Splash + Onboarding Screen 3
├── index.html                     # Integrated splash/onboarding HTML
└── splash-onboarding.html         # Standalone component (reference)
```

---

## User Flow

### First-Time User
1. ✈️ **Splash Screen** (2.5 seconds)
   - Animated Hopwise logo floating
   - Brand name + tagline
   - Travel-themed progress bar with "Planning your journey..."

2. 🚗 **Onboarding Screen 1: Compare Rides**
   - Sticker background v1 (35% opacity)
   - Bouncing car emoji 🚗
   - Title: "Compare Rides Instantly"
   - Description: "Get real-time prices from Uber and Lyft..."
   - Actions: [Next] button, [Skip] button (top-right)

3. 🍽️ **Onboarding Screen 2: Discover Places**
   - Sticker background v2 (35% opacity)
   - Bouncing food emoji 🍽️
   - Title: "Discover Great Places"
   - Description: "Find top-rated restaurants..."
   - Actions: [Next] button, [Skip] button (top-right)

4. 🗺️ **Onboarding Screen 3: Smarter Travel**
   - Sticker background v3 (35% opacity)
   - Bouncing map emoji 🗺️
   - Title: "One App. Smarter Travel."
   - Description: "Plan your entire journey..."
   - Actions: [Get Started] button, [Sign In] button (secondary)
   - Note: Skip button hidden on last screen

5. → **Main App**
   - localStorage flag set: `hopwise_onboarding_completed = true`
   - App content becomes visible

### Returning User
1. ✈️ **Splash Screen** (2.5 seconds)
2. → **Main App** (onboarding skipped)

---

## Key Features

### 1. Splash Screen
- **Duration**: 2.5 seconds (configurable in `splash-onboarding.js`)
- **Background**: Sticker background v3 at 40% opacity
- **Logo**: Floating animation (3s cycle)
- **Progress Bar**: Sliding gradient animation (1.5s cycle)
- **Transition**: Fade-out (0.5s) before showing onboarding/app

### 2. Onboarding Screens
- **Backgrounds**: Different sticker backgrounds for each screen
- **Icons**: Bouncing emoji animations (2s cycle)
- **Progress Dots**: 3 dots showing current position
  - Active dot: wider (24px) and white
  - Inactive dots: smaller (8px) and semi-transparent
- **Gradient Highlights**: Title keywords highlighted with golden gradient
- **Responsive**: Optimized for mobile (max-width: 430px)

### 3. Navigation
- **Next**: Advances to next screen
- **Skip**: Completes onboarding immediately, goes to app
- **Get Started**: Completes onboarding, goes to app
- **Sign In**: Completes onboarding, navigates to profile/login page

---

## Animations

All defined in `frontend/css/splash-onboarding.css`:

| Animation | Duration | Effect | Used For |
|-----------|----------|--------|----------|
| `float` | 3s | Up/down movement (-20px) | Splash logo |
| `slide` | 1.5s | Left to right slide | Progress bar fill |
| `hop` | 1s | Jump + rotate | Splash loader icon |
| `bounce` | 2s | Jump + scale | Onboarding icons |

---

## JavaScript API

### SplashOnboardingManager Class

**Location**: `frontend/js/splash-onboarding.js`

#### Methods

```javascript
// Initialize (called automatically on DOMContentLoaded)
window.splashOnboarding.initialize()

// Navigation
window.splashOnboarding.nextScreen()      // Go to next onboarding screen
window.splashOnboarding.skipOnboarding()  // Skip to app
window.splashOnboarding.finishOnboarding() // Complete onboarding, go to app
window.splashOnboarding.showSignIn()      // Complete onboarding, go to profile

// Utility
window.splashOnboarding.resetOnboarding() // Clear localStorage flag
```

#### Testing

To see onboarding again after completing it:

```javascript
// In browser console
resetOnboarding()
// Then refresh the page
```

Or use the global function:
```javascript
window.resetOnboarding()
```

---

## localStorage

**Key**: `hopwise_onboarding_completed`
**Values**:
- `"true"` - User has completed onboarding (skip on next load)
- `null` or missing - First-time user (show onboarding)

**Location**: Browser localStorage (persists across sessions)

---

## Customization

### Change Splash Duration
Edit `frontend/js/splash-onboarding.js`:
```javascript
setTimeout(() => {
    this.hideSplashScreen();
    // ...
}, 2500); // Change this value (milliseconds)
```

### Modify Onboarding Screens
Edit `frontend/index.html`:
- Update titles, descriptions, icons
- Change background images
- Modify button text/actions

### Update Animations
Edit `frontend/css/splash-onboarding.css`:
- Adjust `@keyframes` definitions
- Change animation durations
- Modify icon sizes, colors, etc.

---

## Design Specifications

### Splash Screen
- **Background**: Linear gradient (135deg, #FF8E53 → #FE6B8B)
- **Sticker Overlay**: 40% opacity
- **Logo Size**: 120px × 120px (100px on mobile)
- **Brand Font**: 32px, weight 900 (28px on mobile)
- **Tagline Font**: 16px, weight 600 (14px on mobile)
- **Progress Bar**: 200px × 4px

### Onboarding Screens
- **Background**: Same gradient as splash
- **Sticker Overlay**: 35% opacity
- **Icon Size**: 80px (64px on mobile)
- **Title Font**: 28px, weight 900 (24px on mobile)
- **Description Font**: 16px, line-height 1.6 (14px on mobile)
- **Max Content Width**: 300px
- **Button Height**: 48px (16px padding)
- **Dots**: 8px circle (24px × 8px when active)

### Colors
- **Primary Button**: White background, #FF8E53 text
- **Secondary Button**: Transparent with white border, white text
- **Gradient Highlight**: Linear gradient (135deg, #FFE5B4 → #FFB347)
- **Text Shadow**: 0 2px 8px rgba(0,0,0,0.2)

---

## Browser Compatibility

- ✅ Chrome/Edge (modern)
- ✅ Safari (iOS 12+)
- ✅ Firefox (modern)
- ⚠️ IE11 - Not supported (uses CSS Grid, modern animations)

---

## Performance

### Image Optimization
- **sticker_background_v1.png**: ~1.1 MB
- **sticker_background_v2.png**: ~1.2 MB
- **sticker_background_v3.png**: ~1.0 MB

**Total**: ~3.3 MB (loaded on first visit only)

### Load Sequence
1. HTML/CSS loads → Splash screen visible immediately
2. JavaScript executes → SplashOnboardingManager initializes
3. After 2.5s → Onboarding shows (if first-time)
4. User completes onboarding → Main app becomes visible

### Caching
- Background images cached by browser
- localStorage persists onboarding completion
- Returning users only see splash (2.5s), skip onboarding

---

## Troubleshooting

### Issue: Onboarding shows every time
**Solution**: Check localStorage in browser DevTools:
```javascript
localStorage.getItem('hopwise_onboarding_completed')
```
Should return `"true"` after completing onboarding.

### Issue: Splash screen doesn't disappear
**Solution**: Check browser console for JavaScript errors. Ensure `splash-onboarding.js` loaded correctly.

### Issue: Background images not loading
**Solution**: Verify file paths in `index.html`:
```html
background-image: url('./assets/background/sticker_background_v1.png')
```
Check that files exist in `frontend/assets/background/`.

### Issue: App doesn't show after onboarding
**Solution**: Check that `#app` element has `display: block` set by JavaScript:
```javascript
// In browser console
document.getElementById('app').style.display
// Should return "block"
```

---

## Future Enhancements

Potential improvements:
- [ ] Add swipe gestures for onboarding navigation
- [ ] Implement screen transition animations (slide in/out)
- [ ] Add option to revisit onboarding from settings
- [ ] A/B test different onboarding content
- [ ] Track onboarding completion rate (analytics)
- [ ] Lazy load background images (improve initial load)
- [ ] Add video/Lottie animations instead of static images

---

## Testing Checklist

- [ ] Splash screen shows on first load
- [ ] Onboarding appears after splash (first-time user)
- [ ] All 3 onboarding screens display correctly
- [ ] Progress dots update on each screen
- [ ] "Skip" button works on screens 1-2
- [ ] "Skip" button hidden on screen 3
- [ ] "Next" advances to next screen
- [ ] "Get Started" completes onboarding → shows app
- [ ] "Sign In" completes onboarding → navigates to profile
- [ ] localStorage flag set after completion
- [ ] Returning user skips onboarding (splash → app)
- [ ] `resetOnboarding()` function works
- [ ] Mobile responsive (test on various screen sizes)
- [ ] Animations run smoothly (60fps)

---

## Analytics Events (Future)

Track these events for insights:

```javascript
// Suggested analytics events
gtag('event', 'splash_screen_shown')
gtag('event', 'onboarding_started')
gtag('event', 'onboarding_screen_viewed', { screen: 1 })
gtag('event', 'onboarding_screen_viewed', { screen: 2 })
gtag('event', 'onboarding_screen_viewed', { screen: 3 })
gtag('event', 'onboarding_skipped', { at_screen: 1 })
gtag('event', 'onboarding_completed', { method: 'get_started' })
gtag('event', 'onboarding_completed', { method: 'sign_in' })
```

---

**Last Updated**: December 31, 2024
**Version**: 1.0.0
