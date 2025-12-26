# Domain Routing Implementation

## Overview

The domain router intelligently routes user queries to the appropriate backend domain (rideshare or restaurants) using a combination of keyword matching and AI-powered routing.

## How It Works

### 1. Keyword Matching (Fast Path)

The router first attempts simple keyword matching:

**Rideshare Keywords:**
- ride, uber, lyft, taxi, transport, drive, car, get to, go to

**Restaurant Keywords:**
- restaurant, food, eat, dining, lunch, dinner, cuisine, meal

**Examples:**
```
"need a ride to times square" → matches "ride" → rideshare
"find me Italian food" → matches "food" → restaurants
"uber to central park" → matches "uber" → rideshare
```

### 2. AI Routing (Fallback)

When keyword matching returns 0 or 2+ matches, the router uses GPT-4o-mini for intelligent routing:

**Examples:**
```
"best pizza near me" → no keyword match → AI routes to restaurants
"get me to JFK airport" → no keyword match → AI routes to rideshare
```

## API Endpoints

### Unified Search (Recommended)

**Endpoint:** `POST /api/search`

**Request:**
```json
{
  "query": "need a ride to times square",
  "location": "Central Park, NYC"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "domain": "rideshare",
  "query_parsed": {
    "origin": "Central Park, NYC",
    "destination": "Times Square"
  },
  "data": {
    "rides": [...],
    "aiRecommendation": "..."
  }
}
```

### Domain-Specific Endpoints

Still available for direct access:

- `POST /api/rides` - Direct rideshare comparison
- `POST /api/restaurants` - Direct restaurant search

## Testing

### Test Domain Router

```bash
python test_domain_router.py
```

This tests the routing logic with various queries and shows:
- Which keywords matched
- Which domain was selected
- Whether keyword or AI routing was used

### Test Unified Search API

```bash
# Start the API server first
python api/app.py

# In another terminal:
python test_unified_search.py
```

This tests the actual API endpoint with real queries.

## Debug Logging

The domain router includes comprehensive logging:

```
[DomainRouter] Query: 'need a ride to times square'
[DomainRouter] Keyword matches: ['rideshare']
[DomainRouter] Single match, using: ['rideshare']
```

Check Railway logs or local console to see routing decisions.

## Frontend Integration

### Current State

The frontend currently calls domain-specific endpoints directly:
- `HopwiseAPI.searchRestaurants()` → `/api/restaurants`
- `HopwiseAPI.compareRides()` → `/api/rides`

### To Enable Smart Routing

Add a new method to `frontend/js/hopwise-api.js`:

```javascript
// Unified search with automatic domain routing
async unifiedSearch(query, location = '') {
    return this.request('/search', {
        method: 'POST',
        body: JSON.stringify({ query, location })
    });
}
```

Then update the search handler in `frontend/js/app.js`:

```javascript
async function handleSearch(event) {
    event.preventDefault();
    const query = DOM.homeSearchInput?.value || DOM.searchInput?.value || '';

    // Use unified search
    const api = new HopwiseAPI();
    const result = await api.unifiedSearch(query, 'Times Square, NYC');

    // Route to appropriate page based on domain
    if (result.domain === 'rideshare') {
        navigateTo('rides');
        renderRideResults(result.data.rides);
    } else {
        navigateTo('search');
        renderSearchResults(result.data.results);
    }
}
```

## Query Parsing

### Rideshare Queries

The unified search endpoint parses rideshare queries to extract origin and destination:

**Pattern: "to [destination]"**
```
"need a ride to times square"
→ origin: "Times Square, NYC" (from location param or default)
→ destination: "Times Square"
```

**Pattern: "from [origin] to [destination]"**
```
"ride from central park to jfk airport"
→ origin: "Central Park"
→ destination: "Jfk Airport"
```

### Restaurant Queries

Queries are passed directly to the restaurant handler with location context.

## Configuration

### Adding New Domains

Edit `src/orchestration/domain_router.py`:

```python
AVAILABLE_DOMAINS = {
    'new_domain': {
        'name': 'new_domain',
        'description': 'Description for AI routing',
        'keywords': ['keyword1', 'keyword2'],
        'enabled': True
    }
}
```

### Adjusting Keywords

Modify the `keywords` list in `AVAILABLE_DOMAINS` to improve routing accuracy.

## Performance

- **Keyword matching:** ~1ms (synchronous, no API call)
- **AI routing:** ~200-500ms (OpenAI API call)
- **Cache:** Domain routing uses GPT-4o-mini with temperature=0 for consistent results

## Error Handling

If the domain router fails:
1. AI routing falls back to keyword matching
2. Unified search returns 400 if no domain can be determined
3. All errors are logged with stack traces

## Monitoring

Check these metrics:
- Domain routing decisions (logged to console/Railway)
- Query patterns that trigger AI routing
- Routing accuracy (correct domain vs expected)

## Future Enhancements

1. **NLP-based location extraction** - Better parsing of "from X to Y"
2. **Multi-domain queries** - Support "find a ride and restaurant"
3. **User feedback loop** - Learn from corrections
4. **Caching routing decisions** - Cache domain for similar queries
5. **More domains** - Activities, hotels, etc.
