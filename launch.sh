#!/bin/bash
echo "🚀 Starting Google Places Lead Scraper Web Interface..."
echo "============================================="

# Activate virtual environment
source lead_scraper_env/bin/activate

# Launch Streamlit app
echo "📱 Opening Streamlit web interface..."
echo "🌐 App will be available at: http://localhost:8501"
echo "💡 Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py 