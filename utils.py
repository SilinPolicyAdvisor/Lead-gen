import re
import random
import string
from typing import List, Iterator, Optional
import config

class PostalCodeGenerator:
    """Generate postal codes for different regions."""
    
    @staticmethod
    def canadian_postal_codes(start_code: str, count: int = 100) -> List[str]:
        """Generate Canadian postal codes starting from a given code."""
        codes = []
        
        # Parse the starting postal code
        match = re.match(r'([A-Za-z])(\d)([A-Za-z])\s?(\d)([A-Za-z])(\d)', start_code.upper())
        if not match:
            raise ValueError(f"Invalid Canadian postal code format: {start_code}")
        
        area_code, district_num, district_letter, _, _, _ = match.groups()
        
        # Generate variations
        for i in range(count):
            # Increment district number with wraparound
            new_district_num = (int(district_num) + (i // 26)) % 10
            
            # Cycle through district letters
            letter_offset = i % 26
            new_district_letter = chr((ord(district_letter) - ord('A') + letter_offset) % 26 + ord('A'))
            
            # Random unit portion (last 3 characters)
            unit_num = random.randint(1, 9)
            unit_letter = random.choice(string.ascii_uppercase)
            unit_final = random.randint(0, 9)
            
            postal_code = f"{area_code}{new_district_num}{new_district_letter} {unit_num}{unit_letter}{unit_final}"
            codes.append(postal_code)
        
        return codes
    
    @staticmethod
    def us_zip_codes(start_zip: str, count: int = 100) -> List[str]:
        """Generate US ZIP codes starting from a given ZIP."""
        try:
            start_num = int(start_zip[:5])
            codes = []
            
            for i in range(count):
                new_zip = start_num + i
                if new_zip > 99999:
                    new_zip = new_zip % 100000
                codes.append(f"{new_zip:05d}")
            
            return codes
        except ValueError:
            raise ValueError(f"Invalid US ZIP code format: {start_zip}")
    
    @staticmethod
    def uk_postal_codes(start_code: str, count: int = 100) -> List[str]:
        """Generate UK postal codes starting from a given code."""
        # Simplified UK postal code generation
        codes = []
        base_code = start_code.replace(' ', '').upper()
        
        # Extract area code (first 1-2 letters)
        area_match = re.match(r'([A-Z]{1,2})', base_code)
        if not area_match:
            raise ValueError(f"Invalid UK postal code format: {start_code}")
        
        area = area_match.group(1)
        
        for i in range(count):
            district = random.randint(1, 99)
            sector = random.randint(0, 9)
            unit = ''.join(random.choices(string.ascii_uppercase, k=2))
            
            postal_code = f"{area}{district} {sector}{unit}"
            codes.append(postal_code)
        
        return codes

def detect_postal_code_type(postal_code: str) -> Optional[str]:
    """Detect the type of postal code (Canada, US, UK)."""
    postal_code = postal_code.strip()
    
    for region, pattern in config.POSTAL_CODE_PATTERNS.items():
        if re.match(pattern, postal_code):
            return region
    
    return None

def generate_postal_codes(start_code: str, count: int = 100) -> List[str]:
    """Generate postal codes based on the detected type."""
    region = detect_postal_code_type(start_code)
    
    if region == 'canada':
        return PostalCodeGenerator.canadian_postal_codes(start_code, count)
    elif region == 'usa':
        return PostalCodeGenerator.us_zip_codes(start_code, count)
    elif region == 'uk':
        return PostalCodeGenerator.uk_postal_codes(start_code, count)
    else:
        raise ValueError(f"Unsupported postal code format: {start_code}")

def validate_query_template(template: str) -> bool:
    """Validate that the query template contains the {} placeholder."""
    return '{}' in template

def clean_phone_number(phone: str) -> str:
    """Clean and standardize phone number format."""
    if not phone:
        return ""
    
    # Remove all non-digit characters except + at the beginning
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Handle international format
    if cleaned.startswith('+'):
        return cleaned
    
    # Handle North American format
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    elif len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    
    return cleaned

def extract_domain_from_website(website: str) -> str:
    """Extract domain name from website URL."""
    if not website:
        return ""
    
    # Remove protocol
    domain = re.sub(r'^https?://', '', website)
    # Remove www
    domain = re.sub(r'^www\.', '', domain)
    # Remove path
    domain = domain.split('/')[0]
    # Remove port
    domain = domain.split(':')[0]
    
    return domain.lower()

def batch_list(items: List, batch_size: int) -> Iterator[List]:
    """Split a list into batches of specified size."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

class ProgressTracker:
    """Track and display progress of scraping operations."""
    
    def __init__(self, total_items: int):
        self.total_items = total_items
        self.completed_items = 0
        self.start_time = None
        self.current_item = ""
    
    def start(self):
        """Start the progress tracker."""
        import time
        self.start_time = time.time()
        print(f"Starting processing of {self.total_items} items...")
    
    def update(self, item_name: str = "", increment: int = 1):
        """Update progress."""
        import time
        self.completed_items += increment
        self.current_item = item_name
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            if self.completed_items > 0:
                rate = self.completed_items / elapsed
                eta = (self.total_items - self.completed_items) / rate if rate > 0 else 0
                
                print(f"Progress: {self.completed_items}/{self.total_items} "
                      f"({self.completed_items/self.total_items*100:.1f}%) "
                      f"| Current: {item_name} "
                      f"| Rate: {rate:.1f} items/sec "
                      f"| ETA: {eta/60:.1f} min")
    
    def finish(self):
        """Complete the progress tracking."""
        import time
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"Completed {self.completed_items} items in {total_time/60:.1f} minutes")

def geocode_area_name(area_name: str, api_key: str = None) -> Optional[tuple]:
    """Geocode an area name to coordinates using multiple services."""
    import requests
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Try Google Geocoding API first (more reliable for area names)
    if api_key:
        try:
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': area_name,
                'key': api_key
            }
            response = requests.get(geocode_url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                location = data['results'][0]['geometry']['location']
                logger.info(f"Successfully geocoded {area_name} using Google API")
                return (location['lat'], location['lng'])
            else:
                logger.warning(f"Google Geocoding failed for {area_name}: {data.get('status', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Google Geocoding exception for {area_name}: {e}")
    
    # Fallback to Nominatim (OpenStreetMap) - free but requires proper headers
    try:
        geocode_url = "https://nominatim.openstreetmap.org/search"
        headers = {
            'User-Agent': 'Lead-Scraper/1.0 (Business Lead Generation Tool)'
        }
        params = {
            'q': area_name,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'ca,us,gb'  # Limit to common countries
        }
        
        # Add delay to respect rate limits
        time.sleep(1)
        
        response = requests.get(geocode_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                logger.info(f"Successfully geocoded {area_name} using Nominatim")
                return (float(data[0]['lat']), float(data[0]['lon']))
            else:
                logger.warning(f"Nominatim returned no results for {area_name}")
        else:
            logger.error(f"Nominatim HTTP error {response.status_code} for {area_name}")
    
    except Exception as e:
        logger.error(f"Nominatim geocoding exception for {area_name}: {e}")
    
    logger.error(f"Failed to geocode {area_name} with all methods")
    return None

def format_business_summary(business: dict) -> str:
    """Format a business record into a readable summary."""
    name = business.get('name', 'Unknown')
    address = business.get('address', 'No address')
    phone = business.get('phone', 'No phone')
    rating = business.get('rating', 'No rating')
    
    summary = f"• {name}\n"
    summary += f"  Address: {address}\n"
    summary += f"  Phone: {phone}\n"
    summary += f"  Rating: {rating}"
    
    if business.get('website'):
        summary += f"\n  Website: {business['website']}"
    
    return summary 