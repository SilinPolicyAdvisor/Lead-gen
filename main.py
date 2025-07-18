#!/usr/bin/env python3
"""
Google Maps Lead Automation Tool
Extract business leads using Google Places API
"""

import argparse
import logging
import os
import sys
from typing import List
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from places_scraper import PlacesScraper
from data_handler import DataHandler
from utils import (
    generate_postal_codes, 
    validate_query_template, 
    ProgressTracker,
    format_business_summary,
    batch_list
)
import config

class LeadScraper:
    def __init__(self, api_key: str = None, output_dir: str = None, max_workers: int = 1):
        """Initialize the lead scraper."""
        self.scraper = PlacesScraper(api_key)
        self.data_handler = DataHandler(output_dir)
        self.max_workers = max_workers
        self.running = True
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format=config.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('scraper.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def scrape_single_location(self, query_template: str, postal_code: str, 
                             detailed: bool = True) -> List[dict]:
        """Scrape a single postal code location."""
        if not self.running:
            return []
        
        try:
            # Geocode postal code
            coordinates = self.scraper.geocode_postal_code(postal_code)
            if not coordinates:
                self.logger.warning(f"Could not geocode: {postal_code}")
                return []
            
            # Format query
            query = query_template.format(postal_code)
            self.scraper.current_query = query
            self.scraper.current_location = postal_code
            
            # Search places
            places = self.scraper.search_places(query, coordinates)
            
            # Extract business data
            businesses = []
            for place in places:
                if not self.running:
                    break
                try:
                    business_data = self.scraper.extract_business_data(place, detailed)
                    businesses.append(business_data)
                except Exception as e:
                    self.logger.error(f"Error extracting data for place: {e}")
                    continue
            
            return businesses
            
        except Exception as e:
            self.logger.error(f"Error processing {postal_code}: {e}")
            return []
    
    def scrape_locations_parallel(self, query_template: str, postal_codes: List[str], 
                                detailed: bool = True, batch_size: int = 10) -> None:
        """Scrape multiple locations using parallel processing."""
        self.logger.info(f"Starting parallel scraping of {len(postal_codes)} locations")
        
        # Process in batches to manage memory and API limits
        for batch in batch_list(postal_codes, batch_size):
            if not self.running:
                break
            
            batch_results = []
            
            # Use ThreadPoolExecutor for I/O bound tasks
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks for current batch
                future_to_postal = {
                    executor.submit(self.scrape_single_location, query_template, postal_code, detailed): postal_code
                    for postal_code in batch
                }
                
                # Collect results with progress tracking
                with tqdm(total=len(batch), desc=f"Processing batch") as pbar:
                    for future in as_completed(future_to_postal):
                        if not self.running:
                            break
                        
                        postal_code = future_to_postal[future]
                        try:
                            businesses = future.result()
                            if businesses:
                                batch_results.extend(businesses)
                                self.logger.info(f"Found {len(businesses)} businesses in {postal_code}")
                        except Exception as e:
                            self.logger.error(f"Error processing {postal_code}: {e}")
                        
                        pbar.update(1)
            
            # Save batch results immediately
            if batch_results:
                self.data_handler.save_businesses(batch_results, continuous=True)
                self.logger.info(f"Saved {len(batch_results)} businesses from current batch")
    
    def scrape_locations_sequential(self, query_template: str, postal_codes: List[str], 
                                  detailed: bool = True) -> None:
        """Scrape locations sequentially with progress tracking."""
        self.logger.info(f"Starting sequential scraping of {len(postal_codes)} locations")
        
        progress = ProgressTracker(len(postal_codes))
        progress.start()
        
        all_results = []
        save_batch_size = 10  # Save every 10 locations
        
        for i, postal_code in enumerate(postal_codes):
            if not self.running:
                break
            
            progress.update(postal_code)
            
            businesses = self.scrape_single_location(query_template, postal_code, detailed)
            
            if businesses:
                all_results.extend(businesses)
                self.logger.info(f"Found {len(businesses)} businesses in {postal_code}")
            
            # Save periodically to avoid data loss
            if (i + 1) % save_batch_size == 0 or i == len(postal_codes) - 1:
                if all_results:
                    self.data_handler.save_businesses(all_results, continuous=True)
                    self.logger.info(f"Saved {len(all_results)} businesses (checkpoint)")
                    all_results = []  # Reset for next batch
        
        progress.finish()
    
    def run(self, query_template: str, start_postal: str, count: int = 50, 
            detailed: bool = True, parallel: bool = False, max_workers: int = 3) -> None:
        """Main execution method."""
        try:
            # Validate inputs
            if not validate_query_template(query_template):
                raise ValueError("Query template must contain {} placeholder")
            
            # Generate postal codes
            self.logger.info(f"Generating {count} postal codes starting from {start_postal}")
            postal_codes = generate_postal_codes(start_postal, count)
            
            # Display initial info
            print(f"\n{'='*60}")
            print(f"Google Places Lead Scraper")
            print(f"{'='*60}")
            print(f"Query Template: {query_template}")
            print(f"Starting Postal Code: {start_postal}")
            print(f"Total Locations: {len(postal_codes)}")
            print(f"Processing Mode: {'Parallel' if parallel else 'Sequential'}")
            print(f"Output Directory: {self.data_handler.output_dir}")
            print(f"{'='*60}\n")
            
            # Update max_workers if provided
            if parallel and max_workers:
                self.max_workers = max_workers
            
            # Start scraping
            if parallel:
                self.scrape_locations_parallel(query_template, postal_codes, detailed)
            else:
                self.scrape_locations_sequential(query_template, postal_codes, detailed)
            
            # Display final statistics
            self._display_final_stats()
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            raise
    
    def _display_final_stats(self):
        """Display final statistics and summary."""
        stats = self.data_handler.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETED")
        print(f"{'='*60}")
        print(f"Total Records: {stats['total_records']}")
        print(f"Unique Places: {stats['unique_places']}")
        print(f"Records with Phone: {stats['has_phone']}")
        print(f"Records with Website: {stats['has_website']}")
        print(f"Records with Rating: {stats['has_rating']}")
        
        if stats['has_rating'] > 0:
            print(f"Average Rating: {stats['avg_rating']:.1f}")
        
        print(f"\nTop Business Types:")
        for business_type, count in list(stats['business_types'].items())[:5]:
            print(f"  • {business_type}: {count}")
        
        print(f"\nFiles Created:")
        print(f"  • CSV: {self.data_handler.csv_path}")
        print(f"  • XLSX: {self.data_handler.xlsx_path}")
        print(f"{'='*60}")

