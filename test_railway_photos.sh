#!/bin/bash
# Test Railway photos every 30 seconds until Google Places works

echo "=========================================="
echo "TESTING RAILWAY PHOTOS"
echo "=========================================="
echo ""
echo "This will test every 30 seconds until Google Places photos appear..."
echo ""

count=1
while true; do
    echo "Test #$count - $(date +%H:%M:%S)"

    # Make API call and check for google_places provider
    response=$(curl -s -X POST 'https://hopwise-api.up.railway.app/api/restaurants' \
        -H 'Content-Type: application/json' \
        -d '{"location": "Times Square, NYC", "query": "Italian", "filter_category": "Food", "priority": "rating", "use_ai": false}')

    # Check if google_places appears in response
    if echo "$response" | grep -q "google_places"; then
        echo "✅ SUCCESS! Google Places is working!"
        echo ""

        # Show photo info
        echo "$response" | python3 -m json.tool | grep -A 5 "google_places" | head -20
        echo ""
        echo "Photos are now working on Railway!"
        break
    else
        echo "   Still only Yelp results... (API restrictions propagating)"
    fi

    echo ""
    count=$((count + 1))
    sleep 30
done
