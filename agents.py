# agents.py
import json
import requests
import os
from datetime import datetime, timedelta
from utils import load_demo_for_query, iso_to_dt, dt_to_iso

# ---- IngestAgent ----
class IngestAgent:
    def run(self, query):
        """
        Given a structured query, decide the high-level mode steps.
        This now creates a more intelligent routing plan based on distance and available transport.
        """
        from_location = query["from"]
        to_location = query["to"]
        date = query["date"]
        
        # For direct routes (same city or very close), provide multiple local options
        if self._is_same_city(from_location, to_location):
            return [
                {"mode": "bus", "from": from_location, "to": to_location, "date": date},
                {"mode": "train", "from": from_location, "to": to_location, "date": date}
            ]
        
        # For long-distance routes, provide multiple options
        if self._is_long_distance(from_location, to_location):
            options = []
            if self._is_very_long_distance(from_location, to_location):
                # Very long distance: prioritize flight, but also offer train
                options.append({"mode": "flight", "from": from_location, "to": to_location, "date": date})
                options.append({"mode": "train", "from": from_location, "to": to_location, "date": date})
                options.append({"mode": "bus", "from": from_location, "to": to_location, "date": date})
            else:
                # Long distance: prioritize train, but also offer flight and bus
                options.append({"mode": "train", "from": from_location, "to": to_location, "date": date})
                options.append({"mode": "flight", "from": from_location, "to": to_location, "date": date})
                options.append({"mode": "bus", "from": from_location, "to": to_location, "date": date})
            return options
        
        # For medium distances, provide bus and train options
        return [
            {"mode": "bus", "from": from_location, "to": to_location, "date": date},
            {"mode": "train", "from": from_location, "to": to_location, "date": date}
        ]
    
    def _is_same_city(self, from_loc, to_loc):
        """Check if locations are in the same city"""
        from_city = from_loc.split(",")[0].strip().lower()
        to_city = to_loc.split(",")[0].strip().lower()
        return from_city == to_city
    
    def _is_long_distance(self, from_loc, to_loc):
        """Estimate if route is long distance (should use train)"""
        try:
            from geopy.geocoders import Nominatim
            from geopy.distance import geodesic
            
            geolocator = Nominatim(user_agent="travel_planner")
            
            from_coords = geolocator.geocode(from_loc)
            to_coords = geolocator.geocode(to_loc)
            
            if from_coords and to_coords:
                distance_km = geodesic(
                    (from_coords.latitude, from_coords.longitude),
                    (to_coords.latitude, to_coords.longitude)
                ).kilometers
                
                # Consider long distance if > 200km
                return distance_km > 200
            
        except Exception as e:
            print(f"Error calculating distance: {e}")
        
        # Fallback: assume long distance for different states
        from_state = from_loc.split(",")[-2].strip().lower() if len(from_loc.split(",")) > 1 else ""
        to_state = to_loc.split(",")[-2].strip().lower() if len(to_loc.split(",")) > 1 else ""
        
        return from_state != to_state and from_state != "" and to_state != ""
    
    def _is_very_long_distance(self, from_loc, to_loc):
        """Estimate if route is very long distance (should use flight)"""
        # Simple heuristic: major city pairs that are far apart
        major_city_pairs = [
            ("delhi", "mumbai"), ("delhi", "bangalore"), ("delhi", "chennai"), ("delhi", "kolkata"),
            ("mumbai", "bangalore"), ("mumbai", "chennai"), ("mumbai", "kolkata"),
            ("bangalore", "chennai"), ("bangalore", "kolkata"),
            ("chennai", "kolkata")
        ]
        
        from_city = from_loc.split(",")[0].strip().lower()
        to_city = to_loc.split(",")[0].strip().lower()
        
        for city1, city2 in major_city_pairs:
            if ((city1 in from_city and city2 in to_city) or 
                (city2 in from_city and city1 in to_city)):
                return True
        