def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Extract business leads using Google Places API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --query "Dental offices in {}" --start-postal "N2J 4Z2" --count 25
  python main.py --query "Restaurants in {}" --start-postal "10001" --parallel --max-workers 5
  python main.py --query "Lawyers in {}" --start-postal "SW1A 1AA" --output-dir "legal_leads"
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        required=True,
        help='Search query template with {} placeholder (e.g., "Dental offices in {}")'
    )
    
    parser.add_argument(
        '--start-postal', '-p',
        required=True,
        help='Starting postal code (e.g., "N2J 4Z2", "10001", "SW1A 1AA")'
    )
    
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=50,
        help='Number of postal codes to generate and search (default: 50)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default=config.OUTPUT_DIR,
        help=f'Output directory for results (default: {config.OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '--api-key',
        default=config.GOOGLE_API_KEY,
        help='Google Places API key (or set in config.py)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Use parallel processing for faster scraping'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=3,
        help='Maximum number of parallel workers (default: 3)'
    )
    
    parser.add_argument(
        '--basic',
        action='store_true',
        help='Skip detailed place information (faster but less data)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate API key
    if not args.api_key:
        print("Error: Google Places API key is required")
        print("Set it in config.py or use --api-key argument")
        sys.exit(1)
    
    # Create and run scraper
    try:
        scraper = LeadScraper(
            api_key=args.api_key,
            output_dir=args.output_dir,
            max_workers=args.max_workers
        )
        
        scraper.run(
            query_template=args.query,
            start_postal=args.start_postal,
            count=args.count,
            detailed=not args.basic,
            parallel=args.parallel,
            max_workers=args.max_workers
        )
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 