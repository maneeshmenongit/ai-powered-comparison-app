# Favorites API Documentation

## Overview

The Favorites API allows users to save restaurants to their personal collection using a device-based identification system. No login is required - users are tracked by a unique device ID.

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Saved Restaurants Table
```sql
CREATE TABLE saved_restaurants (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id VARCHAR(255) NOT NULL,
    restaurant_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### 1. Save a Restaurant

**POST** `/api/user/saved`

Save a restaurant to the user's favorites.

**Request Headers:**
- `X-Device-ID` (optional): UUID string for the device
- `Content-Type`: application/json

**Request Body:**
```json
{
  "device_id": "optional-uuid-here",
  "restaurant_id": "ChIJ...",
  "restaurant_data": {
    "place_id": "ChIJ...",
    "name": "Restaurant Name",
    "rating": 4.5,
    "price_level": 2,
    "vicinity": "123 Main St",
    "... any other restaurant fields ..."
  }
}
```

**Success Response:** `201 Created`
```json
{
  "success": true,
  "device_id": "generated-or-provided-uuid",
  "data": {
    "id": 1,
    "user_id": 1,
    "restaurant_id": "ChIJ...",
    "restaurant_data": { ... },
    "created_at": "2025-12-29T10:00:00.000000"
  }
}
```

**Error Responses:**

`400 Bad Request` - Missing required fields
```json
{
  "success": false,
  "error": "Missing required fields: restaurant_id, restaurant_data"
}
```

`409 Conflict` - Restaurant already saved
```json
{
  "success": false,
  "error": "Restaurant already saved",
  "data": { ... }
}
```

---

### 2. Get Saved Restaurants

**GET** `/api/user/saved`

Retrieve all restaurants saved by the user.

**Request Headers:**
- `X-Device-ID`: UUID string for the device

**Alternative: Query Parameter**
- `?device_id=uuid-string`

**Success Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "restaurant_id": "ChIJ...",
      "restaurant_data": {
        "place_id": "ChIJ...",
        "name": "Restaurant Name",
        "rating": 4.5,
        ...
      },
      "created_at": "2025-12-29T10:00:00.000000"
    }
  ]
}
```

**Empty State Response:** `200 OK`
```json
{
  "success": true,
  "data": [],
  "message": "No saved restaurants found"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "success": false,
  "error": "Missing device_id in header or query parameter"
}
```

---

### 3. Delete Saved Restaurant

**DELETE** `/api/user/saved/<saved_id>`

Remove a restaurant from the user's favorites.

**URL Parameters:**
- `saved_id`: Integer ID of the saved restaurant

**Request Headers:**
- `X-Device-ID`: UUID string for the device

**Success Response:** `200 OK`
```json
{
  "success": true,
  "message": "Restaurant removed from saved items"
}
```

**Error Responses:**

`400 Bad Request` - Missing device ID
```json
{
  "success": false,
  "error": "Missing X-Device-ID header"
}
```

`404 Not Found` - User not found
```json
{
  "success": false,
  "error": "User not found"
}
```

`404 Not Found` - Saved restaurant not found
```json
{
  "success": false,
  "error": "Saved restaurant not found"
}
```

## Usage Example

### JavaScript/TypeScript (Frontend)

```javascript
// Generate or retrieve device ID (store in localStorage)
const getDeviceId = () => {
  let deviceId = localStorage.getItem('device_id');
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem('device_id', deviceId);
  }
  return deviceId;
};

const deviceId = getDeviceId();

// Save a restaurant
async function saveRestaurant(restaurant) {
  const response = await fetch('https://api.hopwise.app/api/user/saved', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Device-ID': deviceId
    },
    body: JSON.stringify({
      restaurant_id: restaurant.place_id,
      restaurant_data: restaurant
    })
  });

  return await response.json();
}

// Get saved restaurants
async function getSavedRestaurants() {
  const response = await fetch('https://api.hopwise.app/api/user/saved', {
    headers: {
      'X-Device-ID': deviceId
    }
  });

  return await response.json();
}

// Delete saved restaurant
async function deleteSavedRestaurant(savedId) {
  const response = await fetch(`https://api.hopwise.app/api/user/saved/${savedId}`, {
    method: 'DELETE',
    headers: {
      'X-Device-ID': deviceId
    }
  });

  return await response.json();
}
```

### Python (Testing)

```python
import requests
import uuid

device_id = str(uuid.uuid4())

# Save restaurant
response = requests.post(
    'http://localhost:5001/api/user/saved',
    json={
        'device_id': device_id,
        'restaurant_id': 'ChIJ...',
        'restaurant_data': {
            'place_id': 'ChIJ...',
            'name': 'Test Restaurant',
            'rating': 4.5
        }
    }
)

# Get saved restaurants
response = requests.get(
    'http://localhost:5001/api/user/saved',
    headers={'X-Device-ID': device_id}
)

# Delete saved restaurant
response = requests.delete(
    f'http://localhost:5001/api/user/saved/{saved_id}',
    headers={'X-Device-ID': device_id}
)
```

## Implementation Notes

### Device ID Generation
- Frontend should generate a UUID on first use and store it in localStorage
- Backend will auto-generate if not provided in save request
- Always return the device_id to the frontend for storage

### Data Storage
- Full restaurant object is stored as JSONB for offline access
- No need to re-fetch restaurant data from Google Places API
- Allows the app to work offline with saved restaurants

### User Model
- Users are created automatically when they save their first restaurant
- No email, password, or authentication required
- Device ID is the only identifier

### Security Considerations
- Device-based system means data is tied to the device
- If user clears localStorage, they lose access to their saves
- Future enhancement: allow users to backup/export their device ID
- Consider rate limiting to prevent abuse

## Database Initialization

The database tables are created automatically on server startup. To manually initialize:

```bash
python test_db.py
```

Or from Python:
```python
from api.db_init import initialize_database
initialize_database()
```

## Testing

Run the test suite:
```bash
python test_favorites_api.py
```

This will test:
1. Saving a restaurant
2. Preventing duplicate saves
3. Retrieving saved restaurants
4. Deleting saved restaurants
5. Verifying empty state after deletion

## Environment Setup

Required environment variables:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

The DATABASE_URL is configured in `.env` for local development and should be set in Railway for production.

## Future Enhancements

1. **Collections/Lists**: Allow users to organize saves into collections
2. **Notes**: Let users add personal notes to saved restaurants
3. **Sharing**: Generate shareable links for favorite lists
4. **Cloud Sync**: Allow users to backup their device ID for multi-device access
5. **Analytics**: Track which restaurants are saved most often
