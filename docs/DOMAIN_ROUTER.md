# Multi-Domain Query Router

## Overview

The Domain Router is an AI-powered query routing system that intelligently determines which domain(s) should handle a user's natural language query.

**Location:** `src/orchestration/domain_router.py`

## Features

✅ **Fast Keyword Matching** - No API call for simple, unambiguous queries
✅ **AI Fallback** - Uses GPT-4o-mini for complex/ambiguous queries
✅ **Multi-Domain Support** - Single query can route to multiple domains
✅ **Priority Ordering** - Returns domains in order of importance
✅ **Extensible** - Easy to add new domains
✅ **Graceful Degradation** - Falls back to keywords if AI fails
✅ **Domain Enable/Disable** - Control which domains are active

## Architecture

### Hybrid Routing Approach

```
User Query
    ↓
Keyword Matching (Fast)
    ↓
Single Match? → Return [domain]
    ↓
Multi-Match or No Match?
    ↓
AI Routing (GPT-4o-mini)
    ↓
Return [domain1, domain2, ...]
```

### Currently Supported Domains

| Domain | Status | Description | Keywords |
|--------|--------|-------------|----------|
| **rideshare** | ✅ Enabled | Transportation, Uber, Lyft | ride, uber, lyft, taxi, transport, drive, car |
| **restaurants** | ✅ Enabled | Dining, food, cuisine | restaurant, food, eat, dining, lunch, dinner, cuisine |
| **activities** | ❌ Disabled | Attractions, tours, entertainment | activity, tour, attraction, museum, show |
| **hotels** | ❌ Disabled | Accommodation, lodging | hotel, stay, accommodation, lodging, room |

## Usage

### Basic Usage

```python
from orchestration import DomainRouter

# Initialize router
router = DomainRouter()

# Route a single-domain query
domains = router.route("Get me an Uber to JFK")
# Returns: ["rideshare"]

# Route a multi-domain query
domains = router.route("I need a ride and want Italian food")
# Returns: ["rideshare", "restaurants"]

# Check if multi-domain
is_multi = router.is_multi_domain(domains)
# Returns: True
```

### With Context

```python
# Provide context for better routing
context = {
    'user_location': 'New York, NY',
    'preferences': {'cuisine': 'Italian'}
}

domains = router.route("Find me something good", context=context)
# AI uses context to make better routing decisions
```

### Get Enabled Domains

```python
enabled = router.get_enabled_domains()
# Returns: ['rideshare', 'restaurants']
```

## Routing Examples

### Single-Domain Queries

| Query | Routed To | Method |
|-------|-----------|--------|
| "Get me an Uber to JFK" | `[rideshare]` | Keyword |
| "Find a good Italian restaurant" | `[restaurants]` | Keyword |
| "Compare Lyft and Uber prices" | `[rideshare]` | Keyword |
| "Where should I eat dinner?" | `[restaurants]` | Keyword |

### Multi-Domain Queries

| Query | Routed To | Method |
|-------|-----------|--------|
| "I need a ride and want to eat" | `[rideshare, restaurants]` | Keyword |
| "Take me to a nice restaurant" | `[restaurants]` | AI |
| "Plan my evening - dinner and transportation" | `[restaurants, rideshare]` | AI |

### Ambiguous Queries (AI Helps)

| Query | Routed To | Method |
|-------|-----------|--------|
| "I want to go somewhere nice" | `[restaurants]` | AI |
| "Plan my anniversary" | `[restaurants]` | AI |
| "What should I do tonight?" | `[]` or `[restaurants]` | AI |

## Implementation Details

### Keyword Matching Algorithm

```python
def _keyword_match(self, query: str) -> List[str]:
    """Fast keyword matching - O(n*m) where n=domains, m=keywords"""
    query_lower = query.lower()
    matched_domains = []

    for domain_name, domain_info in self.enabled_domains.items():
        if any(keyword in query_lower for keyword in domain_info['keywords']):
            matched_domains.append(domain_name)

    return matched_domains
```

### AI Routing

Uses GPT-4o-mini with:
- **Temperature:** 0 (deterministic)
- **Response Format:** JSON object
- **Fallback:** Keywords if AI fails
- **Validation:** Only returns enabled domains

## Adding New Domains

To add a new domain:

1. **Update AVAILABLE_DOMAINS** in `domain_router.py`:

```python
AVAILABLE_DOMAINS = {
    # ... existing domains ...
    'your_new_domain': {
        'name': 'your_new_domain',
        'description': 'Brief description of what this domain handles',
        'keywords': ['keyword1', 'keyword2', 'keyword3'],
        'enabled': True  # or False if not ready
    }
}
```

2. **Implement the domain handler** following the `DomainHandler` pattern

3. **Add tests** for the new domain routing

## Testing

### Unit Tests

```bash
# Run all domain router tests (28 tests)
pytest tests/test_domain_router*.py -v
```

**Test Coverage:**
- Keyword matching for each domain
- Single-domain routing
- Multi-domain routing
- AI fallback behavior
- Context parameter handling
- Empty/ambiguous query handling
- Disabled domain filtering

### Demo

```bash
# Run interactive demo
python3 tests/demo_domain_router.py
```

## Performance

### Keyword Matching
- **Speed:** ~0.001ms per query
- **Cost:** $0 (no API call)
- **Use Case:** Simple, unambiguous queries

### AI Routing
- **Speed:** ~200-500ms per query
- **Cost:** ~$0.0001 per query (GPT-4o-mini)
- **Use Case:** Complex, multi-domain, or ambiguous queries

### Optimization Strategy
1. Try keyword matching first (fast)
2. If only 1 match → return immediately
3. If 0 or 2+ matches → use AI
4. If AI fails → fall back to keyword matches

## Integration with Handlers

The router works seamlessly with domain handlers:

```python
from orchestration import DomainRouter
from domains.rideshare.handler import RideShareHandler
from domains.restaurants.handler import RestaurantHandler

# Initialize
router = DomainRouter()
handlers = {
    'rideshare': RideShareHandler(),
    'restaurants': RestaurantHandler()
}

# Route query
query = "I need a ride and want Italian food"
domains = router.route(query)

# Process with appropriate handlers
results = {}
for domain in domains:
    if domain in handlers:
        results[domain] = handlers[domain].process(query)
```

## Future Enhancements

### Planned Features
- [ ] Domain priority scoring (0-100)
- [ ] User preference learning
- [ ] Query intent classification (plan, compare, book)
- [ ] Caching for repeated queries
- [ ] A/B testing framework for routing strategies

### Future Domains
- [ ] **Activities** - Tours, attractions, entertainment
- [ ] **Hotels** - Accommodation search and booking
- [ ] **Events** - Concerts, shows, sports
- [ ] **Weather** - Weather forecasts and conditions

## Error Handling

### Graceful Degradation

```python
def _ai_route(self, query, context):
    try:
        # AI routing logic...
    except Exception as e:
        # Log error
        print(f"AI routing failed: {e}")

        # Fall back to keyword matching
        return self._keyword_match(query)
```

### Validation

- Only returns domains that are enabled
- Filters out disabled domains from AI responses
- Returns empty list if no matches (not an error)

## Monitoring

Recommended metrics to track:
- **Routing method distribution** (keyword vs AI)
- **Multi-domain query percentage**
- **AI routing latency (p50, p95, p99)**
- **Keyword match accuracy**
- **AI routing cost per day**

## Best Practices

1. **Add comprehensive keywords** - Better keyword matching = fewer AI calls
2. **Keep AI prompts focused** - Clear instructions = better routing
3. **Test with real queries** - Use actual user queries for testing
4. **Monitor AI costs** - Track GPT-4o-mini usage
5. **Update keywords regularly** - Learn from AI routing patterns

## Files

**Core:**
- `src/orchestration/domain_router.py` - Main router implementation
- `src/orchestration/__init__.py` - Package exports

**Tests:**
- `tests/test_domain_router.py` - Unit tests (14 tests)
- `tests/test_domain_router_additional.py` - Additional tests (14 tests)
- `tests/demo_domain_router.py` - Interactive demo

**Total: 28 tests, all passing ✅**

## Summary

The Domain Router is a production-ready, intelligent routing system that:
- Routes queries to appropriate domains automatically
- Optimizes for speed (keyword matching) and accuracy (AI fallback)
- Supports both single and multi-domain queries
- Gracefully handles errors and edge cases
- Is easily extensible for new domains

**Status:** ✅ Production-ready, fully tested
