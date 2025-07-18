import googlemaps
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import config

class PlacesScraper:
    def __init__(self, api_key: str = None):
        """Initialize the Places API scraper."""
        self.api_key = api_key or config.GOOGLE_API_KEY
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.geocoder = Nominatim(user_agent="lead_scraper_v1.0")
        self.request_count = 0
        self.start_time = time.time()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format=config.LOG_FORMAT
        )
        self.logger = logging.getLogger(__name__)
        
    def _rate_limit(self):
        """Implement rate limiting to avoid API quota exhaustion."""
        self.request_count += 1
        
        # Check if we're approaching rate limits
        elapsed_time = time.time() - self.start_time
        if elapsed_time < 60:  # Within 1 minute
            if self.request_count >= config.MAX_REQUESTS_PER_MINUTE:
                sleep_time = 60 - elapsed_time
                self.logger.info(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.start_time = time.time()
        else:
            # Reset counter after 1 minute
            self.request_count = 1
            self.start_time = time.time()
        
        # Random delay between requests
        delay = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
        time.sleep(delay)
    
    def geocode_postal_code(self, postal_code: str) -> Optional[Tuple[float, float]]:
        """Convert postal code to latitude/longitude coordinates."""
        try:
            self.logger.info(f"Geocoding postal code: {postal_code}")
            location = self.geocoder.geocode(postal_code)
            if location:
                return (location.latitude, location.longitude)
            else:
                self.logger.warning(f"Could not geocode postal code: {postal_code}")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Geocoding error for {postal_code}: {e}")
            return None
    
    def search_places(self, query: str, location: Tuple[float, float], 
                     radius: int = None, is_large_city: bool = False) -> List[Dict]:
        """Search for places using Google Places API (New)."""
        radius = radius or config.DEFAULT_RADIUS
        
        # For large cities/areas, use a larger radius and potentially multiple searches
        if is_large_city or any(city in query.lower() for city in ['toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'edmonton', 'winnipeg', 'new york', 'los angeles', 'chicago', 'london', 'manchester', 'birmingham']):
            radius = max(radius, 25000)  # 25km for large cities
            self.logger.info(f"Large city detected, using expanded radius: {radius}m")
        
        try:
            all_places = []
            search_locations = [location]
            
            # For very large cities, add additional search points with better spacing
            if is_large_city and radius >= 25000:
                # Add search points with larger spacing for better coverage
                lat, lng = location
                # Use larger offsets to avoid overlap (roughly 15-20km spacing)
                offset_large = 0.15  # ~15km
                offset_medium = 0.08  # ~8km
                
                additional_locations = [
                    # Cardinal directions - far out
                    (lat + offset_large, lng),        # North
                    (lat - offset_large, lng),        # South  
                    (lat, lng + offset_large),        # East
                    (lat, lng - offset_large),        # West
                    
                    # Diagonal directions - medium distance
                    (lat + offset_medium, lng + offset_medium),   # NE
                    (lat - offset_medium, lng - offset_medium),   # SW
                    (lat + offset_medium, lng - offset_medium),   # NW
                    (lat - offset_medium, lng + offset_medium),   # SE
                    
                    # Additional ring for maximum coverage
                    (lat + offset_large*1.5, lng),               # Far North
                    (lat - offset_large*1.5, lng),               # Far South
                    (lat, lng + offset_large*1.5),               # Far East
                    (lat, lng - offset_large*1.5),               # Far West
                ]
                search_locations.extend(additional_locations)
                self.logger.info(f"Using {len(search_locations)} search points with improved spacing for maximum coverage")
            
            seen_place_ids = set()
            
            for i, search_loc in enumerate(search_locations):
                if i > 0:  # Add delay between multiple searches
                    import time
                    time.sleep(1)
                
                self._rate_limit()
                
                if i == 0:
                    self.logger.info(f"Searching: '{query}' near {search_loc}")
                else:
                    self.logger.info(f"Additional search {i+1}/{len(search_locations)} near {search_loc}")
                
                # Use the new Places API Text Search endpoint
                url = "https://places.googleapis.com/v1/places:searchText"
                
                headers = {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': self.api_key,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.businessStatus,places.priceLevel,places.types,places.nationalPhoneNumber,places.internationalPhoneNumber,places.websiteUri,places.regularOpeningHours'
                }
                
                data = {
                    "textQuery": query,
                    "locationBias": {
                        "circle": {
                            "center": {
                                "latitude": search_loc[0],
                                "longitude": search_loc[1]
                            },
                            "radius": radius  # Use full radius for each search point for maximum coverage
                        }
                    },
                    "maxResultCount": config.MAX_RESULTS_PER_LOCATION,
                    "languageCode": "en"
                }
                
                import requests
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    places = result.get('places', [])
                    
                    # Deduplicate by place_id
                    new_places = []
                    for place in places:
                        place_id = place.get('id')
                        if place_id and place_id not in seen_place_ids:
                            seen_place_ids.add(place_id)
                            converted_place = self._convert_new_api_format(place)
                            new_places.append(converted_place)
                    
                    all_places.extend(new_places)
                    self.logger.info(f"Search {i+1}: Found {len(new_places)} new places (total: {len(all_places)})")
                    
                    # Stop if we have enough results
                    max_results = getattr(config, 'MAX_RESULTS_LARGE_CITY', config.MAX_RESULTS_PER_LOCATION * 3)
                    if len(all_places) >= max_results:
                        break
                        
                else:
                    self.logger.error(f"API request failed: {response.status_code} - {response.text}")
            
            self.logger.info(f"Total unique places found: {len(all_places)}")
            return all_places
            
        except Exception as e:
            self.logger.error(f"Error searching places: {e}")
            return []
    
    def _convert_new_api_format(self, place: Dict) -> Dict:
        """Convert new Places API format to legacy format for compatibility."""
        try:
            location = place.get('location', {})
            opening_hours = place.get('regularOpeningHours', {})
            
            return {
                'place_id': place.get('id', ''),
                'name': place.get('displayName', {}).get('text', ''),
                'formatted_address': place.get('formattedAddress', ''),
                'vicinity': place.get('formattedAddress', ''),
                'geometry': {
                    'location': {
                        'lat': location.get('latitude'),
                        'lng': location.get('longitude')
                    }
                },
                'rating': place.get('rating'),
                'user_ratings_total': place.get('userRatingCount'),
                'business_status': place.get('businessStatus', '').upper(),
                'price_level': place.get('priceLevel'),
                'types': place.get('types', []),
                'formatted_phone_number': place.get('nationalPhoneNumber', ''),
                'international_phone_number': place.get('internationalPhoneNumber', ''),
                'website': place.get('websiteUri', ''),
                'opening_hours': {
                    'weekday_text': opening_hours.get('weekdayDescriptions', [])
                } if opening_hours else {}
            }
        except Exception as e:
            self.logger.error(f"Error converting place format: {e}")
            return {}
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information for a specific place using new Places API."""
        try:
            self._rate_limit()
            
            # Use the new Places API Get Place endpoint
            url = f"https://places.googleapis.com/v1/places/{place_id}"
            
            headers = {
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'id,displayName,formattedAddress,location,rating,userRatingCount,businessStatus,priceLevel,types,nationalPhoneNumber,internationalPhoneNumber,websiteUri,regularOpeningHours,photos'
            }
            
            import requests
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                place_data = response.json()
                # Convert to legacy format for compatibility
                return self._convert_new_api_format(place_data)
            else:
                self.logger.error(f"Place details API request failed: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting place details for {place_id}: {e}")
            return None
    
    def extract_business_data(self, place: Dict, detailed: bool = True) -> Dict:
        """Extract and normalize business data from place information."""
        # Get detailed info if requested
        if detailed and 'place_id' in place:
            place_details = self.get_place_details(place['place_id'])
            if place_details:
                place.update(place_details)
        
        # Extract coordinates
        geometry = place.get('geometry', {}).get('location', {})
        lat = geometry.get('lat')
        lng = geometry.get('lng')
        
        # Extract opening hours
        opening_hours = place.get('opening_hours', {})
        hours_text = None
        if opening_hours:
            hours_text = '; '.join(opening_hours.get('weekday_text', []))
        
        # Extract business types
        types = place.get('types', [])
        primary_type = types[0] if types else 'establishment'
        
        # Extract email if available (often in website or additional data)
        email = None
        if place.get('website'):
            # Try to extract email from website domain
            import re
            website = place.get('website', '')
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', website)
            if domain_match:
                domain = domain_match.group(1)
                # Common email patterns
                possible_emails = [
                    f"info@{domain}",
                    f"contact@{domain}",
                    f"hello@{domain}",
                    f"office@{domain}"
                ]
                # For now, use the most common one
                email = f"info@{domain}"

        return {
            'place_id': place.get('place_id'),
            'name': place.get('name'),
            'address': place.get('formatted_address') or place.get('vicinity'),
            'phone': place.get('formatted_phone_number') or place.get('international_phone_number'),
            'email': email,
            'website': place.get('website'),
            'rating': place.get('rating'),
            'review_count': place.get('user_ratings_total'),
            'business_status': place.get('business_status'),
            'price_level': place.get('price_level'),
            'primary_type': primary_type,
            'all_types': ', '.join(types),
            'latitude': lat,
            'longitude': lng,
            'opening_hours': hours_text,
            'search_query': getattr(self, 'current_query', ''),
            'search_location': getattr(self, 'current_location', ''),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def scrape_postal_codes(self, query_template: str, postal_codes: List[str], 
                          detailed: bool = True) -> List[Dict]:
        """Scrape multiple postal codes with a query template."""
        all_results = []
        
        for i, postal_code in enumerate(postal_codes, 1):
            self.logger.info(f"Processing postal code {i}/{len(postal_codes)}: {postal_code}")
            
            # Geocode postal code
            coordinates = self.geocode_postal_code(postal_code)
            if not coordinates:
                continue
            
            # Format query
            query = query_template.format(postal_code)
            self.current_query = query
            self.current_location = postal_code
            
            # Search places
            places = self.search_places(query, coordinates)
            
            # Extract business data
            for place in places:
                try:
                    business_data = self.extract_business_data(place, detailed)
                    all_results.append(business_data)
                except Exception as e:
                    self.logger.error(f"Error extracting data for place: {e}")
                    continue
            
            self.logger.info(f"Extracted {len(places)} businesses from {postal_code}")
        
        self.logger.info(f"Total businesses extracted: {len(all_results)}")
        return all_results 