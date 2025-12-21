# Package Structure Documentation

## Overview

The TouristCompanion project now has a clean, well-organized package structure with proper `__init__.py` files that control imports and exports.

## Package Hierarchy

```
src/
├── domains/                    # All domain implementations
│   ├── __init__.py            # Version: 0.2.0
│   ├── base/                  # Abstract base classes
│   │   ├── __init__.py        # Exports: DomainHandler, DomainQuery, DomainResult
│   │   ├── domain_handler.py  # Core domain pattern
│   │   └── README.md          # Pattern documentation
│   ├── rideshare/             # Ride comparison domain
│   │   ├── __init__.py        # Exports: RideShareHandler, RideQuery, etc.
│   │   ├── handler.py         # Domain handler implementation
│   │   ├── models.py          # RideQuery, RideEstimate
│   │   ├── intent_parser.py   # LLM-based parsing
│   │   ├── comparator.py      # AI-powered comparison
│   │   └── api_clients/       # Provider clients (Uber, Lyft)
│   └── weather/               # Weather domain (Week 1)
└── core/                       # Shared services
    ├── __init__.py            # Exports: GeocodingService
    ├── geocoding_service.py   # Location to coordinates
    ├── cache_service.py       # Generic caching
    └── base_client.py         # API client base
```

## Clean Import Examples

### Before (Without __init__.py)
```python
# Ugly imports with full paths
from domains.rideshare.handler import RideShareHandler
from domains.rideshare.models import RideQuery, RideEstimate
from domains.base.domain_handler import DomainHandler
from core.geocoding_service import GeocodingService
```

### After (With __init__.py)
```python
# Clean imports from package level
from domains.rideshare import RideShareHandler, RideQuery, RideEstimate
from domains.base import DomainHandler, DomainQuery, DomainResult
from core import GeocodingService
```

## Package Details

### 1. domains Package

**File:** `src/domains/__init__.py`

**Purpose:** Top-level package for all domain implementations

**Version:** 0.2.0 (Week 2)

**Contents:**
- base: Abstract base classes
- rideshare: Ride comparison domain
- weather: Weather domain (from Week 1)
- (future) restaurants, hotels, activities

### 2. domains.base Package

**File:** `src/domains/base/__init__.py`

**Purpose:** Abstract base classes that all domains implement

**Exports:**
- `DomainHandler` - Abstract base class for domain handlers
- `DomainQuery` - Base class for domain queries
- `DomainResult` - Base class for domain results

**Usage:**
```python
from domains.base import DomainHandler

class MyDomainHandler(DomainHandler):
    def parse_query(self, raw_query, context=None):
        # Implementation
        pass
```

### 3. domains.rideshare Package

**File:** `src/domains/rideshare/__init__.py`

**Purpose:** Ride-share comparison domain

**Providers:** Uber, Lyft, Via

**Exports:**
- `RideShareHandler` - Main handler implementing DomainHandler
- `RideQuery` - Ride-share specific query model
- `RideEstimate` - Ride estimate from providers
- `RideShareIntentParser` - LLM-based query parsing
- `RideShareComparator` - AI-powered comparison

**Usage:**
```python
from domains.rideshare import RideShareHandler
from core import GeocodingService

handler = RideShareHandler(geocoding_service=GeocodingService())
results = handler.process(
    "Get me from Times Square to JFK",
    context={"user_location": "New York"},
    priority="price"
)
```

### 4. core Package

**File:** `src/core/__init__.py`

**Purpose:** Shared services used across all domains

**Exports:**
- `GeocodingService` - Location to coordinates conversion

**Usage:**
```python
from core import GeocodingService

geocoder = GeocodingService()
lat, lng, display_name = geocoder.geocode("Times Square, New York")
```

## Benefits

### 1. Clean Imports
```python
# Single-line imports for multiple classes
from domains.rideshare import RideShareHandler, RideQuery, RideEstimate
```

### 2. Explicit API Control
Only classes listed in `__all__` are considered public API. Internal implementation details remain private.

### 3. Self-Documenting
Each package has a docstring explaining its purpose and contents:
```python
"""
Ride-share comparison domain.

Compares ride options from multiple providers (Uber, Lyft, Via).
"""
```

### 4. Version Tracking
```python
import domains
print(domains.__version__)  # "0.2.0"
```

### 5. Better IDE Support
IDEs can now provide better autocomplete and documentation since the package structure is explicit.

### 6. Easier Testing
```python
# Import only what you need for testing
from domains.base import DomainHandler
from domains.rideshare import RideShareHandler
```

## Testing

All tests pass with the new package structure:

### Test Files
- `tests/test_clean_imports.py` - Verifies clean imports work (5/5 passed)
- `tests/test_domain_handler_base.py` - Tests base classes (5/5 passed)
- `tests/test_rideshare_handler.py` - Tests rideshare handler (7/7 passed)

### Running Tests
```bash
# Test clean imports
python3 tests/test_clean_imports.py

# Test base domain handler
python3 tests/test_domain_handler_base.py

# Test rideshare handler
python3 tests/test_rideshare_handler.py

# Test main application
python3 main_rideshare.py --query "Get me from Times Square to JFK" --location "New York" --priority "price"
```

## Future Domains

When adding new domains (restaurants, hotels, activities), follow this pattern:

### 1. Create domain directory
```bash
mkdir -p src/domains/restaurants
```

### 2. Create __init__.py
```python
# src/domains/restaurants/__init__.py
"""
Restaurant comparison domain.

Compares restaurant options from multiple providers (Yelp, Google, OpenTable).
"""

from .handler import RestaurantHandler
from .models import RestaurantQuery, RestaurantOption

__all__ = [
    'RestaurantHandler',
    'RestaurantQuery',
    'RestaurantOption',
]
```

### 3. Implement handler
```python
# src/domains/restaurants/handler.py
from domains.base import DomainHandler
from .models import RestaurantQuery, RestaurantOption

class RestaurantHandler(DomainHandler):
    # Implement abstract methods
    pass
```

### 4. Use clean imports
```python
from domains.restaurants import RestaurantHandler

handler = RestaurantHandler()
results = handler.process("Find Italian restaurants nearby")
```

## Summary

✅ **Accomplished:**
- Created 4 `__init__.py` files for clean package structure
- All exports explicitly controlled via `__all__`
- Self-documenting packages with docstrings
- Version tracking at package level (0.2.0)
- All tests pass (17/17 total)
- Main application works perfectly

✅ **Benefits:**
- Cleaner imports
- Better IDE support
- Explicit public API
- Easier testing
- Self-documenting code
- Ready for new domains

✅ **Next Steps:**
- Add restaurants domain using same pattern
- Add hotels domain using same pattern
- Add activities domain using same pattern
