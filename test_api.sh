#!/bin/bash

echo "================================"
echo "Testing Hopwise API Endpoints"
echo "================================"

echo -e "\n1. Testing /api/health..."
curl -s http://localhost:5001/api/health | python3 -m json.tool

echo -e "\n2. Testing /api/restaurants (Italian food)..."
curl -s -X POST http://localhost:5001/api/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Times Square, NYC",
    "query": "Italian food",
    "filter_category": "Food",
    "priority": "balanced"
  }' | python3 -c "import json, sys; d = json.load(sys.stdin); print(f'Success: {d[\"success\"]}'); print(f'Total: {d[\"data\"][\"total_results\"]} restaurants'); print(f'Top: {d[\"data\"][\"restaurants\"][0][\"name\"]} ({d[\"data\"][\"restaurants\"][0][\"rating\"]}⭐)')"

echo -e "\n3. Testing /api/restaurants (Ice Cream filter)..."
curl -s -X POST http://localhost:5001/api/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Brooklyn, NY",
    "query": "ice cream",
    "filter_category": "Ice Cream",
    "priority": "distance"
  }' | python3 -c "import json, sys; d = json.load(sys.stdin); print(f'Success: {d[\"success\"]}'); print(f'Total: {d[\"data\"][\"total_results\"]} results')"

echo -e "\n4. Testing /api/stats..."
curl -s http://localhost:5001/api/stats | python3 -c "import json, sys; d = json.load(sys.stdin); print(f'Success: {d[\"success\"]}'); print(f'Cache hits: {d[\"data\"][\"cache\"][\"hits\"]}'); print(f'Cache misses: {d[\"data\"][\"cache\"][\"misses\"]}')"

echo -e "\n================================"
echo "✅ All API tests completed!"
echo "================================"
