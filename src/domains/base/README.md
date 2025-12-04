# Domain Handler Base Pattern

## Overview

The Domain Handler pattern provides a consistent, extensible architecture for adding new domains to the Tourist Companion app. Each domain (rideshare, restaurants, hotels, activities) implements the same interface, making the codebase predictable and maintainable.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DomainHandler                            │
│                   (Abstract Base Class)                      │
├─────────────────────────────────────────────────────────────┤
│  + parse_query()      : Natural language → Query            │
│  + fetch_options()    : Query → Options from providers      │
│  + compare_options()  : Options → AI recommendation         │
│  + format_results()   : Results → Display format            │
│  + process()          : Orchestrate full pipeline           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────┴────────┐  ┌───────┴────────┐  ┌──────┴────────┐
│  RideShare     │  │  Restaurant    │  │  Hotel        │
│  Handler       │  │  Handler       │  │  Handler      │
└────────────────┘  └────────────────┘  └───────────────┘
```

## Core Classes

### 1. DomainQuery (Base)

Base class for all domain queries. Subclasses add domain-specific fields.

```python
@dataclass
class DomainQuery:
    raw_query: str
    user_location: Optional[str] = None
    user_preferences: Optional[Dict] = None
```

**Example Subclass:**
```python
@dataclass
class RideQuery(DomainQuery):
    origin: str
    destination: str
    providers: List[str]
    vehicle_type: str = "standard"
```

### 2. DomainResult (Base)

Base class for all provider results. Subclasses add domain-specific data.

```python
@dataclass
class DomainResult:
    provider: str
    score: float  # 0-100
    metadata: Optional[Dict] = None
```

**Example Subclass:**
```python
@dataclass
class RideEstimate(DomainResult):
    vehicle_type: str
    price_estimate: float
    duration_minutes: int
    pickup_eta_minutes: int
    distance_miles: float
```

### 3. DomainHandler (Abstract)

Abstract base class defining the interface all domains must implement.

**Abstract Methods:**
- `parse_query()` - Parse natural language into structured query
- `fetch_options()` - Get options from multiple providers
- `compare_options()` - AI-powered comparison
- `format_results()` - Format for display

**Concrete Method:**
- `process()` - Orchestrates the full pipeline

## Implementation Guide

### Step 1: Define Domain Models

Create domain-specific query and result classes:

```python
# src/domains/restaurants/models.py

from dataclasses import dataclass
from ..base import DomainQuery, DomainResult

@dataclass
class RestaurantQuery(DomainQuery):
    """Restaurant search query."""
    cuisine: str
    location: str
    price_level: str = "$$"  # $, $$, $$$, $$$$
    party_size: int = 2

@dataclass
class RestaurantOption(DomainResult):
    """Restaurant option from a provider."""
    name: str
    rating: float
    price_level: str
    cuisine: str
    address: str
    distance_miles: float
```

### Step 2: Implement Domain Handler

Create handler implementing all abstract methods:

```python
# src/domains/restaurants/handler.py

from typing import List, Dict, Optional
from ..base import DomainHandler
from .models import RestaurantQuery, RestaurantOption

class RestaurantHandler(DomainHandler):
    """Handler for restaurant domain."""

    def parse_query(self, raw_query: str, context: Dict = None) -> RestaurantQuery:
        """Parse natural language into restaurant query."""
        # Use LLM to extract: cuisine, location, price_level, party_size
        # Implementation here...
        pass

    def fetch_options(self, query: RestaurantQuery) -> List[RestaurantOption]:
        """Fetch restaurants from Yelp, Google, OpenTable."""
        # Call APIs for each provider
        # Implementation here...
        pass

    def compare_options(self, options: List[RestaurantOption],
                       priority: str = "balanced") -> str:
        """AI comparison of restaurants."""
        # Use LLM to compare based on ratings, reviews, distance
        # Implementation here...
        pass

    def format_results(self, options: List[RestaurantOption],
                      comparison: str) -> Dict:
        """Format results for Rich table display."""
        # Create table with name, rating, price, distance
        # Implementation here...
        pass
```

### Step 3: Use the Handler

```python
# In main application
from domains.restaurants.handler import RestaurantHandler

handler = RestaurantHandler(
    cache_service=cache,
    geocoding_service=geocoder
)

# Single method call does everything!
results = handler.process(
    "Find Italian restaurants nearby",
    context={"user_location": "Manhattan"},
    priority="quality"
)

# results contains:
# {
#   "query": RestaurantQuery(...),
#   "options": [RestaurantOption(...), ...],
#   "recommendation": "Try Joe's Pizza...",
#   "metadata": {...}
# }
```

## Pipeline Flow

The `process()` method orchestrates this flow:

```
User Query
    ↓
