import os
from typing import List, Dict

# Google Places API Configuration
GOOGLE_API_KEY = "AIzaSyC40IF3ruBEru0canZ16_YxnUROjijWwdM"

# Rate limiting settings
REQUEST_DELAY_MIN = 0.5  # Minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 1.5  # Maximum delay between requests (seconds)
MAX_REQUESTS_PER_MINUTE = 100  # Conservative limit

# Search configuration
DEFAULT_RADIUS = 5000  # 5km radius for searches
MAX_RESULTS_PER_LOCATION = 60  # Google Places limit is 60 results per search
MAX_RESULTS_LARGE_CITY = 180  # Allow up to 3x for large cities with multiple search points

# File output settings
OUTPUT_DIR = "output"
CSV_FILENAME = "leads.csv"
XLSX_FILENAME = "leads.xlsx"

# Data fields to extract
PLACE_FIELDS = [
    'place_id',
    'name',
    'formatted_address',
    'formatted_phone_number',
    'international_phone_number',
    'website',
    'rating',
    'user_ratings_total',
    'business_status',
    'opening_hours',
    'price_level',
    'types',
    'geometry'
]

# Search types mapping
BUSINESS_TYPES = {
    'dental': ['dentist', 'dental_clinic'],
    'restaurant': ['restaurant', 'food'],
    'pharmacy': ['pharmacy'],
    'gym': ['gym'],
    'hotel': ['lodging'],
    'gas_station': ['gas_station'],
    'hospital': ['hospital'],
    'bank': ['bank'],
    'lawyer': ['lawyer'],
    'real_estate': ['real_estate_agency']
}

# Postal code ranges for different regions
POSTAL_CODE_PATTERNS = {
    'canada': r'^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$',
    'usa': r'^\d{5}(-\d{4})?$',
    'uk': r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$'
}

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO' 