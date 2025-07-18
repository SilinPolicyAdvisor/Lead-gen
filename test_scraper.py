#!/usr/bin/env python3
"""
Quick test script for the Google Places Lead Scraper
Tests basic functionality with a small sample
"""

import sys
from places_scraper import PlacesScraper
from data_handler import DataHandler
from utils import generate_postal_codes

def test_basic_functionality():
    """Test basic scraper functionality."""
    print("🧪 Testing Google Places Lead Scraper...")
    
    try:
        # Initialize components
        scraper = PlacesScraper()
        data_handler = DataHandler("test_output")
        
        print("✅ Successfully initialized scraper and data handler")
        
        # Test postal code generation
        postal_codes = generate_postal_codes("N2J 4Z2", 3)
        print(f"✅ Generated postal codes: {postal_codes}")
        
        # Test geocoding
        coordinates = scraper.geocode_postal_code("N2J 4Z2")
        if coordinates:
            print(f"✅ Geocoded N2J 4Z2 to {coordinates}")
        else:
            print("❌ Failed to geocode postal code")
            return False
        
        # Test basic search
        places = scraper.search_places("restaurants", coordinates, radius=1000)
        print(f"✅ Found {len(places)} restaurants near N2J 4Z2")
        
        if places:
            # Test data extraction
            business_data = scraper.extract_business_data(places[0], detailed=False)
            print(f"✅ Extracted data for: {business_data.get('name', 'Unknown')}")
            
            # Test data saving
            data_handler.save_businesses([business_data], continuous=False)
            print("✅ Successfully saved test data")
            
            # Show statistics
            stats = data_handler.get_statistics()
            print(f"✅ Statistics: {stats['total_records']} records saved")
        
        print("\n🎉 All tests passed! The scraper is working correctly.")
        print("\nReady to run:")
        print('python main.py --query "Dental offices in {}" --start-postal "N2J 4Z2" --count 5')
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nCheck your API key and internet connection.")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1) 