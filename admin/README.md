# Admin Tools

This directory contains internal tools and dashboards for the Hopwise team.

**⚠️ Important: These files are NOT deployed to production and should NOT be accessible to users.**

## Contents

- **cost-dashboard.html** - Real-time Google Places API cost tracking dashboard
  - View daily/monthly API usage
  - Monitor budget status and alerts
  - Track costs against free tier and $200 monthly credit

## Usage

### Cost Dashboard

1. Ensure the backend is running (locally or on Railway)
2. Open `cost-dashboard.html` in your browser
3. The dashboard will fetch data from `/api/costs/*` endpoints

### Local Development

```bash
# Make sure backend is running
cd api
python app.py

# Open dashboard
open admin/cost-dashboard.html
```

### Production Monitoring

Update the API_BASE_URL in the dashboard to point to:
```
https://api.hopwise.app
```

## Security Notes

- This directory should be added to `.gitignore` if it contains sensitive data
- Dashboard authenticates via CORS (only allowed origins can access)
- No sensitive API keys are exposed in the dashboard
- Data is read-only from the cost tracking endpoints
