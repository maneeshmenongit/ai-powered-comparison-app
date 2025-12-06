
import sys
sys.path.insert(0, 'src')

# Test base imports
from domains.base import DomainHandler, DomainQuery, DomainResult
print("✅ Base domain imports work")

# Test rideshare imports
from domains.rideshare import RideShareHandler, RideQuery, RideEstimate
print("✅ RideShare imports work")

# Test core imports
from core import GeocodingService
print("✅ Core imports work")

print("\n🎉 All package structures verified!")