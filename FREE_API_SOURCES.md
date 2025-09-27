# Free & Community API Sources for Real Data

## 🚂 Indian Railways (FREE - Community APIs)

### 1. Railway MCP Server (LIVE DATA)
```
URL: https://railway-mcp.amithv.xyz/mcp
Type: Model Context Protocol server
Features: Live train status, seat availability, schedules
Cost: FREE (community-maintained)
```

### 2. RailwayAPI.com (Unofficial)
```
URL: https://railwayapi.com/api/
Features: Train between stations, live status, PNR status
Cost: FREE with rate limits
Example: https://railwayapi.com/api/v2/between/source/{source_code}/dest/{dest_code}/date/{date}/
```

### 3. Indian Railways Enquiry API
```
URL: https://enquiry.indianrail.gov.in/
Features: Train schedules, fare enquiry
Cost: FREE (official but limited)
```

## ✈️ Flights (FREE - Limited)

### 1. Google Flights API (Serpapi)
```
URL: https://serpapi.com/google-flights-api
Free Tier: 100 searches/month
Features: Real flight prices, schedules
Cost: FREE tier available
```

### 2. Aviationstack API
```
URL: https://aviationstack.com/
Free Tier: 1000 requests/month
Features: Flight schedules, real-time data
Cost: FREE tier
```

### 3. FlightAware API
```
URL: https://flightaware.com/commercial/aeroapi/
Free Tier: Limited requests
Features: Flight tracking, schedules
Cost: FREE tier available
```

## 🚌 Bus APIs (Regional Coverage)

### 1. BMTC (Bangalore) - Unofficial
```
URL: https://github.com/geohacker/bmtc
Features: Bangalore bus routes, schedules
Coverage: Bangalore only
Cost: FREE (GitHub project)
```

### 2. DTC (Delhi) - Unofficial  
```
URL: https://github.com/captn3m0/dtc-api
Features: Delhi bus routes, live tracking
Coverage: Delhi NCR
Cost: FREE (community project)
```

### 3. MSRTC (Maharashtra) - Unofficial
```
URL: Various GitHub projects
Features: Maharashtra state transport
Coverage: Maharashtra routes
Cost: FREE (community-driven)
```

## 🚇 Metro APIs (City-specific)

### 1. Delhi Metro API
```
URL: https://github.com/swapagarwal/delhi-metro-api
Features: Route planning, fare calculation, station info
Coverage: Delhi NCR
Cost: FREE (open source)
```

### 2. Hyderabad Metro API
```
URL: https://github.com/hyderabad-metro/api (example)
Features: Route info, timings
Coverage: Hyderabad
Cost: FREE (if available)
```

### 3. Mumbai Metro/Local API
```
URL: https://github.com/datameet/mumbai-local-trains
Features: Local train schedules
Coverage: Mumbai
Cost: FREE (community data)
```

## 🌐 Multi-Modal APIs

### 1. OpenTripPlanner
```
URL: https://www.opentripplanner.org/
Features: Multi-modal trip planning
Coverage: Various cities (if data available)
Cost: FREE (open source)
```

### 2. Transitland API
```
URL: https://www.transit.land/
Features: Transit schedules, routes
Coverage: Global (limited India coverage)
Cost: FREE
```

## 📍 Supporting APIs

### 1. Indian Cities Database
```
URL: https://github.com/dr5hn/countries-states-cities-database
Features: City codes, coordinates
Cost: FREE
```

### 2. Airport/Station Codes
```
URL: https://github.com/datasets/airport-codes
Features: IATA codes, coordinates
Cost: FREE
```

## Implementation Priority

### Phase 1: Railways (High Success Rate)
1. **Railway MCP Server** - Primary source
2. **RailwayAPI.com** - Fallback
3. **Demo data** - Final fallback

### Phase 2: Flights (Limited but Real)
1. **Google Flights (Serpapi)** - 100 free searches
2. **Aviationstack** - 1000 free requests
3. **Demo data** - Fallback

### Phase 3: Buses (Regional)
1. **Delhi DTC API** - Delhi routes
2. **Bangalore BMTC** - Bangalore routes  
3. **Demo data** - Other cities

### Phase 4: Metro (City-specific)
1. **Delhi Metro API** - Full implementation
2. **Mumbai Local** - If available
3. **Demo data** - Other cities

## Rate Limiting Strategy

```python
# Implement smart fallbacks
def get_train_data(route):
    try:
        # Try Railway MCP first
        return railway_mcp_api(route)
    except:
        try:
            # Try RailwayAPI.com
            return railway_api_com(route)
        except:
            # Fallback to demo
            return demo_train_data(route)
```

## Legal Considerations

- ✅ **Community APIs**: Generally safe to use
- ✅ **Open Source**: MIT/GPL licensed projects
- ✅ **Free Tiers**: Within usage limits
- ⚠️ **Unofficial APIs**: Use responsibly, respect rate limits
- ⚠️ **Web Scraping**: Avoid if possible, check robots.txt
