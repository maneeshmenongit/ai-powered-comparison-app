# Google Analytics Domain Update Guide

## Domain Change
- **Old URL:** https://hopwise-app.netlify.app
- **New URL:** https://app.hopwise.app

---

## Important: No Action Required! ✅

**Good news:** Google Analytics 4 doesn't care about the URL configured in the data stream settings. As long as your website uses the correct `GA_MEASUREMENT_ID`, tracking will work perfectly from any domain.

**What matters:**
- ✅ Measurement ID: `G-N7B9CJR4CD` (stays the same)
- ✅ Your website sends events with this ID
- ✅ Analytics tracks any domain that uses this ID

**What doesn't matter:**
- ❌ The "Website URL" field in GA4 data stream settings
- ❌ This is just metadata/documentation, not functional

---

## Optional Updates (For Organization Only)

If you want to keep your GA4 console organized and up-to-date:

### 1. Update Data Stream URL (Optional - Documentation Only)

1. Go to [Google Analytics](https://analytics.google.com/)
2. Navigate to: **Admin** → **Property** (Hopwise App) → **Data Streams**
3. Click on your web data stream (ID: `13202288634`)
4. Update the **Website URL** from:
   - `https://hopwise-app.netlify.app`
   - `https://app.hopwise.app`
5. Click **Save**

**Why:** Purely for documentation - makes it easier to remember which domain this stream represents. Does NOT affect tracking functionality.

---

### 2. Update Referral Exclusions (Optional but Recommended)

If you're redirecting from the old domain to the new domain:

1. Go to: **Admin** → **Property** → **Data Streams** → Click your stream
2. Scroll to **More tagging settings** → **Configure tag settings**
3. Under **Referral exclusions**, add:
   - `hopwise-app.netlify.app` (to prevent self-referrals during transition)

**Why:** Prevents the old domain from showing as a referral source when users navigate from old to new domain.

---

### 3. Check Cross-Domain Tracking (If Applicable)

If you have multiple domains (e.g., marketing site vs app):

1. Go to: **Admin** → **Property** → **Data Streams** → **Configure tag settings**
2. Under **Cross-domain measurement**, verify your domains:
   - `app.hopwise.app`
   - Any other related domains

**Why:** Ensures user sessions are tracked correctly across domains.

---

### 4. Update Google Tag Manager (If Used)

If you're using Google Tag Manager instead of direct GA4:

1. Go to [Google Tag Manager](https://tagmanager.google.com/)
2. Update any hardcoded URLs in:
   - **Variables** (check for URL variables)
   - **Triggers** (check for URL-based triggers)
   - **Tags** (check for custom configurations)

---

### 5. Update Search Console (If Connected)

If your GA property is linked to Google Search Console:

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add the new domain: `app.hopwise.app`
3. Verify ownership (using DNS, HTML file, or Google Tag)
4. Link to Google Analytics:
   - **Settings** → **Associations** → **Google Analytics**

**Why:** Maintains SEO data integration between Search Console and Analytics.

---

### 6. Update Site Verification (If Needed)

Verify ownership of the new domain:

1. Go to: **Admin** → **Property Settings** → **Property Details**
2. Check if domain verification is required
3. Verify `app.hopwise.app` using one of these methods:
   - Google Tag (already installed via GA4)
   - HTML file upload
   - DNS TXT record
   - HTML meta tag

---

## Changes Already Made in Code ✅

Updated in [.env](.env:16):
```env
GA_STREAM_URL=https://app.hopwise.app
```

---

## Checklist

### Required (None!)
- [x] **Nothing required!** GA4 tracks based on Measurement ID, not URL configuration

### Optional (For Organization)
- [ ] Update Data Stream URL in Google Analytics (cosmetic only)
- [ ] Add referral exclusion for old domain (if redirecting old → new)
- [ ] Update Google Tag Manager (if used and has hardcoded URLs)
- [ ] Add new domain to Search Console (for SEO data)
- [ ] Update Railway environment variable `GA_STREAM_URL` (documentation only)

---

## Testing After Update

1. **Verify Tracking:**
   - Open your app at `https://app.hopwise.app`
   - Check **Real-time** report in Google Analytics
   - Confirm events are being tracked

2. **Check Debug View:**
   - Enable debug mode in your browser
   - Go to GA4 → **Admin** → **DebugView**
   - Verify events are coming from correct domain

3. **Monitor for 24-48 hours:**
   - Check that data is flowing correctly
   - Verify no duplicate tracking
   - Ensure old domain traffic (if any) is handled properly

---

## Important Notes

- ✅ **Nothing breaks:** Analytics will continue working immediately on new domain
- ✅ **No data loss:** Historical data from `hopwise-app.netlify.app` remains intact
- ✅ **Same Measurement ID:** You're still using `G-N7B9CJR4CD` (no changes needed)
- ✅ **No GA4 updates required:** The URL in data stream settings is just documentation
- ℹ️ **Automatic tracking:** GA4 tracks any domain that sends events with your Measurement ID
- ℹ️ **Both domains work:** If old and new domains both use the same ID, both will be tracked

---

## Railway Environment Variable Update

Update the production environment variable:

1. Go to Railway dashboard
2. Select your project
3. Go to **Variables**
4. Update or add:
   ```
   GA_STREAM_URL=https://app.hopwise.app
   ```
5. Redeploy if needed

---

**Updated:** December 31, 2025
**Status:** ⚠️ Code updated, Google Analytics update pending
