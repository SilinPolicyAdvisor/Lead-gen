import pandas as pd
import os
import logging
from typing import List, Dict, Set
import hashlib
from pathlib import Path
import config

class DataHandler:
    def __init__(self, output_dir: str = None):
        """Initialize the data handler."""
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        
        self.csv_path = self.output_dir / config.CSV_FILENAME
        self.xlsx_path = self.output_dir / config.XLSX_FILENAME
        
        # Track seen businesses for deduplication
        self.seen_hashes: Set[str] = set()
        self.seen_place_ids: Set[str] = set()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Load existing data if files exist
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing data to continue where we left off."""
        if self.csv_path.exists():
            try:
                df = pd.read_csv(self.csv_path)
                # Rebuild deduplication sets
                for _, row in df.iterrows():
                    if pd.notna(row.get('place_id')):
                        self.seen_place_ids.add(row['place_id'])
                    
                    # Create hash for fuzzy deduplication
                    business_hash = self._create_business_hash(row.to_dict())
                    if business_hash:
                        self.seen_hashes.add(business_hash)
                
                self.logger.info(f"Loaded {len(df)} existing records from {self.csv_path}")
            except Exception as e:
                self.logger.error(f"Error loading existing data: {e}")
    
    def _create_business_hash(self, business: Dict) -> str:
        """Create a hash for fuzzy deduplication based on name and address."""
        try:
            # Normalize data for comparison
            name = str(business.get('name', '')).lower().strip()
            address = str(business.get('address', '')).lower().strip()
            phone = str(business.get('phone', '')).strip()
            
            # Remove common variations
            name = name.replace('inc.', '').replace('inc', '').replace('ltd.', '').replace('ltd', '')
            name = name.replace('llc', '').replace('corp.', '').replace('corp', '').strip()
            
            # Create hash from normalized data
            hash_string = f"{name}|{address}|{phone}"
            return hashlib.md5(hash_string.encode()).hexdigest()
        except Exception:
            return None
    
    def _validate_business_data(self, business: Dict) -> bool:
        """Validate business data quality."""
        # Must have name
        if not business.get('name'):
            return False
        
        # Must have some contact info (address, phone, or website)
        if not any([
            business.get('address'),
            business.get('phone'),
            business.get('website')
        ]):
            return False
        
        # Filter out obviously invalid data
        name = business.get('name', '').lower()
        if any(keyword in name for keyword in ['test', 'example', 'placeholder']):
            return False
        
        return True
    
    def deduplicate_businesses(self, businesses: List[Dict]) -> List[Dict]:
        """Remove duplicate businesses from the list."""
        unique_businesses = []
        
        for business in businesses:
            # Skip if validation fails
            if not self._validate_business_data(business):
                self.logger.debug(f"Skipping invalid business: {business.get('name')}")
                continue
            
            # Check place_id first (exact match)
            place_id = business.get('place_id')
            if place_id and place_id in self.seen_place_ids:
                self.logger.debug(f"Skipping duplicate place_id: {place_id}")
                continue
            
            # Check fuzzy hash
            business_hash = self._create_business_hash(business)
            if business_hash and business_hash in self.seen_hashes:
                self.logger.debug(f"Skipping fuzzy duplicate: {business.get('name')}")
                continue
            
            # Add to unique list and tracking sets
            unique_businesses.append(business)
            if place_id:
                self.seen_place_ids.add(place_id)
            if business_hash:
                self.seen_hashes.add(business_hash)
        
        self.logger.info(f"Deduplicated {len(businesses)} -> {len(unique_businesses)} businesses")
        return unique_businesses
    
    def save_to_csv(self, businesses: List[Dict], mode: str = 'a'):
        """Save businesses to CSV file."""
        if not businesses:
            return
        
        try:
            df = pd.DataFrame(businesses)
            
            # Reorder columns for better readability
            column_order = [
                'name', 'address', 'phone', 'website', 'rating', 'review_count',
                'business_status', 'primary_type', 'all_types', 'opening_hours',
                'latitude', 'longitude', 'place_id', 'search_query', 
                'search_location', 'scraped_at'
            ]
            
            # Only include columns that exist
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            # Save with header only if file doesn't exist
            header = not self.csv_path.exists() if mode == 'a' else True
            
            df.to_csv(self.csv_path, mode=mode, header=header, index=False, encoding='utf-8')
            
            self.logger.info(f"Saved {len(businesses)} businesses to CSV")
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
    
    def save_to_xlsx(self, businesses: List[Dict] = None):
        """Save all businesses to XLSX file with formatting."""
        try:
            # Load all data from CSV if no specific businesses provided
            if businesses is None:
                if not self.csv_path.exists():
                    return
                df = pd.read_csv(self.csv_path)
            else:
                df = pd.DataFrame(businesses)
            
            if df.empty:
                return
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(self.xlsx_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Leads', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Leads']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column widths
                for i, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    )
                    worksheet.set_column(i, i, min(max_length + 2, 50))
                
                # Add filters
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            self.logger.info(f"Saved {len(df)} businesses to XLSX")
            
        except Exception as e:
            self.logger.error(f"Error saving to XLSX: {e}")
    
    def save_businesses(self, businesses: List[Dict], continuous: bool = True):
        """Save businesses with deduplication and validation."""
        if not businesses:
            return
        
        # Deduplicate and validate
        unique_businesses = self.deduplicate_businesses(businesses)
        
        if not unique_businesses:
            self.logger.info("No new unique businesses to save")
            return
        
        # Save to CSV (append mode for continuous saving)
        self.save_to_csv(unique_businesses, mode='a' if continuous else 'w')
        
        # Update XLSX with all data
        if continuous:
            self.save_to_xlsx()  # Rebuild from CSV
        else:
            self.save_to_xlsx(unique_businesses)
        
        self.logger.info(f"Successfully saved {len(unique_businesses)} new businesses")
    
    def get_statistics(self) -> Dict:
        """Get statistics about collected data."""
        stats = {
            'total_records': 0,
            'unique_places': 0,
            'unique_names': 0,
            'has_phone': 0,
            'has_website': 0,
            'has_rating': 0,
            'avg_rating': 0.0,
            'business_types': {}
        }
        
        try:
            if self.csv_path.exists():
                df = pd.read_csv(self.csv_path)
                stats['total_records'] = len(df)
                stats['unique_places'] = df['place_id'].nunique()
                stats['unique_names'] = df['name'].nunique()
                stats['has_phone'] = df['phone'].notna().sum()
                stats['has_website'] = df['website'].notna().sum()
                stats['has_rating'] = df['rating'].notna().sum()
                
                if stats['has_rating'] > 0:
                    stats['avg_rating'] = df['rating'].mean()
                
                # Business types distribution
                if 'primary_type' in df.columns:
                    stats['business_types'] = df['primary_type'].value_counts().to_dict()
        
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
        
        return stats
    
    def export_filtered_data(self, filter_func, filename: str):
        """Export filtered subset of data."""
        try:
            if not self.csv_path.exists():
                return
            
            df = pd.read_csv(self.csv_path)
            filtered_df = df[df.apply(filter_func, axis=1)]
            
            export_path = self.output_dir / filename
            filtered_df.to_csv(export_path, index=False)
            
            self.logger.info(f"Exported {len(filtered_df)} filtered records to {export_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting filtered data: {e}") 