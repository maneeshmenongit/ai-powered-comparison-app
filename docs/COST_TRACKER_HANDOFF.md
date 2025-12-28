# Hopwise Cost Tracker - Tech Architecture Handoff

**From:** Supervisor Thread (Thread 4)  
**To:** Tech & Architecture Thread (Thread 2)  
**Date:** December 28, 2024  
**Priority:** 🟡 P1 - Implement during next backend update

---

## 📋 Overview

We need to track all Google Places API costs in real-time to avoid budget surprises. This document provides everything needed to integrate cost tracking into the Hopwise backend.

**Goal:** Every Google API call gets logged → Dashboard shows daily/monthly costs → Alerts at 70%/90% budget usage.

---

## 📦 Files to Add

Add these files to your project structure:

```
hopwise/
├── backend/
│   ├── app.py                    # Your existing Flask app
│   ├── cost_tracker.py           # ✅ NEW - Add this file
│   ├── cost_data/                # ✅ NEW - Auto-created directory
│   │   ├── api_calls_YYYY-MM-DD.json
│   │   └── monthly_summary_YYYY-MM.json
│   └── handlers/
│       ├── restaurant_handler.py # Update with tracking
│       ├── rides_handler.py      # Update with tracking
│       └── ...
├── frontend/
│   └── cost-dashboard.html       # ✅ NEW - Optional, for monitoring
└── ...
```

---

## 🔧 Integration Steps

### Step 1: Add cost_tracker.py

Copy the `cost_tracker.py` file (attached) to your backend directory. No modifications needed.

### Step 2: Initialize Tracker in Main App

```python
# In your main app.py or __init__.py

from cost_tracker import CostTracker, create_cost_tracker_blueprint

# Initialize once at app startup
cost_tracker = CostTracker(data_dir="./cost_data")

# Register API endpoints for dashboard
app.register_blueprint(
    create_cost_tracker_blueprint(cost_tracker), 
    url_prefix='/api/costs'
)

# Make tracker available to handlers
app.config['COST_TRACKER'] = cost_tracker
```

### Step 3: Update Handlers to Log API Calls

Here's exactly what to add to each handler:

---

#### restaurant_handler.py

```python
# At the top of file
from flask import current_app

class RestaurantHandler:
    def __init__(self):
        # ... existing init code ...
        pass
    
    def _get_tracker(self):
        """Get cost tracker from app context"""
        return current_app.config.get('COST_TRACKER')
    
    def search_restaurants(self, query, location):
        """Search for restaurants using Google Places API"""
        
        # Your existing API call
        results = self._call_google_places_text_search(query, location)
        
        # ✅ ADD: Log the API call
        tracker = self._get_tracker()
        if tracker:
            tracker.log_api_call(
                api_type="text_search_pro",
                endpoint="places.searchText",
                request_count=1,
                details={
                    "query": query,
                    "location": str(location),
                    "results_count": len(results)
                }
            )
        
        return results
    
    def get_restaurant_details(self, place_id):
        """Get details for a specific restaurant"""
        
        # Your existing API call
        details = self._call_google_places_details(place_id)
        
        # ✅ ADD: Log the API call
        tracker = self._get_tracker()
        if tracker:
            tracker.log_api_call(
                api_type="place_details_pro",
                endpoint="places.get",
                details={"place_id": place_id}
            )
        
        return details
    
    def autocomplete(self, input_text, session_token=None):
        """Autocomplete suggestions"""
        
        results = self._call_google_autocomplete(input_text)
        
        # ✅ ADD: Log the API call
        tracker = self._get_tracker()
        if tracker:
            tracker.log_api_call(
                api_type="autocomplete",
                endpoint="places.autocomplete",
                details={"input": input_text[:50]}  # Truncate for privacy
            )
        
        return results
```

---

#### geocoding_service.py

```python
def geocode_address(address):
    """Convert address to lat/lng"""
    
    result = google_geocoding_api.geocode(address)
    
    # ✅ ADD: Log the API call
    tracker = current_app.config.get('COST_TRACKER')
    if tracker:
        tracker.log_api_call(
            api_type="geocoding",
            endpoint="geocode",
            details={"address": address[:100]}
        )
    
    return result
```

---

#### rides_handler.py (for future Uber/Lyft tracking)