┌──────────────────┐
│  parse_query()   │  → DomainQuery object
└────────┬─────────┘
         ↓
┌──────────────────┐
│ fetch_options()  │  → List[DomainResult]
└────────┬─────────┘
         ↓
┌──────────────────┐
│compare_options() │  → Recommendation string
└────────┬─────────┘
         ↓
┌──────────────────┐
│ format_results() │  → Display-ready dict
└────────┬─────────┘
         ↓
    Final Results
```

## Benefits

### 1. Consistency
- All domains work the same way
- Predictable behavior
- Easy to understand

### 2. Extensibility
- Add new domains by implementing 4 methods
- No changes to core application
- Plug-and-play architecture

### 3. Testability
- Each method can be tested independently
- Easy to mock services
- Clear separation of concerns

### 4. Maintainability
- Domain logic isolated
- Changes don't affect other domains
- Clear dependencies

## Testing

```python
# tests/test_restaurant_handler.py

from domains.restaurants.handler import RestaurantHandler

def test_parse_query():
    handler = RestaurantHandler()
    query = handler.parse_query("Find Italian restaurants")
    assert query.cuisine == "Italian"

def test_fetch_options():
    handler = RestaurantHandler()
    query = RestaurantQuery(cuisine="Italian", location="Manhattan")
    options = handler.fetch_options(query)
    assert len(options) > 0

def test_full_pipeline():
    handler = RestaurantHandler()
    results = handler.process("Find Italian restaurants nearby")
    assert "options" in results
    assert "recommendation" in results
```

## Existing Implementation

### RideShare Domain ✅

The rideshare domain already exists but needs refactoring to use this pattern:

**Current Files:**
- `src/domains/rideshare/models.py` - Already has query/result classes
- `src/domains/rideshare/intent_parser.py` - Implements parsing
- `src/domains/rideshare/comparator.py` - Implements comparison
- `src/domains/rideshare/api_clients/` - Implements fetching

**Refactoring Task:**
Create `src/domains/rideshare/handler.py` that wraps existing components into the DomainHandler interface.

## Future Domains

Following this pattern, adding new domains becomes trivial:

### Restaurants
- **Providers**: Yelp, Google Places, OpenTable
- **Comparison**: Rating, price, distance, reviews
- **Query params**: Cuisine, location, price_level, party_size

### Hotels
- **Providers**: Booking.com, Hotels.com, Airbnb
- **Comparison**: Price, rating, amenities, location
- **Query params**: Check-in, check-out, guests, location

### Activities
- **Providers**: Viator, GetYourGuide, TripAdvisor
- **Comparison**: Rating, price, duration, availability
- **Query params**: Activity type, date, duration, location

## Design Decisions

### Why Abstract Base Class?

- **Enforces interface**: Can't instantiate without implementing methods
- **Type safety**: Clear contract for all handlers
- **Documentation**: Abstract methods serve as documentation

### Why Separate Query/Result Classes?

- **Type safety**: Prevents mixing domains
- **Clarity**: Explicit about what each domain needs
- **Extensibility**: Easy to add domain-specific fields

### Why process() is Concrete?

- **Consistency**: Same pipeline for all domains
- **Simplicity**: Users call one method, not four
- **Debugging**: Easier to add logging/monitoring

## Common Patterns

### Using Cache Service

```python
def fetch_options(self, query: DomainQuery) -> List[DomainResult]:
    # Check cache first
    if self.cache:
        cache_key = self._generate_cache_key(query)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

    # Fetch from APIs
    options = self._fetch_from_apis(query)

    # Store in cache
    if self.cache:
        self.cache.set(cache_key, options)

    return options
```

### Using Geocoding Service

```python
def parse_query(self, raw_query: str, context: Dict = None) -> DomainQuery:
    # Extract location name from query
    location_name = self._extract_location(raw_query)

    # Geocode if service available
    if self.geocoder:
        lat, lng, display_name = self.geocoder.geocode(location_name)
        location = {"lat": lat, "lng": lng, "name": display_name}
    else:
        location = {"name": location_name}

    return DomainQuery(location=location)
```

## Error Handling

Each method should raise appropriate exceptions:

```python
def parse_query(self, raw_query: str, context: Dict = None) -> DomainQuery:
    if not raw_query:
        raise ValueError("Query cannot be empty")

    # Parse...
    if not parsed_location:
        raise ValueError("Could not determine location from query")

    return DomainQuery(...)
```

## Summary

The Domain Handler pattern provides a robust, scalable architecture for building multi-domain applications. By implementing these abstract classes, each domain gets:

- ✅ Consistent interface
- ✅ Built-in pipeline orchestration
- ✅ Easy testing
- ✅ Clear separation of concerns
- ✅ Shared services (cache, geocoding)

Next steps: Refactor rideshare domain to use this pattern, then add restaurant domain.
