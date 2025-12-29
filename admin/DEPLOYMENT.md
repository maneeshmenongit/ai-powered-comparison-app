# Admin Dashboard Deployment Guide

This guide explains how to deploy the admin cost tracking dashboard to Netlify.

## Deployment Steps

### 1. Create New Netlify Site

1. Go to [Netlify Dashboard](https://app.netlify.com/)
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `admin`
   - **Build command**: Leave empty (static site)
   - **Publish directory**: `admin` (or `.` if base directory is already set)
   - **Branch to deploy**: `main` (or your production branch)

### 2. Enable Password Protection

Netlify offers several options for password protection:

#### Option A: Visitor Access Control (Recommended for simple use)
1. Go to Site Settings → Security → Visitor Access
2. Enable "Visitor access control"
3. Set a password that all team members will use
4. Click "Save"

This creates a simple password prompt before accessing the site.

#### Option B: Netlify Identity (More robust, per-user access)
1. Go to Site Settings → Identity
2. Enable Identity
3. Set "Registration preferences" to "Invite only"
4. Go to Identity tab and invite team members via email
5. Each person gets their own login credentials

### 3. Update Backend CORS

After deployment, you'll get a Netlify URL like `https://hopwise-admin.netlify.app`

Add this URL to the backend CORS configuration in `api/app.py`:

```python
CORS(app, resources={r"/api/*": {
    "origins": [
        # ... existing origins ...
        "https://hopwise-admin.netlify.app",  # Add your Netlify URL here
        "https://*.netlify.app"  # Or use wildcard for preview deployments
    ]
}})
```

Commit and deploy the backend changes to Railway.

### 4. Verify Deployment

1. Visit your Netlify dashboard URL
2. Enter the password (if using Visitor Access Control)
3. Verify the dashboard loads and displays cost data
4. Check that API calls to `https://api.hopwise.app` work correctly

## Security Notes

- **Password Protection**: This dashboard contains sensitive cost information and should ALWAYS be password-protected
- **HTTPS Only**: Netlify provides HTTPS by default - never disable it
- **Team Access Only**: Only share credentials with authorized team members
- **Regular Updates**: Keep the password secure and rotate it periodically

## Maintenance

- The dashboard auto-refreshes every 30 seconds
- No build or deployment needed for updates - just push to the branch
- Monitor the Netlify deployment logs if issues occur

## Troubleshooting

### Dashboard loads but shows "Unable to load budget data"
- Check that backend CORS includes the Netlify URL
- Verify backend is running at `https://api.hopwise.app`
- Check browser console for CORS errors

### Password prompt not appearing
- Verify Visitor Access Control is enabled in Netlify settings
- Clear browser cache and try again

### Dashboard shows old data
- Check that backend `/api/costs/budget` endpoint is working
- Verify API calls in browser Network tab
- Dashboard auto-refreshes every 30 seconds
