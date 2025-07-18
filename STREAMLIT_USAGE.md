# 🎯 Google Places Lead Scraper - Web Interface

## 🚀 Quick Start

### Launch the Web App:
```bash
# Method 1: Using the launch script
./launch.sh

# Method 2: Manual launch
source lead_scraper_env/bin/activate
streamlit run streamlit_app.py
```

### Access the Interface:
- **URL**: http://localhost:8501
- **Browser**: Chrome, Firefox, Safari, or Edge
- **Auto-opens**: Browser should open automatically

## 📱 Web Interface Features

### 🔧 Configuration Panel (Left Sidebar)
- **API Key**: Your Google Places API key (pre-filled)
- **Search Query**: Template with {} placeholder
- **Starting Postal Code**: Any valid postal code
- **Number of Codes**: How many locations to search
- **Parallel Processing**: Enable for faster scraping
- **Performance Settings**: Max workers and detailed data options

### 🎮 Main Dashboard
- **Validation**: Real-time input validation
- **Cost Estimation**: Approximate API costs
- **Control Buttons**: Start, Stop, Clear operations
- **Progress Tracking**: Real-time progress bars
- **Results Display**: Live statistics and data tables

### 📊 Results & Analytics
- **Live Statistics**: Total records, phone numbers, websites, ratings
- **Data Visualizations**: Business type charts, rating distributions
- **Interactive Data Table**: Sortable, filterable grid
- **Download Options**: CSV and Excel exports

## 💡 Usage Examples

### Example 1: Dental Offices
1. **Query**: `Dental offices in {}`
2. **Postal Code**: `N2J 4Z2`
3. **Count**: `10`
4. **Click**: 🚀 Start Scraping

### Example 2: Restaurants (Parallel)
1. **Query**: `Italian restaurants in {}`
2. **Postal Code**: `10001`
3. **Count**: `25`
4. **Enable**: ✅ Parallel Processing
5. **Workers**: `5`
6. **Click**: 🚀 Start Scraping

### Example 3: Business Services
1. **Query**: `Real estate agents in {}`
2. **Postal Code**: `SW1A 1AA`
3. **Count**: `15`
4. **Click**: 🚀 Start Scraping

## 🎯 Pro Tips

### ✅ Best Practices
- **Start Small**: Test with 5-10 postal codes first
- **Monitor Progress**: Watch the real-time progress bar
- **Check Statistics**: Review completion statistics
- **Download Results**: Export CSV/Excel when complete

### ⚡ Performance Tips
- **Enable Parallel**: For 20+ postal codes
- **Optimal Workers**: Use 3-5 workers max
- **Monitor API**: Check Google Cloud Console for quotas
- **Batch Processing**: Process in smaller batches for large runs

### 🔍 Query Examples
```
"Dental offices in {}"
"Italian restaurants in {}"
"Lawyers in {}"
"Auto repair shops in {}"
"Hair salons in {}"
"Real estate agents in {}"
"Pharmacies in {}"
"Veterinarians in {}"
```

## 📈 Understanding Results

### Key Metrics
- **Total Records**: Number of businesses found
- **With Phone**: Businesses with phone numbers
- **With Website**: Businesses with websites
- **Avg Rating**: Average Google rating

### Data Quality Indicators
- **High Quality**: ✅ Phone + Website + Rating
- **Medium Quality**: ⚠️ 2 of 3 contact methods
- **Low Quality**: ❌ Missing critical contact info

### Charts & Visualizations
- **Business Types**: Horizontal bar chart of categories
- **Rating Distribution**: Histogram of customer ratings
- **Interactive Table**: Sortable data grid with filters

## 🛠️ Troubleshooting

### Common Issues

**App Won't Start**:
```bash
# Make sure virtual environment is activated
source lead_scraper_env/bin/activate
# Check dependencies
pip install -r requirements.txt
```

**No Results Found**:
- Check API key validity
- Verify postal code format
- Try broader search terms
- Check Google Cloud Console quotas

**Slow Performance**:
- Enable parallel processing
- Reduce number of postal codes
- Use basic mode (disable detailed data)

**API Errors**:
- Check API key permissions
- Verify Places API (New) is enabled
- Monitor rate limits in real-time

### Port Issues
If port 8501 is busy:
```bash
streamlit run streamlit_app.py --server.port 8502
```

## 💰 Cost Monitoring

### Real-time Tracking
- **Live Cost Estimation**: Shows before scraping
- **Progress Monitoring**: Track API calls in real-time
- **Results Statistics**: Final cost calculation

### Google Cloud Console
Monitor your usage at:
- **Billing**: https://console.cloud.google.com/billing
- **APIs**: https://console.cloud.google.com/apis/dashboard
- **Quotas**: https://console.cloud.google.com/iam-admin/quotas

## 🔄 Workflow

### Typical Session
1. **Configure** search parameters
2. **Validate** inputs (auto-checked)
3. **Estimate** costs and results
4. **Start** scraping process
5. **Monitor** real-time progress
6. **Review** statistics and data
7. **Download** results (CSV/Excel)
8. **Analyze** data for outreach

### Multiple Searches
- **Clear Results**: Between different searches
- **Change Parameters**: Modify query/location
- **Export Data**: Save each search separately
- **Compare Results**: Track different business types

---

## 🎉 Enjoy Your Lead Generation!

The web interface makes it incredibly easy to extract high-quality business leads. Start with small tests and scale up as needed!

**Questions?** Check the logs in the terminal or review the README.md for detailed information. 