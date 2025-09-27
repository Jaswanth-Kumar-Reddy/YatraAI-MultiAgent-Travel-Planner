# real_api_agents.py - Template for Real-Time API Integration

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class RealFlightAgent:
    """Real-time flight data using Amadeus API"""
    
    def __init__(self):
        self.api_key = os.getenv('AMADEUS_API_KEY')
        self.api_secret = os.getenv('AMADEUS_API_SECRET')
        self.access_token = None
        self.base_url = "https://api.amadeus.com"
        
    def get_access_token(self):
        """Get OAuth token from Amadeus"""
        if not self.api_key or not self.api_secret:
            raise ValueError("Amadeus API credentials not found in environment")
            
        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        return self.access_token
    
    def search_flights(self, from_code: str, to_code: str, date: str) -> List[Dict]:
        """Search real flights using Amadeus API"""
        if not self.access_token:
            self.get_access_token()
            
        url = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        params = {
            'originLocationCode': from_code,
            'destinationLocationCode': to_code,
            'departureDate': date,
            'adults': 1,
            'max': 10
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self.parse_amadeus_flights(data.get('data', []))
    
    def parse_amadeus_flights(self, flight_data: List[Dict]) -> List[Dict]:
        """Parse Amadeus API response to our format"""
        flights = []
        
        for offer in flight_data:
            for itinerary in offer.get('itineraries', []):
                for segment in itinerary.get('segments', []):
                    flight = {
                        'mode': 'flight',
                        'from': f"{segment['departure']['iataCode']} Airport",
                        'to': f"{segment['arrival']['iataCode']} Airport",
                        'dep_time': segment['departure']['at'],
                        'arr_time': segment['arrival']['at'],
                        'duration_min': self.parse_duration(itinerary['duration']),
                        'airline': segment['carrierCode'],
                        'flight_number': f"{segment['carrierCode']}-{segment['number']}",
                        'price_inr': self.convert_to_inr(offer['price']['total'], offer['price']['currency']),
                        'source': 'amadeus_api',
                        'availability': 'available',
                        'booking_class': segment['cabin']
                    }
                    flights.append(flight)
                    
        return flights
    
    def parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        # Example: PT2H15M -> 135 minutes
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes
        return 0
    
    def convert_to_inr(self, price: str, currency: str) -> int:
        """Convert price to INR (simplified - use real exchange rate API)"""
        price_float = float(price)
        if currency == 'USD':
            return int(price_float * 83)  # Approximate USD to INR
        elif currency == 'EUR':
            return int(price_float * 90)  # Approximate EUR to INR
        elif currency == 'INR':
            return int(price_float)
        else:
            return int(price_float * 83)  # Default to USD rate

class RealTrainAgent:
    """Real-time train data using Railway API"""
    
    def __init__(self):
        self.api_key = os.getenv('RAILWAY_API_KEY')  # RailYatri or similar
        self.base_url = "https://api.railyatri.in"  # Example
        
    def search_trains(self, from_station: str, to_station: str, date: str) -> List[Dict]:
        """Search real trains using Railway API"""
        if not self.api_key:
            raise ValueError("Railway API key not found")
            
        # This is a template - actual API endpoints vary
        url = f"{self.base_url}/trains/search"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'from': from_station,
            'to': to_station,
            'date': date
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self.parse_train_data(data.get('trains', []))
    
    def parse_train_data(self, train_data: List[Dict]) -> List[Dict]:
        """Parse railway API response"""
        trains = []
        
        for train in train_data:
            train_info = {
                'mode': 'train',
                'from': f"{train['from_station_name']} ({train['from_station_code']})",
                'to': f"{train['to_station_name']} ({train['to_station_code']})",
                'dep_time': train['departure_time'],
                'arr_time': train['arrival_time'],
                'duration_min': self.calculate_duration(train['departure_time'], train['arrival_time']),
                'train_name': train['train_name'],
                'train_number': train['train_number'],
                'price_inr': train.get('fare', 0),
                'source': 'railway_api',
                'availability': train.get('availability', 'unknown'),
                'class': train.get('class', 'SL')
            }
            trains.append(train_info)
            
        return trains
    
    def calculate_duration(self, dep_time: str, arr_time: str) -> int:
        """Calculate journey duration in minutes"""
        # Implementation depends on time format from API
        # This is a simplified example
        try:
            dep = datetime.strptime(dep_time, "%H:%M")
            arr = datetime.strptime(arr_time, "%H:%M")
            
            # Handle overnight journeys
            if arr < dep:
                arr += timedelta(days=1)
                
            duration = arr - dep
            return int(duration.total_seconds() / 60)
        except:
            return 0

class RealBusAgent:
    """Real-time bus data using RedBus API"""
    
    def __init__(self):
        self.api_key = os.getenv('REDBUS_API_KEY')
        self.base_url = "https://api.redbus.in"  # Example
        
    def search_buses(self, from_city: str, to_city: str, date: str) -> List[Dict]:
        """Search real buses using RedBus API"""
        if not self.api_key:
            raise ValueError("RedBus API key not found")
            
        # Template - actual RedBus API structure may differ
        url = f"{self.base_url}/buses/search"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'from': from_city,
            'to': to_city,
            'date': date
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self.parse_bus_data(data.get('buses', []))
    
    def parse_bus_data(self, bus_data: List[Dict]) -> List[Dict]:
        """Parse bus API response"""
        buses = []
        
        for bus in bus_data:
            bus_info = {
                'mode': 'bus',
                'from': bus['boarding_point'],
                'to': bus['dropping_point'],
                'dep_time': bus['departure_time'],
                'arr_time': bus['arrival_time'],
                'duration_min': bus.get('duration_minutes', 0),
                'operator': bus['operator_name'],
                'bus_type': bus['bus_type'],
                'price_inr': bus['fare'],
                'source': 'redbus_api',
                'availability': f"{bus['available_seats']} seats",
                'amenities': bus.get('amenities', [])
            }
            buses.append(bus_info)
            
        return buses

# Usage Example (when APIs are configured):
"""
# Set environment variables:
export AMADEUS_API_KEY="your_amadeus_key"
export AMADEUS_API_SECRET="your_amadeus_secret"
export RAILWAY_API_KEY="your_railway_key"
export REDBUS_API_KEY="your_redbus_key"

# Use in your agents:
flight_agent = RealFlightAgent()
flights = flight_agent.search_flights("DEL", "BOM", "2025-10-01")

train_agent = RealTrainAgent()
trains = train_agent.search_trains("NDLS", "MMCT", "2025-10-01")

bus_agent = RealBusAgent()
buses = bus_agent.search_buses("New Delhi", "Mumbai", "2025-10-01")
"""

# Integration with existing agents:
def upgrade_agents_to_real_api():
    """
    To upgrade your existing agents:
    
    1. Replace demo data methods with real API calls
    2. Add error handling and fallbacks
    3. Implement rate limiting
    4. Add caching for frequently requested routes
    5. Handle API quotas and costs
    """
    pass
