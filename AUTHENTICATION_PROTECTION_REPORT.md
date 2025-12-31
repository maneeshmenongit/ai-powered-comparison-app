# Authentication Protection Report

## Executive Summary

**Question:** How do we test that protected endpoints are restricted from guest users like saved and profile?

**Answer:** We tested the endpoints and found that **saved restaurant endpoints are currently UNPROTECTED** and allow guest users with only a `device_id` to access them.

---

## Test Results

### Protected Endpoints ✅

These endpoints correctly require JWT authentication:

| Endpoint | Method | Status | Auth Required |
|----------|--------|--------|---------------|
| `/api/auth/me` | GET | 401 | ✅ JWT Required |
| `/api/auth/logout` | POST | - | ✅ JWT Required (has `@jwt_required()`) |

### UNPROTECTED Endpoints ❌

These endpoints currently allow guest users with only `device_id`:

| Endpoint | Method | Status | Current Behavior |
|----------|--------|--------|------------------|
| `/api/user/saved` | GET | 200 | ❌ Allows device_id access |
| `/api/user/saved` | POST | 201 | ❌ Allows device_id access |
| `/api/user/saved/<id>` | DELETE | 404 | ❓ May allow device_id access |

---

## Current Implementation

### Code Analysis

**File:** `api/app.py`

#### Saved Restaurants Endpoints (Lines 608-778)

```python
# POST /api/user/saved - NO @jwt_required() decorator
@app.route('/api/user/saved', methods=['POST'])
def save_restaurant():
    # Uses device_id from header or request body
    device_id = data.get('device_id') or request.headers.get('X-Device-ID') or str(uuid.uuid4())
    user = get_or_create_user(device_id, db)  # Creates guest user
    # ...saves restaurant for guest user

# GET /api/user/saved - NO @jwt_required() decorator
@app.route('/api/user/saved', methods=['GET'])
def get_saved_restaurants():
    # Uses device_id from header or query param
    device_id = request.headers.get('X-Device-ID') or request.args.get('device_id')
    user = db.query(User).filter(User.device_id == device_id).first()
    # ...returns saved restaurants for guest user

# DELETE /api/user/saved/<id> - NO @jwt_required() decorator
@app.route('/api/user/saved/<int:saved_id>', methods=['DELETE'])
def delete_saved_restaurant(saved_id):
    # Uses device_id from header
    device_id = request.headers.get('X-Device-ID')
    # ...deletes restaurant for guest user
```

**Issue:** These endpoints use the `device_id` pattern which was designed to support **both**:
- Guest users (unauthenticated, identified by device_id)
- Authenticated users (with JWT tokens)

However, this creates a security concern if we want to restrict saved restaurants to authenticated users only.

---

## Security Implications

### Current State (UNPROTECTED)

**Pros:**
- Allows guest users to save restaurants before creating an account
- Better user experience (no forced registration)
- Guest data can be migrated when user registers

**Cons:**
- ❌ Anyone with a device_id can save/view/delete restaurants
- ❌ No authentication required for user data
- ❌ Potential for abuse (spam, fake data)
- ❌ Cannot enforce user-specific business logic
- ❌ Cannot implement premium features

### Recommended State (PROTECTED)

**Pros:**
- ✅ Only authenticated users can save restaurants
- ✅ User data is protected
- ✅ Can implement premium features
- ✅ Can enforce rate limits per user
- ✅ Better data integrity

**Cons:**
- Requires users to register/login before saving
- Slightly reduced initial user experience

---

## How To Fix

### Option 1: Require JWT for All Saved Endpoints (Recommended)

Add `@jwt_required()` decorator to all saved restaurant endpoints:

