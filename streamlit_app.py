#!/usr/bin/env python3
"""
Streamlit Web Interface for Google Places Lead Scraper
A user-friendly web app for extracting business leads
"""

import streamlit as st
import pandas as pd
import time
import threading
import queue
from datetime import datetime

from places_scraper import PlacesScraper
from data_handler import DataHandler
from utils import generate_postal_codes, validate_query_template, detect_postal_code_type, geocode_area_name
import config

# Page configuration
st.set_page_config(
    page_title="Google Places Lead Scraper",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        color: #155724;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = []
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'progress_queue' not in st.session_state:
    st.session_state.progress_queue = queue.Queue()
if 'results_queue' not in st.session_state:
    st.session_state.results_queue = queue.Queue()

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Google Places Lead Scraper</h1>
        <p>Extract high-quality business leads using Google Places API</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key section
        st.subheader("🔑 API Settings")
        
        # Check if API key is configured in environment
        if config.GOOGLE_API_KEY:
            st.success("✅ API Key configured from environment")
            api_key = config.GOOGLE_API_KEY  # Use the env API key
            
            # Option to override with custom key
            use_custom_key = st.checkbox("Use custom API key", value=False)
            if use_custom_key:
                api_key = st.text_input(
                    "Custom Google Places API Key",
                    type="password",
                    help="Override the environment API key"
                )
                if not api_key:
                    api_key = config.GOOGLE_API_KEY  # Fallback to env key
        else:
            st.error("❌ API Key not found in environment")
            api_key = st.text_input(
                "Google Places API Key",
                type="password",
                help="Enter your Google Places API key"
            )
        
        st.divider()
        
        # Search Configuration
        st.subheader("🔍 Search Configuration")
        
        query_template = st.text_input(
            "Search Query Template",
            value="Dental offices in {}",
            help="Use {} as placeholder for location"
        )
        
        # Search mode selection
        search_mode = st.radio(
            "Search Mode",
            ["📍 By Postal Code", "🏙️ By Area Name"],
            help="Choose whether to search by postal codes or area names"
        )
        
        if search_mode == "📍 By Postal Code":
            start_postal = st.text_input(
                "Starting Postal Code",
                value="N2J 4Z2",
                help="Starting postal code (Canadian, US, or UK format)"
            )
            
            count = st.slider(
                "Number of Postal Codes",
                min_value=1,
                max_value=100,
                value=10,
                help="Number of postal codes to generate and search"
            )
            
            # Store for later use
            location_input = start_postal
            search_type = "postal_code"
            
        else:  # By Area Name
            area_names = st.text_area(
                "Area Names (one per line)",
                value="Waterloo, ON\nKitchener, ON\nCambridge, ON",
                help="Enter area names, one per line (e.g., 'Toronto, ON' or 'New York, NY')",
                height=150
            )
            
            area_list = [area.strip() for area in area_names.split('\n') if area.strip()]
            count = len(area_list)
            st.info(f"Will search {count} areas")
            
            # Store for later use
            location_input = area_list
            search_type = "area_name"
        
        st.divider()
        
        # Advanced Settings
        st.subheader("⚡ Performance Settings")
        
        use_parallel = st.checkbox(
            "Enable Parallel Processing",
            value=False,
            help="Use multiple threads for faster scraping"
        )
        
        max_workers = st.slider(
            "Max Workers",
            min_value=1,
            max_value=10,
            value=3,
            disabled=not use_parallel,
            help="Number of parallel workers (if enabled)"
        )
        
        detailed_data = st.checkbox(
            "Get Detailed Data",
            value=True,
            help="Fetch additional place details (slower but more data)"
        )
        
        output_dir = st.text_input(
            "Output Directory",
            value="output",
            help="Directory to save results"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 Lead Extraction")
        
        # Validation
        validation_container = st.container()
        with validation_container:
            if not validate_query_template(query_template):
                st.error("❌ Query template must contain {} placeholder")
                return
            
            if search_type == "postal_code":
                postal_type = detect_postal_code_type(start_postal)
                if postal_type:
                    st.success(f"✅ Detected {postal_type.upper()} postal code format")
                else:
                    st.error("❌ Invalid postal code format")
                    return
            else:  # area_name
                if not area_list:
                    st.error("❌ Please enter at least one area name")
                    return
                else:
                    st.success(f"✅ Ready to search {len(area_list)} areas")
            
            if not api_key:
                st.error("❌ Please provide Google Places API key")
                return
        
        # Cost estimation
        st.subheader("💰 Cost Estimation")
        estimated_cost = count * 0.12  # Rough estimate
        col_cost1, col_cost2, col_cost3 = st.columns(3)
        
        with col_cost1:
            st.metric("Postal Codes", count)
        with col_cost2:
            st.metric("Estimated Cost", f"${estimated_cost:.2f}")
        with col_cost3:
            st.metric("Est. Results", f"{count * 15}-{count * 25}")
        
        # Control buttons
        st.subheader("🎮 Controls")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            start_scraping = st.button(
                "🚀 Start Scraping",
                disabled=st.session_state.scraping_in_progress,
                use_container_width=True
            )
        
        with col_btn2:
            stop_scraping = st.button(
                "⏹️ Stop Scraping",
                disabled=not st.session_state.scraping_in_progress,
                use_container_width=True
            )
        
        with col_btn3:
            clear_results = st.button(
                "🗑️ Clear Results",
                disabled=st.session_state.scraping_in_progress,
                use_container_width=True
            )
        
        # Progress section
        if st.session_state.scraping_in_progress:
            st.subheader("📊 Progress")
            progress_container = st.container()
            status_container = st.container()
        
        # Results section will be displayed at the bottom
    
    with col2:
        st.header("📈 Quick Stats")
        if st.session_state.get('all_results'):
            df = pd.DataFrame(st.session_state.all_results)
            st.metric("Total Leads", len(df))
            if 'phone' in df.columns:
                with_phone = df['phone'].notna().sum()
                st.metric("With Phone", f"{with_phone}/{len(df)}")
        else:
            st.info("No results yet!")
        
        st.header("💡 Tips") 
        st.info("• Use specific queries like 'Dental offices in {}'\n• Large cities will find 100+ results")
        
        st.header("📋 Examples")
        st.code("Dental offices in {}\nRestaurants in {}\nLawyers in {}")
    
    # Handle button clicks
    if start_scraping:
        start_scraping_process(
            query_template, location_input, search_type, count, api_key,
            use_parallel, max_workers, detailed_data, output_dir
        )
    
    if stop_scraping:
        st.session_state.scraping_in_progress = False
        st.warning("⏹️ Scraping stopped by user")
    
    if clear_results:
        st.session_state.scraping_results = []
        if 'all_results' in st.session_state:
            del st.session_state.all_results
        if 'current_data' in st.session_state:
            del st.session_state.current_data
        st.success("🗑️ Results cleared")
        st.rerun()

def start_scraping_process(query_template, location_input, search_type, count, api_key, 
                         use_parallel, max_workers, detailed_data, output_dir):
    """Start the scraping process in a separate thread."""
    
    st.session_state.scraping_in_progress = True
    st.session_state.scraping_results = []
    
    # Clear queues
    while not st.session_state.progress_queue.empty():
        st.session_state.progress_queue.get()
    while not st.session_state.results_queue.empty():
        st.session_state.results_queue.get()
    
    # Start scraping thread with queue references
    thread = threading.Thread(
        target=scraping_worker,
        args=(query_template, location_input, search_type, count, api_key,
              use_parallel, max_workers, detailed_data, output_dir,
              st.session_state.progress_queue, st.session_state.results_queue)
    )
    thread.daemon = True
    thread.start()
    
    st.success("🚀 Scraping started! Check progress below.")
    st.rerun()

def scraping_worker(query_template, location_input, search_type, count, api_key,
                   use_parallel, max_workers, detailed_data, output_dir,
                   progress_queue, results_queue):
    """Worker function for scraping in background thread."""
    
    # Store a reference to check scraping status
    scraping_active = True
    
    try:
        # Initialize scraper
        scraper = PlacesScraper(api_key)
        data_handler = DataHandler(output_dir)
        
        # Generate locations based on search type
        if search_type == "postal_code":
            locations = generate_postal_codes(location_input, count)
            progress_queue.put({
                'type': 'info',
                'message': f'Generated {len(locations)} postal codes'
            })
        else:  # area_name
            locations = location_input  # Already a list of area names
            progress_queue.put({
                'type': 'info',
                'message': f'Searching {len(locations)} areas'
            })
        
        # Process locations
        all_results = []
        
        for i, location in enumerate(locations):
            # Check if we should continue (simplified check)
            try:
                import streamlit as st_check
                if hasattr(st_check, 'session_state') and hasattr(st_check.session_state, 'scraping_in_progress'):
                    if not st_check.session_state.scraping_in_progress:
                        break
            except:
                pass  # Continue if we can't check session state
            
            progress_queue.put({
                'type': 'progress',
                'current': i + 1,
                'total': len(locations),
                'location': location
            })
            
            try:
                # Get coordinates based on search type
                if search_type == "postal_code":
                    coordinates = scraper.geocode_postal_code(location)
                else:  # area_name
                    # For area names, get coordinates by geocoding the area name
                    coordinates = geocode_area_name(location, api_key)
                
                if not coordinates:
                    progress_queue.put({
                        'type': 'warning',
                        'message': f'Could not geocode {location}'
                    })
                    continue
                
                # Format query and search
                query = query_template.format(location)
                scraper.current_query = query
                scraper.current_location = location
                
                # Use enhanced search for area names (large cities)
                is_large_city = (search_type == "area_name")
                places = scraper.search_places(query, coordinates, is_large_city=is_large_city)
                
                # Extract business data (simplified)
                for place in places:
                    try:
                        business_data = scraper.extract_business_data(place, detailed_data)
                        all_results.append(business_data)
                    except Exception as e:
                        continue
                
                progress_queue.put({
                    'type': 'success',
                    'message': f'Found {len(places)} businesses in {location}'
                })
            
            except Exception as e:
                progress_queue.put({
                    'type': 'error',
                    'message': f'Error processing {location}: {str(e)}'
                })
                continue
        
        # Send results directly without complex processing
        results_queue.put({
            'type': 'completed',
            'results': all_results,
            'total_count': len(all_results)
        })
        
    except Exception as e:
        results_queue.put({
            'type': 'error',
            'message': f'Scraping failed: {str(e)}'
        })
    
    finally:
        # Ensure scraping is marked as complete
        try:
            progress_queue.put({
                'type': 'complete_status',
                'scraping_complete': True
            })
        except:
            pass

def display_results():
    """Display scraping results immediately and seamlessly."""
    
    st.header("📋 Results")
    
    # Check for new results from queue
    try:
        while not st.session_state.results_queue.empty():
            result = st.session_state.results_queue.get_nowait()
            
            if result['type'] == 'completed':
                # Mark scraping as complete
                st.session_state.scraping_in_progress = False
                
                # Get results directly - no complex processing
                results = result['results']
                total_count = result['total_count']
                
                # Show completion message
                st.success(f"✅ Found {total_count} businesses!")
                
                # Simple append - no expensive operations
                if results:
                    # Just extend the list - fastest operation
                    if 'all_results' not in st.session_state:
                        st.session_state.all_results = []
                    st.session_state.all_results.extend(results)
                    
                    # Create DataFrame only when needed
                    df = pd.DataFrame(st.session_state.all_results)
                    
                    # Fix only rating column quickly
                    if 'rating' in df.columns:
                        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
                    
                    # Display table immediately
                    st.subheader("📊 Business Leads")
                    display_cols = ['name', 'address', 'phone', 'email', 'website', 'rating']
                    available_cols = [col for col in display_cols if col in df.columns]
                    st.dataframe(
                        df[available_cols].fillna(''),
                        use_container_width=True,
                        height=400
                    )
                    
                    # Download button - CSV generated only when clicked
                    @st.cache_data
                    def convert_df(df):
                        return df.to_csv(index=False)
                    
                    csv_data = convert_df(df)
                    st.download_button(
                        label="📄 Download CSV",
                        data=csv_data,
                        file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_results"
                    )
                else:
                    st.warning("No businesses found.")
            
            elif result['type'] == 'error':
                st.error(f"❌ {result['message']}")
                st.session_state.scraping_in_progress = False
    
    except queue.Empty:
        pass
    
    # Show existing data if available
    if not st.session_state.get('scraping_in_progress', False) and 'all_results' in st.session_state and st.session_state.all_results:
        df = pd.DataFrame(st.session_state.all_results)
        
        # Fix data types
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        st.subheader("📊 Business Leads")
        display_cols = ['name', 'address', 'phone', 'email', 'website', 'rating']
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(
            df[available_cols].fillna(''),
            use_container_width=True,
            height=400
        )
        
        # Cached download button
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False)
        
        csv_data = convert_df(df)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_existing"
        )
    elif not st.session_state.get('scraping_in_progress', False):
        st.info("💡 No data available yet. Start scraping to see results here!")



# Simple progress monitoring
if st.session_state.get('scraping_in_progress', False):
    try:
        # Check for progress updates
        while not st.session_state.progress_queue.empty():
            progress_update = st.session_state.progress_queue.get_nowait()
            
            if progress_update['type'] == 'progress':
                current = progress_update['current']
                total = progress_update['total'] 
                location = progress_update['location']
                st.text(f"Processing {current}/{total}: {location}")
            
            elif progress_update['type'] == 'complete_status':
                st.session_state.scraping_in_progress = False
                st.rerun()
    
    except queue.Empty:
        pass
    
    # Auto-refresh while scraping
    time.sleep(1)
    st.rerun()

# Always display results section
display_results()

if __name__ == "__main__":
    main() 