```python
def get_ride_estimates(origin, destination):
    """Get ride price estimates"""
    
    # Uber API call
    uber_result = uber_client.get_estimates(origin, destination)
    
    # ✅ ADD: Track Uber API (when we have pricing info)
    tracker = current_app.config.get('COST_TRACKER')
    if tracker:
        tracker.log_api_call(
            api_type="uber_estimates",  # We'll add pricing later
            endpoint="uber.estimates",
            details={"origin": str(origin), "destination": str(destination)}
        )
    
    return uber_result
```

---

## 🗺️ API Type Mapping Reference

Use these exact `api_type` strings when logging:

| Google API Endpoint | api_type String | Free Cap | Cost/1000 |
|---------------------|-----------------|----------|-----------|
| Text Search (New) | `text_search_pro` | 5,000 | $32.00 |
| Nearby Search (New) | `nearby_search_pro` | 5,000 | $32.00 |
| Place Details (Pro fields) | `place_details_pro` | 5,000 | $17.00 |
| Place Details (Basic fields) | `place_details_essentials` | 10,000 | $5.00 |
| Autocomplete | `autocomplete` | 10,000 | $2.83 |
| Geocoding | `geocoding` | 10,000 | $5.00 |
| Place Photos | `place_photos` | 1,000 | $7.00 |
| Time Zone | `time_zone` | 10,000 | $5.00 |

**Important:** The `api_type` must match exactly - the cost calculator uses these keys.

---

## 📊 Dashboard Endpoints

Once integrated, these endpoints will be available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/costs/report` | GET | Full cost report (use this for dashboard) |
| `/api/costs/monthly` | GET | Monthly breakdown |
| `/api/costs/daily` | GET | Today's API calls |
| `/api/costs/budget` | GET | Budget status with alerts |
| `/api/costs/pricing` | GET | Current pricing configuration |

**Example Response from `/api/costs/budget`:**

```json
{
  "overall_status": "healthy",
  "credit_usage_pct": 12.5,
  "credit_remaining": 175.00,
  "api_alerts": [],
  "monthly_summary": {
    "total_requests": 1250,
    "gross_cost": 25.00,
    "net_cost": 0.00
  }
}
```

---

## 🎯 Alternative: Decorator Pattern

For cleaner code, use the decorator:

```python
from cost_tracker import track_api_call

tracker = CostTracker()

@track_api_call(tracker, "text_search_pro")
def search_restaurants(query, location):
    return google_places.text_search(query, location)
```

The decorator automatically logs after each function call.

---

## ⚠️ Important Notes

1. **Thread Safety:** The tracker is thread-safe - multiple requests can log simultaneously.

2. **Data Storage:** Logs are stored in JSON files under `./cost_data/`. For production, consider migrating to PostgreSQL.

3. **Free Tier Resets:** Google's free tier resets on the 1st of each month (midnight Pacific). The tracker handles this automatically.

4. **$200 Credit:** The monthly credit applies AFTER free tier is exhausted. So if you use 5,000 Text Searches (all free), you still have the full $200 credit.

5. **Field Masks:** Google charges based on fields requested. Using `place_details_essentials` (basic fields only) costs $5/1000 vs `place_details_pro` at $17/1000. Consider which fields you actually need.

---

## 📁 Attached Files

1. **cost_tracker.py** - Core tracking module (450 lines)
2. **dashboard.html** - Optional web dashboard
3. **requirements.txt** - Add `flask-cors` if not already installed

---

## ✅ Acceptance Criteria

- [ ] `cost_tracker.py` added to backend
- [ ] Tracker initialized in main app
- [ ] All Google API calls in handlers log to tracker
- [ ] `/api/costs/report` endpoint returns valid data
- [ ] Dashboard accessible and showing real data
- [ ] Alert system triggers at 70% usage (test with `/demo/heavy-usage`)

---

## 🔄 Sync Back

Once implemented, please update the Project Tracker with:
- Actual API call volumes per day
- Any adjustments needed to pricing config
- Dashboard URL for team monitoring

---

**Questions?** Flag in the Supervisor thread and I'll clarify.

**Document Status:** READY FOR IMPLEMENTATION  
**Owner:** Tech & Architecture Thread  
**Deadline:** Include in next backend deployment