# ---- FlightAgent ----
class FlightAgent:
    def __init__(self, mode="static"):
        self.mode = mode
        # Amadeus API credentials (if using API mode)
        self.amadeus_api_key = os.getenv('AMADEUS_API_KEY')
        self.amadeus_api_secret = os.getenv('AMADEUS_API_SECRET')
        
        # Initialize hybrid agent for real data
        if mode == "hybrid":
            from hybrid_agents import HybridFlightAgent
            self.hybrid_agent = HybridFlightAgent()
        self.amadeus_base_url = "https://test.api.amadeus.com"  # Sandbox URL

    def run(self, req):
        if self.mode == "hybrid":
            # Use hybrid agent for real data with fallbacks
            return self.hybrid_agent.search_flights(req['from'], req['to'], req['date'])
        elif self.mode == "static":
            # Generate multiple flight options with realistic pricing
            base_price = self._estimate_flight_price(req['from'], req['to'])
            flights = []
            
            # Morning flight - premium pricing
            flights.append({
                "mode": "flight",
                "from": f"{self._get_airport_name(req['from'])}",
                "to": f"{self._get_airport_name(req['to'])}",
                "dep_time": f"{req['date']}T06:30:00+05:30",
                "arr_time": f"{req['date']}T08:45:00+05:30",
                "duration_min": 135,
                "price_inr": int(base_price * 1.3),
                "availability": "available",
                "source": "static_demo",
                "airline": "IndiGo",
                "flight_number": "6E-123"
            })
            
            # Afternoon flight - standard pricing
            flights.append({
                "mode": "flight",
                "from": f"{self._get_airport_name(req['from'])}",
                "to": f"{self._get_airport_name(req['to'])}",
                "dep_time": f"{req['date']}T14:20:00+05:30",
                "arr_time": f"{req['date']}T16:35:00+05:30",
                "duration_min": 135,
                "price_inr": base_price,
                "availability": "available",
                "source": "static_demo",
                "airline": "SpiceJet",
                "flight_number": "SG-456"
            })
            
            # Evening flight - budget pricing
            flights.append({
                "mode": "flight",
                "from": f"{self._get_airport_name(req['from'])}",
                "to": f"{self._get_airport_name(req['to'])}",
                "dep_time": f"{req['date']}T20:15:00+05:30",
                "arr_time": f"{req['date']}T22:30:00+05:30",
                "duration_min": 135,
                "price_inr": int(base_price * 0.8),
                "availability": "available",
                "source": "static_demo",
                "airline": "Air India Express",
                "flight_number": "IX-789"
            })
            
            return flights
        elif self.mode == "api":
            return self.fetch_from_api(req)
        else:
            return []
    
    def _get_airport_name(self, city):
        """Get proper airport name for city"""
        airport_names = {
            "New Delhi": "Indira Gandhi International Airport (DEL)",
            "Mumbai": "Chhatrapati Shivaji International Airport (BOM)",
            "Bangalore": "Kempegowda International Airport (BLR)",
            "Chennai": "Chennai International Airport (MAA)",
            "Hyderabad": "Rajiv Gandhi International Airport (HYD)",
            "Kolkata": "Netaji Subhas Chandra Bose International Airport (CCU)",
            "Pune": "Pune Airport (PNQ)",
            "Chandigarh": "Chandigarh Airport (IXC)"
        }
        
        for city_name, airport in airport_names.items():
            if city_name.lower() in city.lower():
                return airport
        
        return f"{city} Airport"
    
    def _estimate_flight_price(self, from_city, to_city):
        """Estimate flight price based on route"""
        # Major route pricing (base prices in INR)
        route_prices = {
            ("New Delhi", "Mumbai"): 4500,
            ("New Delhi", "Bangalore"): 5200,
            ("New Delhi", "Chennai"): 5800,
            ("Mumbai", "Bangalore"): 4200,
            ("Mumbai", "Chennai"): 4800,
            ("Bangalore", "Chennai"): 3500
        }
        
        # Normalize city names
        from_norm = from_city.split(",")[0].strip()
        to_norm = to_city.split(",")[0].strip()
        
        # Check both directions
        for (city1, city2), price in route_prices.items():
            if ((city1.lower() in from_norm.lower() and city2.lower() in to_norm.lower()) or
                (city2.lower() in from_norm.lower() and city1.lower() in to_norm.lower())):
                return price
        
        # Default price for unknown routes
        return 4000

    def fetch_from_api(self, req):
        """Fetch flight data from Amadeus API"""
        try:
            if not self.amadeus_api_key or not self.amadeus_api_secret:
                print("Amadeus API credentials not found, using realistic demo data")
                # Return realistic demo data with clear disclaimers
                demo_req = req.copy()
                demo_req['mode'] = 'static'
                static_results = self.run(demo_req)
                # Add API disclaimer to each result
                for result in static_results:
                    result['source'] = 'demo_data_api_unavailable'
                    result['api_disclaimer'] = 'Real API unavailable - showing realistic demo data'
                return static_results
            
            # Get access token
            token = self._get_amadeus_token()
            if not token:
                return []
            
            # Extract airport codes
            from_airport = self._get_airport_code(req['from'])
            to_airport = self._get_airport_code(req['to'])
            
            if not from_airport or not to_airport:
                print(f"Could not find airport codes for {req['from']} or {req['to']}")
                return []
            
            # Search flights
            flights = self._search_flights(token, from_airport, to_airport, req['date'])
            
            # Convert to leg format
            legs = []
            for flight in flights:
                leg = self._convert_flight_to_leg(flight, req['date'])
                if leg:
                    legs.append(leg)
            
            return legs[:5]  # Return top 5 options
            
        except Exception as e:
            print(f"Error fetching flight data: {e}")
            return []

    def _get_amadeus_token(self):
        """Get Amadeus API access token"""
        try:
            url = f"{self.amadeus_base_url}/v1/security/oauth2/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.amadeus_api_key,
                'client_secret': self.amadeus_api_secret
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            print(f"Error getting Amadeus token: {e}")
            return None

    def _get_airport_code(self, city_name):
        """Convert city name to airport code"""
        airport_mapping = {
            "New Delhi": "DEL",
            "Mumbai": "BOM", 
            "Bangalore": "BLR",
            "Chennai": "MAA",
            "Hyderabad": "HYD",
            "Kolkata": "CCU",
            "Pune": "PNQ",
            "Chandigarh": "IXC",
            "Jaipur": "JAI",
            "Ahmedabad": "AMD"
        }
        
        for city, code in airport_mapping.items():
            if city.lower() in city_name.lower():
                return code
        
        return None

    def _search_flights(self, token, from_airport, to_airport, date):
        """Search flights using Amadeus API"""
        try:
            url = f"{self.amadeus_base_url}/v2/shopping/flight-offers"
            headers = {'Authorization': f'Bearer {token}'}
            params = {
                'originLocationCode': from_airport,
                'destinationLocationCode': to_airport,
                'departureDate': date,
                'adults': 1,
                'max': 5
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            print(f"Error searching flights: {e}")
            return []

    def _convert_flight_to_leg(self, flight_data, date):
        """Convert Amadeus flight data to leg format"""
        try:
            itinerary = flight_data.get('itineraries', [{}])[0]
            segments = itinerary.get('segments', [])
            
            if not segments:
                return None
            
            first_segment = segments[0]
            last_segment = segments[-1]
            
            # Parse times
            dep_time_str = first_segment.get('departure', {}).get('at', '')
            arr_time_str = last_segment.get('arrival', {}).get('at', '')
            
            if not dep_time_str or not arr_time_str:
                return None
            
            dep_time = datetime.fromisoformat(dep_time_str.replace('Z', '+00:00'))
            arr_time = datetime.fromisoformat(arr_time_str.replace('Z', '+00:00'))
            
            duration_min = int((arr_time - dep_time).total_seconds() / 60)
            
            # Get price
            price_data = flight_data.get('price', {})
            total_price = price_data.get('total', '0')
            
            return {
                "mode": "flight",
                "from": f"{first_segment.get('departure', {}).get('iataCode', 'Unknown')} Airport",
                "to": f"{last_segment.get('arrival', {}).get('iataCode', 'Unknown')} Airport",
                "dep_time": dep_time.isoformat(),
                "arr_time": arr_time.isoformat(),
                "duration_min": duration_min,
                "price_inr": int(float(total_price) * 83),  # Convert to INR
                "availability": "check_airline",
                "source": "amadeus_api",
                "airline": first_segment.get('carrierCode', 'Unknown'),
                "flight_number": first_segment.get('number', 'Unknown')
            }
            
        except Exception as e:
            print(f"Error converting flight data: {e}")
            return None

# ---- TrainAgent ----
class TrainAgent:
    def __init__(self, mode="static"):
        self.mode = mode
        
        # Initialize hybrid agent for real data
        if mode == "hybrid":
            from hybrid_agents import HybridTrainAgent
            self.hybrid_agent = HybridTrainAgent()

    def run(self, req):
        # Mode: static -> return demo static leg
        if self.mode == "hybrid":
            # Use hybrid agent for real data with fallbacks
            return self.hybrid_agent.search_trains(req['from'], req['to'], req['date'])
        elif self.mode == "static":
            return self._generate_static_trains(req)
        elif self.mode == "api":
            return self.fetch_from_api(req)
        else:
            return []
    
    def _generate_static_trains(self, req):
        """Generate multiple realistic train options"""
        trains = []
        base_price = self._estimate_train_price(req['from'], req['to'])
        base_duration = self._estimate_train_duration(req['from'], req['to'])
        
        from_station = self._get_station_name(req['from'])
        to_station = self._get_station_name(req['to'])
        
        # Express train - faster, more expensive
        trains.append({
            "mode": "train",
            "from": from_station,
            "to": to_station,
            "dep_time": f"{req['date']}T06:15:00+05:30",
            "arr_time": f"{req['date']}T{self._add_minutes_to_time('06:15', int(base_duration * 0.8))}+05:30",
            "duration_min": int(base_duration * 0.8),
            "price_inr": int(base_price * 1.4),
            "availability": "available",
            "source": "static_demo",
            "train_name": "Rajdhani Express",
            "train_number": "12001"
        })
        
        # Regular express - standard timing and price
        trains.append({
            "mode": "train",
            "from": from_station,
            "to": to_station,
            "dep_time": f"{req['date']}T14:30:00+05:30",
            "arr_time": f"{req['date']}T{self._add_minutes_to_time('14:30', base_duration)}+05:30",
            "duration_min": base_duration,
            "price_inr": base_price,
            "availability": "available",
            "source": "static_demo",
            "train_name": "Shatabdi Express",
            "train_number": "12002"
        })
        
        # Overnight train - slower, cheaper
        trains.append({
            "mode": "train",
            "from": from_station,
            "to": to_station,
            "dep_time": f"{req['date']}T22:45:00+05:30",
            "arr_time": f"{self._get_next_day_date(req['date'])}T{self._add_minutes_to_time('22:45', int(base_duration * 1.2))}+05:30",
            "duration_min": int(base_duration * 1.2),
            "price_inr": int(base_price * 0.7),
            "availability": "available",
            "source": "static_demo",
            "train_name": "Mail Express",
            "train_number": "12003"
        })
        
        return trains
    
    def _get_station_name(self, city):
        """Get proper railway station name"""
        station_names = {
            "New Delhi": "New Delhi Railway Station (NDLS)",
            "Mumbai": "Mumbai Central (MMCT)",
            "Bangalore": "Bangalore City Junction (SBC)",
            "Chennai": "Chennai Central (MAS)",
            "Hyderabad": "Hyderabad Deccan (HYB)",
            "Kolkata": "Howrah Junction (HWH)",
            "Pune": "Pune Junction (PUNE)",
            "Chandigarh": "Chandigarh Railway Station (CDG)"
        }
        
        for city_name, station in station_names.items():
            if city_name.lower() in city.lower():
                return station
        
        return f"{city} Railway Station"
    
    def _estimate_train_price(self, from_city, to_city):
        """Estimate train price based on route"""
        route_prices = {
            ("New Delhi", "Mumbai"): 1800,
            ("New Delhi", "Bangalore"): 2200,
            ("New Delhi", "Chennai"): 2400,
            ("New Delhi", "Chandigarh"): 350,
            ("Mumbai", "Bangalore"): 1600,
            ("Mumbai", "Chennai"): 1900,
            ("Mumbai", "Pune"): 250,
            ("Bangalore", "Chennai"): 800
        }
        
        from_norm = from_city.split(",")[0].strip()
        to_norm = to_city.split(",")[0].strip()
        
        for (city1, city2), price in route_prices.items():
            if ((city1.lower() in from_norm.lower() and city2.lower() in to_norm.lower()) or
                (city2.lower() in from_norm.lower() and city1.lower() in to_norm.lower())):
                return price
        
        return 1200
    
    def _estimate_train_duration(self, from_city, to_city):
        """Estimate train duration in minutes"""
        route_durations = {
            ("New Delhi", "Mumbai"): 960,  # 16 hours
            ("New Delhi", "Bangalore"): 1800,  # 30 hours
            ("New Delhi", "Chennai"): 1680,  # 28 hours
            ("New Delhi", "Chandigarh"): 240,  # 4 hours
            ("Mumbai", "Bangalore"): 1440,  # 24 hours
            ("Mumbai", "Chennai"): 1320,  # 22 hours
            ("Mumbai", "Pune"): 210,  # 3.5 hours
            ("Bangalore", "Chennai"): 300  # 5 hours
        }
        
        from_norm = from_city.split(",")[0].strip()
        to_norm = to_city.split(",")[0].strip()
        
        for (city1, city2), duration in route_durations.items():
            if ((city1.lower() in from_norm.lower() and city2.lower() in to_norm.lower()) or
                (city2.lower() in from_norm.lower() and city1.lower() in to_norm.lower())):
                return duration
        
        return 720  # 12 hours default
    
    def _add_minutes_to_time(self, time_str, minutes):
        """Add minutes to time string and return formatted time"""
        from datetime import datetime, timedelta
        time_obj = datetime.strptime(time_str, "%H:%M")
        new_time = time_obj + timedelta(minutes=minutes)
        return new_time.strftime("%H:%M")
    
    def _get_next_day_date(self, date_str):
        """Get next day's date"""
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_day = date_obj + timedelta(days=1)
        return next_day.strftime("%Y-%m-%d")
    
    def _get_station_code(self, city_name):
        """
        Convert city name to railway station code.
        This is a simplified mapping - in production, you'd use a proper station database.
        """
        station_mapping = {
            "Chandigarh": "CDG",
            "Secunderabad": "SC",
            "Mandi": "MNDI",
            "Anantapur": "ATP",
            "New Delhi": "NDLS",
            "Mumbai": "CSTM",
            "Chennai": "MAS",
            "Bangalore": "SBC",
            "Kolkata": "HWH",
            "Hyderabad": "HYB"
        }
        
        # Try exact match first
        for city, code in station_mapping.items():
            if city.lower() in city_name.lower():
                return code
        
        # Default fallback - you might want to implement geocoding here
        return None
    
    def _convert_train_to_leg(self, train_data, date):
        """
        Convert API train data to our leg format
        """
        try:
            train_base = train_data.get("train_base", {})
            
            # Get departure and arrival times from API response
            from_time_str = train_base.get("from_time", "00:00")
            to_time_str = train_base.get("to_time", "00:00")
            
            # Convert time format (API returns "17.15" format, convert to "17:15")
            from_time_str = from_time_str.replace(".", ":")
            to_time_str = to_time_str.replace(".", ":")
            
            # Parse times
            dep_time = datetime.strptime(f"{date} {from_time_str}", "%Y-%m-%d %H:%M")
            arr_time = datetime.strptime(f"{date} {to_time_str}", "%Y-%m-%d %H:%M")
            
            # Handle overnight trains
            if arr_time < dep_time:
                arr_time += timedelta(days=1)
            
            duration_min = int((arr_time - dep_time).total_seconds() / 60)
            
            # Estimate fare based on train type and distance
            train_name = train_base.get("train_name", "")
            estimated_fare = self._estimate_train_fare(train_name, duration_min)
            
            return {
                "mode": "train",
                "from": f"{train_base.get('from_stn_name', 'Unknown')} Railway Station",
                "to": f"{train_base.get('to_stn_name', 'Unknown')} Railway Station",
                "dep_time": dep_time.isoformat() + "+05:30",
                "arr_time": arr_time.isoformat() + "+05:30",
                "duration_min": duration_min,
                "price_inr": estimated_fare,
                "availability": "check_irctc",
                "source": "indian_rail_api",
                "train_number": train_base.get("train_no", ""),
                "train_name": train_name,
                "running_days": train_base.get("running_days", "1111111")
            }
        except Exception as e:
            print(f"Error converting train data: {e}")
            return None
    
    def _estimate_train_fare(self, train_name, duration_min):
        """
        Estimate train fare based on train type and duration
        """
        # Basic fare estimation based on train type
        if "SHATABDI" in train_name.upper() or "VANDE BHARAT" in train_name.upper():
            # Premium trains - higher fare
            base_fare = 500
            per_hour = 200
        elif "EXPRESS" in train_name.upper() or "EXP" in train_name.upper():
            # Express trains - medium fare
            base_fare = 300
            per_hour = 100
        else:
            # Regular trains - lower fare
            base_fare = 200
            per_hour = 80
        
        hours = duration_min / 60
        estimated_fare = base_fare + (hours * per_hour)
        return int(estimated_fare)
    
    def fetch_from_api(self, req):
        """Fetch train data from Indian Railway API"""
        try:
            # Extract station codes from city names
            from_station = self._get_station_code(req['from'])
            to_station = self._get_station_code(req['to'])
            
            if not from_station or not to_station:
                print(f"Could not find station codes for {req['from']} or {req['to']}, using realistic demo data")
                # Return realistic demo data with clear disclaimers
                demo_req = req.copy()
                static_results = self._generate_static_trains(demo_req)
                # Add API disclaimer to each result
                for result in static_results:
                    result['source'] = 'demo_data_api_unavailable'
                    result['api_disclaimer'] = 'Real API unavailable - showing realistic demo data'
                return static_results
            
            # Call the Indian Railway API
            api_url = "http://localhost:3000/trains/betweenStations"
            params = {
                "from": from_station,
                "to": to_station
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success", False):
                print(f"API call failed: {data}")
                return []
            
            # Convert API response to leg format
            legs = []
            for train_data in data.get("data", []):
                leg = self._convert_train_to_leg(train_data, req['date'])
                if leg:
                    legs.append(leg)
            
            return legs
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}, using realistic demo data")
            # Return realistic demo data with clear disclaimers
            demo_req = req.copy()
            static_results = self._generate_static_trains(demo_req)
            # Add API disclaimer to each result
            for result in static_results:
                result['source'] = 'demo_data_api_failed'
                result['api_disclaimer'] = 'Real API failed - showing realistic demo data'
            return static_results
        except Exception as e:
            print(f"Error processing train data: {e}, using realistic demo data")
            # Return realistic demo data with clear disclaimers
            demo_req = req.copy()
            static_results = self._generate_static_trains(demo_req)
            # Add API disclaimer to each result
            for result in static_results:
                result['source'] = 'demo_data_error_fallback'
                result['api_disclaimer'] = 'API error - showing realistic demo data'
            return static_results

# ---- BusAgent ----
class BusAgent:
    def __init__(self, mode="static"):
        self.mode = mode
        
        # Initialize hybrid agent for real data
        if mode == "hybrid":
            from hybrid_agents import HybridBusAgent
            self.hybrid_agent = HybridBusAgent()

    def run(self, req):
        if self.mode == "hybrid":
            # Use hybrid agent for real data with fallbacks
            return self.hybrid_agent.search_buses(req['from'], req['to'], req['date'])
        elif self.mode == "static":
            return self._generate_static_buses(req)
        elif self.mode == "api":
            return self.fetch_from_api(req)
        else:
            return []
    
    def _generate_static_buses(self, req):
        """Generate multiple realistic bus options"""
        buses = []
        base_price = self._estimate_bus_price(req['from'], req['to'])
        base_duration = self._estimate_bus_duration(req['from'], req['to'])
        
        from_terminal = self._get_bus_terminal_name(req['from'])
        to_terminal = self._get_bus_terminal_name(req['to'])
        
        # Early morning bus - cheaper, longer journey
        arrival_time_1 = self._calculate_arrival_time(req['date'], '05:30', int(base_duration * 1.1))
        buses.append({
            "mode": "bus",
            "from": from_terminal,
            "to": to_terminal,
            "dep_time": f"{req['date']}T05:30:00+05:30",
            "arr_time": arrival_time_1,
            "duration_min": int(base_duration * 1.1),
            "price_inr": int(base_price * 0.8),
            "availability": "available",
            "source": "static_demo",
            "operator": "State Transport",
            "bus_type": "Ordinary"
        })
        
        # Mid-morning AC bus - standard price and timing
        arrival_time = self._calculate_arrival_time(req['date'], '09:15', base_duration)
        buses.append({
            "mode": "bus",
            "from": from_terminal,
            "to": to_terminal,
            "dep_time": f"{req['date']}T09:15:00+05:30",
            "arr_time": arrival_time,
            "duration_min": base_duration,
            "price_inr": base_price,
            "availability": "available",
            "source": "static_demo",
            "operator": "Private Travels",
            "bus_type": "AC Sleeper"
        })
        
        # Evening Volvo - premium, faster
        arrival_time_3 = self._calculate_arrival_time(req['date'], '18:45', int(base_duration * 0.9))
        buses.append({
            "mode": "bus",
            "from": from_terminal,
            "to": to_terminal,
            "dep_time": f"{req['date']}T18:45:00+05:30",
            "arr_time": arrival_time_3,
            "duration_min": int(base_duration * 0.9),
            "price_inr": int(base_price * 1.4),
            "availability": "available",
            "source": "static_demo",
            "operator": "Volvo Travels",
            "bus_type": "Multi-Axle AC"
        })
        
        return buses
    
    def _get_bus_terminal_name(self, city):
        """Get proper bus terminal name"""
        terminal_names = {
            "New Delhi": "New Delhi ISBT Kashmere Gate",
            "Mumbai": "Mumbai Central Bus Terminal",
            "Bangalore": "Bangalore Majestic Bus Stand",
            "Chennai": "Chennai Koyambedu Bus Terminal",
            "Hyderabad": "Hyderabad Mahatma Gandhi Bus Station",
            "Kolkata": "Kolkata Esplanade Bus Terminal",
            "Pune": "Pune Swargate Bus Stand",
            "Chandigarh": "Chandigarh ISBT Sector 43"
        }
        
        for city_name, terminal in terminal_names.items():
            if city_name.lower() in city.lower():
                return terminal
        
        return f"{city} Bus Stand"
    
    def _estimate_bus_price(self, from_city, to_city):
        """Estimate bus price based on route"""
        route_prices = {
            ("New Delhi", "Mumbai"): 1200,
            ("New Delhi", "Bangalore"): 1800,
            ("New Delhi", "Chennai"): 2000,
            ("New Delhi", "Chandigarh"): 400,
            ("Mumbai", "Bangalore"): 1000,
            ("Mumbai", "Chennai"): 1400,
            ("Mumbai", "Pune"): 300,
            ("Bangalore", "Chennai"): 600
        }
        
        from_norm = from_city.split(",")[0].strip()
        to_norm = to_city.split(",")[0].strip()
        
        for (city1, city2), price in route_prices.items():
            if ((city1.lower() in from_norm.lower() and city2.lower() in to_norm.lower()) or
                (city2.lower() in from_norm.lower() and city1.lower() in to_norm.lower())):
                return price
        
        return 800
    
    def _estimate_bus_duration(self, from_city, to_city):
        """Estimate bus duration in minutes"""
        route_durations = {
            ("New Delhi", "Mumbai"): 1200,  # 20 hours
            ("New Delhi", "Bangalore"): 2160,  # 36 hours
            ("New Delhi", "Chennai"): 2040,  # 34 hours
            ("New Delhi", "Chandigarh"): 300,  # 5 hours
            ("Mumbai", "Bangalore"): 1080,  # 18 hours
            ("Mumbai", "Chennai"): 1320,  # 22 hours
            ("Mumbai", "Pune"): 180,  # 3 hours
            ("Bangalore", "Chennai"): 360  # 6 hours
        }
        
        from_norm = from_city.split(",")[0].strip()
        to_norm = to_city.split(",")[0].strip()
        
        for (city1, city2), duration in route_durations.items():
            if ((city1.lower() in from_norm.lower() and city2.lower() in to_norm.lower()) or
                (city2.lower() in from_norm.lower() and city1.lower() in to_norm.lower())):
                return duration
        
        return 480  # 8 hours default
    
    def _add_minutes_to_time(self, time_str, minutes):
        """Add minutes to time string and return formatted time"""
        from datetime import datetime, timedelta
        time_obj = datetime.strptime(time_str, "%H:%M")
        new_time = time_obj + timedelta(minutes=minutes)
        # Handle day overflow
        if new_time.day > time_obj.day:
            return f"+1day {new_time.strftime('%H:%M')}"
        return new_time.strftime("%H:%M")
    
    def _calculate_arrival_time(self, date, dep_time, duration_min):
        """Calculate proper arrival time with date handling"""
        from datetime import datetime, timedelta
        
        # Parse departure time
        dep_datetime = datetime.strptime(f"{date} {dep_time}", "%Y-%m-%d %H:%M")
        
        # Add duration
        arr_datetime = dep_datetime + timedelta(minutes=duration_min)
        
        # Format with timezone
        return arr_datetime.strftime("%Y-%m-%dT%H:%M:%S+05:30")
    
    def _estimate_bus_legs(self, req):
        """
        Estimate bus legs using simple distance mapping.
        """
        try:
            # Simple city-to-city distance mapping (same as ConnectorAgent)
            city_distances = {
                ("New Delhi", "Chandigarh"): 235,
                ("Delhi", "Chandigarh"): 235,
                ("Mumbai", "Pune"): 150,
                ("Mumbai", "Nashik"): 180,
                ("Bangalore", "Mysore"): 140,
                ("Chennai", "Coimbatore"): 500,
                ("Chennai", "Madurai"): 450,
                ("Hyderabad", "Vijayawada"): 280,
                ("Kolkata", "Durgapur"): 180,
            }
            
            # Extract city names
            from_city, from_state = self._parse_location(req['from'])
            to_city, to_state = self._parse_location(req['to'])
            
            # Try to find distance in mapping
            distance_km = None
            for (city1, city2), dist in city_distances.items():
                if ((from_city.lower() in city1.lower() or city1.lower() in from_city.lower()) and
                    (to_city.lower() in city2.lower() or city2.lower() in to_city.lower())):
                    distance_km = dist
                    break
            
            # If not found, use simple estimation
            if distance_km is None:
                if from_city.lower() == to_city.lower():
                    distance_km = 50  # Within city
                else:
                    distance_km = 200  # Between cities
            
            # Estimate travel time (assuming average speed of 50 km/h for buses)
            duration_min = int((distance_km / 50) * 60)
            
            # Estimate cost (roughly ₹2-3 per km)
            estimated_cost = int(distance_km * 2.5)
            
            # Generate multiple bus options
            legs = []
            bus_times = ["06:00", "10:00", "14:00", "18:00", "22:00"]
            
            for i, time in enumerate(bus_times[:3]):  # Return top 3 options
                dep_time = datetime.strptime(f"{req['date']} {time}", "%Y-%m-%d %H:%M")
                arr_time = dep_time + timedelta(minutes=duration_min)
                
                legs.append({
                    "mode": "bus",
                    "from": f"{req['from']} Bus Stand",
                    "to": f"{req['to']} Bus Stand",
                    "dep_time": dep_time.isoformat() + "+05:30",
                    "arr_time": arr_time.isoformat() + "+05:30",
                    "duration_min": duration_min,
                    "price_inr": estimated_cost + (i * 100),  # Vary price slightly
                    "availability": "check_redbus",
                    "source": "haversine_estimate",
                    "distance_km": round(distance_km, 1),
                    "operator": f"Bus Operator {i+1}"
                })
            
            return legs
            
        except Exception as e:
            print(f"Error estimating bus legs: {e}")
            return []
    
    def _parse_location(self, location_str):
        """
        Parse location string to extract city and state
        Example: "New Delhi, Delhi, India" -> ("New Delhi", "Delhi")
        """
        try:
            parts = [part.strip() for part in location_str.split(',')]
            
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1]
                return city, state
            elif len(parts) == 1:
                # If only one part, assume it's the city
                return parts[0], ""
            else:
                return location_str, ""
        except Exception as e:
            print(f"Error parsing location '{location_str}': {e}")
            return location_str, ""
    
    def fetch_from_api(self, req):
        """Fetch bus data from CSV datasets or estimation"""
        try:
            # Try CSV dataset first
            try:
                from bus_data_loader import BusDataLoader
                
                # Initialize bus data loader
                if not hasattr(self, 'data_loader'):
                    self.data_loader = BusDataLoader()
                
                # Extract city and state information
                from_location = req['from']
                to_location = req['to']
                date = req['date']
                
                # Parse location strings to extract city and state
                from_city, from_state = self._parse_location(from_location)
                to_city, to_state = self._parse_location(to_location)
                
                # Search for matching routes
                matching_routes = self.data_loader.find_routes(from_city, to_city, from_state, to_state)
                
                if matching_routes:
                    # Generate bus options from dataset
                    legs = []
                    for route in matching_routes:
                        route_options = self.data_loader.get_route_options(route, date)
                        legs.extend(route_options)
                    
                    # Sort by departure time and limit to top 5 options
                    legs.sort(key=lambda x: x['dep_time'])
                    return legs[:5]
                
            except ImportError:
                pass  # CSV loader not available
            
            # Fallback to realistic static data
            return self._generate_static_buses(req)
            
        except Exception as e:
            print(f"Error fetching bus data: {e}, using realistic demo data")
            # Return realistic demo data with clear disclaimers
            static_results = self._generate_static_buses(req)
            # Add API disclaimer to each result
            for result in static_results:
                result['source'] = 'demo_data_api_failed'
                result['api_disclaimer'] = 'Real API failed - showing realistic demo data'
            return static_results

