# Week 1: Ride-Share Foundation with Mock Data

## Day 1: Models & Core Setup ⬅️ START HERE
- [ ] Create src/domains/rideshare/models.py (RideQuery, RideEstimate)
- [ ] Create src/core/geocoding_service.py
- [ ] Test models independently

## Day 2: Intent Parser
- [ ] Create src/domains/rideshare/intent_parser.py
- [ ] Adapt from weather parser, modify prompts
- [ ] Test with 5 sample queries

## Day 3: Mock API Clients
- [ ] Create src/domains/rideshare/api_clients/mock_uber_client.py
- [ ] Create src/domains/rideshare/api_clients/mock_lyft_client.py
- [ ] Implement realistic price/time calculations

## Day 4: Comparator
- [ ] Create src/domains/rideshare/comparator.py
- [ ] Adapt from weather comparator
- [ ] Test comparison logic

## Day 5: Main Integration
- [ ] Create main_rideshare.py
- [ ] Connect all components
- [ ] Test full end-to-end flow

## Weekend: Polish & Test
- [ ] Add error handling
- [ ] Test edge cases
- [ ] Update cache service for ride-share (5 min TTL)
- [ ] Document what you built