```python
@app.route('/api/user/saved', methods=['POST'])
@jwt_required()  # ADD THIS
def save_restaurant():
    # Get user from JWT token instead of device_id
    user_id = get_jwt_identity()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Rest of the code...

@app.route('/api/user/saved', methods=['GET'])
@jwt_required()  # ADD THIS
def get_saved_restaurants():
    # Get user from JWT token
    user_id = get_jwt_identity()
    user = db.query(User).filter(User.id == user_id).first()
    # ...

@app.route('/api/user/saved/<int:saved_id>', methods=['DELETE'])
@jwt_required()  # ADD THIS
def delete_saved_restaurant(saved_id):
    # Get user from JWT token
    user_id = get_jwt_identity()
    # ...
```

**Frontend Changes Required:**
- Update `hopwise-api.js` to send JWT token instead of device_id
- Remove `X-Device-ID` header
- Ensure `window.authManager.getAuthHeader()` is called for all requests

### Option 2: Hybrid Approach (More Complex)

Support both guest users AND authenticated users:

```python
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from functools import wraps

def jwt_optional_with_device_fallback(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                # Authenticated user
                request.user_type = 'authenticated'
                request.user_id = user_id
            else:
                # Guest user
                device_id = request.headers.get('X-Device-ID')
                if not device_id:
                    return jsonify({'error': 'Authentication required'}), 401
                request.user_type = 'guest'
                request.device_id = device_id
        except:
            # Fallback to device_id
            device_id = request.headers.get('X-Device-ID')
            if not device_id:
                return jsonify({'error': 'Authentication required'}), 401
            request.user_type = 'guest'
            request.device_id = device_id

        return fn(*args, **kwargs)
    return wrapper
```

---

## Testing Guide

### Manual Test with cURL

#### 1. Test Without Authentication (Should Fail if Protected)

```bash
# Try to save restaurant with device_id only
curl -X POST http://localhost:5001/api/user/saved \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: test-device-123" \
  -d '{
    "restaurant_id": "test123",
    "restaurant_data": {"name": "Test", "rating": 4.0}
  }'

# Expected if PROTECTED: 401 Unauthorized
# Current result: 201 Created (UNPROTECTED)
```

#### 2. Test With Authentication (Should Succeed)

```bash
# First, register/login to get token
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Save the access_token from response
TOKEN="your_token_here"

# Try to save with JWT token
curl -X POST http://localhost:5001/api/user/saved \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "restaurant_id": "test456",
    "restaurant_data": {"name": "Auth Test", "rating": 5.0}
  }'

# Expected: 201 Created
```

### Automated Test

Run the provided test script:

```bash
./venv/bin/python test_endpoint_protection.py
```

**Current Output:**
```
1. GET /api/user/saved with device_id only (no JWT token):
   Status: 200
   ❌ UNPROTECTED - Guest users can access this endpoint!

2. POST /api/user/saved with device_id only (no JWT token):
   Status: 201
   ❌ UNPROTECTED - Guest users can save restaurants!

4. GET /api/auth/me without JWT token:
   Status: 401
   ✅ PROTECTED - Requires JWT token
```

---

## Recommendation

**For Production:** Add `@jwt_required()` to all `/api/user/saved` endpoints (Option 1)

**Reasoning:**
1. Better security - only authenticated users can save data
2. Enables premium features and user-specific limits
3. Simpler implementation (no hybrid logic)
4. Industry standard practice
5. Frontend already has auth system in place

**Migration Path:**
1. Add `@jwt_required()` decorators
2. Update endpoints to use `get_jwt_identity()` instead of device_id
3. Update frontend API calls to use JWT auth headers
4. Test thoroughly
5. Deploy

---

## Files Modified for Testing

1. `test_endpoint_protection.py` - Quick endpoint protection check
2. `test_auth_protection.py` - Comprehensive auth test suite
3. `AUTHENTICATION_PROTECTION_REPORT.md` - This report

## Next Steps

1. **Decide:** Choose Option 1 (JWT required) or Option 2 (Hybrid)
2. **Implement:** Add authentication protection to saved endpoints
3. **Update Frontend:** Modify API calls to use JWT tokens
4. **Test:** Run automated tests
5. **Document:** Update API documentation
6. **Deploy:** Roll out changes

---

**Report Generated:** 2025-12-30
**API Version:** 1.0.0
**Test Port:** 5001