# ---- ConnectorAgent ----
class ConnectorAgent:
    def __init__(self, mode="static"):
        self.mode = mode

    def run(self, legs):
        """
        Create connector legs between different transport modes using real geocoding.
        """
        connectors = []
        
        if self.mode == "static":
            # Original static logic for demo
            for leg in legs:
                if leg["mode"] == "bus" and "Chandigarh" in leg["to"]:
                    dep_time = iso_to_dt(leg["arr_time"])
                    arr_time = dep_time + timedelta(minutes=15)
                    connectors.append({
                        "mode": "taxi",
                        "from": leg["to"],
                        "to": "Chandigarh Railway Station",
                        "dep_time": dt_to_iso(dep_time),
                        "arr_time": dt_to_iso(arr_time),
                        "duration_min": 15,
                        "price_inr": 150,
                        "source": "static_demo"
                    })
        elif self.mode == "api":
            # Real geocoding-based connectors
            connectors = self._generate_real_connectors(legs)
        
        return connectors
    
    def _generate_real_connectors(self, legs):
        """
        Generate real connector legs using simple distance calculations.
        """
        connectors = []
        
        try:
            # Look for bus-to-train connections
            bus_legs = [leg for leg in legs if leg.get("mode") == "bus"]
            train_legs = [leg for leg in legs if leg.get("mode") == "train"]
            
            # Create connectors between bus arrivals and train departures in same city
            for bus_leg in bus_legs:
                bus_city = self._extract_city_name(bus_leg["to"])
                
                for train_leg in train_legs:
                    train_city = self._extract_city_name(train_leg["from"])
                    
                    # If bus arrives in same city where train departs
                    if bus_city.lower() in train_city.lower() or train_city.lower() in bus_city.lower():
                        # Create connector from bus stand to railway station
                        bus_stand = bus_leg["to"]
                        railway_station = train_leg["from"]
                        
                        if bus_stand != railway_station:
                            connector = self._create_connector_leg(bus_stand, railway_station, bus_leg["arr_time"])
                            if connector:
                                connectors.append(connector)
                                break  # Only create one connector per bus leg
            
            return connectors
            
        except Exception as e:
            print(f"Error generating real connectors: {e}")
            return []
    
    def _extract_city_name(self, location):
        """
        Extract city name from location string.
        """
        # Remove common suffixes and extract city name
        location = location.replace(" Bus Stand", "").replace(" Railway Station", "").replace(" Station", "")
        
        # Split by comma and take first part
        parts = location.split(",")
        city = parts[0].strip()
        
        return city
    
    def _create_connector_leg(self, from_location, to_location, start_time):
        """
        Create a connector leg between two locations using simple Haversine distance.
        """
        try:
            # Simple city-to-city distance mapping (in km)
            city_distances = {
                # Delhi area
                ("New Delhi", "Chandigarh"): 235,
                ("Delhi", "Chandigarh"): 235,
                ("New Delhi", "Gurgaon"): 30,
                ("New Delhi", "Noida"): 25,
                ("New Delhi", "Faridabad"): 35,
                
                # Mumbai area
                ("Mumbai", "Pune"): 150,
                ("Mumbai", "Nashik"): 180,
                ("Mumbai", "Thane"): 30,
                
                # Bangalore area
                ("Bangalore", "Mysore"): 140,
                ("Bangalore", "Mangalore"): 350,
                ("Bangalore", "Hubli"): 410,
                
                # Chennai area
                ("Chennai", "Coimbatore"): 500,
                ("Chennai", "Madurai"): 450,
                ("Chennai", "Trichy"): 320,
                
                # Hyderabad area
                ("Hyderabad", "Vijayawada"): 280,
                ("Hyderabad", "Warangal"): 150,
                
                # Kolkata area
                ("Kolkata", "Durgapur"): 180,
                ("Kolkata", "Bhubaneswar"): 450,
            }
            
            # Extract city names from locations
            from_city = self._extract_city_name(from_location)
            to_city = self._extract_city_name(to_location)
            
            # Try to find distance in mapping
            distance_km = None
            for (city1, city2), dist in city_distances.items():
                if ((from_city.lower() in city1.lower() or city1.lower() in from_city.lower()) and
                    (to_city.lower() in city2.lower() or city2.lower() in to_city.lower())):
                    distance_km = dist
                    break
            
            # If not found, use simple estimation based on city names
            if distance_km is None:
                # Rough estimation: assume 50km for same city, 200km for different cities
                if from_city.lower() == to_city.lower():
                    distance_km = 15  # Within city
                else:
                    distance_km = 25  # Between nearby cities
            
            # Calculate travel time: assume 30 km/h taxi speed
            duration_min = int((distance_km / 30) * 60)
            
            # Estimate cost: ₹10 per km for taxi
            estimated_cost = int(distance_km * 10)
            
            # Calculate arrival time
            dep_time = iso_to_dt(start_time)
            arr_time = dep_time + timedelta(minutes=duration_min)
            
            return {
                "mode": "taxi",
                "from": from_location,
                "to": to_location,
                "dep_time": dt_to_iso(dep_time),
                "arr_time": dt_to_iso(arr_time),
                "duration_min": duration_min,
                "price_inr": estimated_cost,
                "source": "haversine_estimate",
                "distance_km": round(distance_km, 1),
                "transfer_type": "bus_to_train"
            }
            
        except Exception as e:
            print(f"Error creating connector leg: {e}")
            return None

