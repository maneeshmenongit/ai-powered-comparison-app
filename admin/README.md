# Admin Tools

This directory contains internal tools and dashboards for the Hopwise team.

**⚠️ Important: These files are NOT deployed anywhere. Team-only, local access.**

## Deployment Structure

```
Vercel  → frontend/           (app.hopwise.app)
Railway → api/, src/, etc.    (api.hopwise.app)
Local   → admin/              (team dashboards)
```

The `admin/` directory is:
- ✅ In Git (so team can access)
- ❌ NOT deployed to Vercel (only `frontend/` is deployed)
- ❌ NOT deployed to Railway (stays local)

## Contents

- **dashboard.html** - Real-time Google Places API cost tracking dashboard
  - View daily/monthly API usage
  - Monitor budget status and alerts
  - Track costs against free tier and $200 monthly credit

## Usage

### Cost Dashboard

1. Clone the repo (if you haven't already)
2. Open `admin/dashboard.html` in your browser
3. Dashboard automatically connects to production API at `api.hopwise.app`

### Local Development

```bash
# Option 1: Open file directly
open admin/dashboard.html

# Option 2: Serve with Python (if CORS issues)
cd admin
python -m http.server 8000
# Then open: http://localhost:8000/dashboard.html
```

The dashboard will automatically detect:
- **Local backend**: `http://localhost:5001/api` (if running locally)
- **Production backend**: `https://api.hopwise.app/api` (default)

### API Endpoints

The dashboard fetches from:
- `GET /api/costs/report` - Full cost report
- `GET /api/costs/budget` - Budget status with alerts
- `GET /api/costs/monthly` - Monthly breakdown
- `GET /api/costs/daily` - Daily summary
- `GET /api/costs/pricing` - Current pricing config

## Security Notes

- ✅ Dashboard is read-only (no write access to backend)
- ✅ CORS protects API (only allowed origins can access)
- ✅ No API keys exposed in dashboard HTML
- ✅ Cost data is non-sensitive (just usage metrics)
- ⚠️ Keep this directory out of public deployments (already configured)