# ---- PlannerAgent ----
class PlannerAgent:
    def run(self, bus_legs, connectors, train_legs, flight_legs=None):
        """Generate multiple optimized itineraries from available transport options"""
        itineraries = []
        
        # Strategy 1: Flight-only (if flights available)
        if flight_legs:
            for flight in flight_legs[:2]:  # Top 2 flights
                itinerary = self._create_itinerary(
                    f"flight-{len(itineraries)+1}",
                    [flight],
                    "flight_direct",
                    "Direct flight - fastest option"
                )
                itineraries.append(itinerary)
        
        # Strategy 2: Train-only (if trains available)
        if train_legs:
            for train in train_legs[:2]:  # Top 2 trains
                itinerary = self._create_itinerary(
                    f"train-{len(itineraries)+1}",
                    [train],
                    "train_direct", 
                    "Direct train - comfortable journey"
                )
                itineraries.append(itinerary)
        
        # Strategy 3: Bus-only (if buses available)
        if bus_legs:
            for bus in bus_legs[:2]:  # Top 2 buses
                itinerary = self._create_itinerary(
                    f"bus-{len(itineraries)+1}",
                    [bus],
                    "bus_direct",
                    "Direct bus - economical option"
                )
                itineraries.append(itinerary)
        
        # Strategy 4: Multi-modal combinations (if connectors exist)
        if connectors and len(connectors) > 0:
            # Find best bus + connector + train combination
            for bus in bus_legs[:1]:  # Best bus
                for connector in connectors[:1]:  # Best connector
                    for train in train_legs[:1]:  # Best train
                        if self._can_connect(bus, connector, train):
                            combined_legs = [bus, connector, train]
                            itinerary = self._create_itinerary(
                                f"multi-{len(itineraries)+1}",
                                combined_legs,
                                "multimodal",
                                "Combined transport - balanced cost and time"
                            )
                            itineraries.append(itinerary)
                            break
                    break
                break
        
        # If no itineraries created, create a fallback
        if not itineraries:
            all_legs = (flight_legs or []) + (train_legs or []) + (bus_legs or [])
            if all_legs:
                best_leg = min(all_legs, key=lambda x: x.get("price_inr", float('inf')))
                itinerary = self._create_itinerary(
                    "fallback-1",
                    [best_leg],
                    "fallback",
                    "Best available option"
                )
                itineraries.append(itinerary)
        
        # Return top 3 itineraries
        return itineraries[:3]
    
    def _create_itinerary(self, itin_id, legs, strategy, description):
        """Create a single itinerary from legs"""
        total_time = sum([l.get("duration_min", 0) for l in legs])
        total_cost = sum([l.get("price_inr", 0) for l in legs])
        
        # Generate transfer instructions
        transfer_instructions = []
        for i in range(len(legs) - 1):
            current_leg = legs[i]
            next_leg = legs[i + 1]
            if current_leg.get("mode") != next_leg.get("mode"):
                instruction = f"Transfer from {current_leg['to']} to {next_leg['from']}"
                transfer_instructions.append(instruction)
        
        return {
            "id": itin_id,
            "legs": legs,
            "total_estimated_time_min": total_time,
            "total_estimated_cost_inr": total_cost,
            "transfer_instructions": transfer_instructions,
            "notes": [description, "Prices are estimates; check availability before booking"],
            "optimization_strategy": strategy
        }
    
    def _can_connect(self, bus_leg, connector_leg, train_leg):
        """Check if legs can be connected logically"""
        try:
            # Check if connector connects bus arrival to train departure
            bus_arrival_city = self._extract_city_from_location(bus_leg["to"])
            connector_from_city = self._extract_city_from_location(connector_leg["from"])
            connector_to_city = self._extract_city_from_location(connector_leg["to"])
            train_departure_city = self._extract_city_from_location(train_leg["from"])
            
            # Bus should arrive in same city as connector starts
            # Connector should end in same city as train departs
            return (bus_arrival_city.lower() in connector_from_city.lower() and
                    connector_to_city.lower() in train_departure_city.lower())
        except:
            return False
    
    def _extract_city_from_location(self, location):
        """Extract city name from location string"""
        # Remove common suffixes
        location = location.replace(" Bus Stand", "").replace(" Railway Station", "")
        location = location.replace(" Airport", "").replace(" Terminal", "")
        
        # Take first part before comma
        return location.split(",")[0].strip()

# ---- RankingAgent ----
class RankingAgent:
    def run(self, itinerary, preferences):
        # Simple scoring: lower cost -> higher cost score; lower time -> higher time score.
        # Normalization using simple heuristics (not perfect).
        cost = itinerary.get("total_estimated_cost_inr", 0)
        time = itinerary.get("total_estimated_time_min", 1)
        # heuristics:
        cost_score = max(0.0, min(1.0, 1.0 - (cost / 10000.0)))  # if cost 0 -> 1.0, if cost 10000 -> 0.0
        time_score = max(0.0, min(1.0, 1.0 - (time / 2000.0)))   # if time 0 -> 1.0, if time 2000 -> 0.0
        # comfort heuristic:
        comfort = 0.6
        overall = 0.5 * cost_score + 0.3 * time_score + 0.2 * comfort
        itinerary["score"] = {
            "cost": round(cost_score, 2),
            "time": round(time_score, 2),
            "comfort": round(comfort, 2),
            "overall": round(overall, 2)
        }
        return itinerary
