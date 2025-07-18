# Google Places Lead Scraper

A Python-based automation tool that uses the Google Places API to extract business leads from Google Maps. Much more reliable and faster than browser automation approaches.

## Features

- **Google Places API Integration**: Official API for reliable, structured data
- **Multi-Region Support**: Canadian postal codes, US ZIP codes, UK postal codes
- **Smart Deduplication**: Avoids duplicate businesses using place_id and fuzzy matching
- **Continuous Saving**: Data saved incrementally to prevent loss
- **Rate Limiting**: Built-in API quota management and request delays
- **Parallel Processing**: Optional multi-threading for faster scraping
- **Data Export**: Both CSV and formatted XLSX output
- **Progress Tracking**: Real-time progress updates and ETA
- **Graceful Shutdown**: CTRL+C handling with data preservation
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Installation

1. **Clone or download the files**
2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Verify your API key** in `config.py` (already set to your key)

## Quick Start

Basic usage:
```bash
python main.py --query "Dental offices in {}" --start-postal "N2J 4Z2" --count 25
```

With parallel processing:
```bash
python main.py --query "Restaurants in {}" --start-postal "10001" --parallel --max-workers 5
```

## Usage Examples

### Canadian Postal Codes
```bash
# Dental offices in Ontario
python main.py -q "Dental offices in {}" -p "N2J 4Z2" -c 50

# Restaurants in Toronto area
python main.py -q "Restaurants in {}" -p "M5V 3A8" -c 30 --parallel
```

### US ZIP Codes
```bash
# Lawyers in New York
python main.py -q "Lawyers in {}" -p "10001" -c 100

# Gas stations in California
python main.py -q "Gas stations in {}" -p "90210" -c 75 --max-workers 3
```

### UK Postal Codes
```bash
# Hotels in London
python main.py -q "Hotels in {}" -p "SW1A 1AA" -c 40

# Pharmacies in Manchester
python main.py -q "Pharmacies in {}" -p "M1 1AA" -c 60
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Search query template with {} placeholder | Required |
| `--start-postal` | `-p` | Starting postal code | Required |
| `--count` | `-c` | Number of postal codes to generate | 50 |
| `--output-dir` | `-o` | Output directory for results | `output` |
| `--api-key` | | Google Places API key | From config.py |
| `--parallel` | | Enable parallel processing | False |
| `--max-workers` | | Number of parallel workers | 3 |
| `--basic` | | Skip detailed place info (faster) | False |
| `--verbose` | `-v` | Enable verbose logging | False |

## Configuration

Edit `config.py` to customize:

```python
# Rate limiting
REQUEST_DELAY_MIN = 0.5  # Minimum delay between requests
REQUEST_DELAY_MAX = 1.5  # Maximum delay between requests
MAX_REQUESTS_PER_MINUTE = 100  # Conservative API limit

# Search settings
DEFAULT_RADIUS = 5000  # Search radius in meters
MAX_RESULTS_PER_LOCATION = 60  # Max results per postal code

# Output settings
OUTPUT_DIR = "output"
CSV_FILENAME = "leads.csv"
XLSX_FILENAME = "leads.xlsx"
```

## Output Format

The tool generates two output files:

### CSV File (`leads.csv`)
Comma-separated values with columns:
- `name`: Business name
- `address`: Full formatted address
- `phone`: Formatted phone number
- `website`: Business website URL
- `rating`: Google rating (1-5 stars)
- `review_count`: Number of reviews
- `business_status`: Operational status
- `primary_type`: Main business category
- `all_types`: All business categories
- `opening_hours`: Operating hours
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `place_id`: Unique Google place identifier
- `search_query`: Original search query used
- `search_location`: Postal code searched
- `scraped_at`: Timestamp of extraction

### XLSX File (`leads.xlsx`)
Formatted Excel file with:
- Auto-sized columns
- Header formatting
- Data filters
- Professional appearance

## API Costs

Google Places API pricing (approximate):
- **Text Search**: $32 per 1,000 requests
- **Place Details**: $17 per 1,000 requests
- **Geocoding**: $5 per 1,000 requests

**Estimated cost per postal code**: $0.10 - $0.15
**Daily free quota**: $200 credit = ~1,300-2,000 postal codes

## Rate Limiting

The tool implements conservative rate limiting:
- 0.5-1.5 second delays between requests
- Maximum 100 requests per minute
- Automatic quota management
- Graceful handling of API limits

## Data Quality

### Validation
- Must have business name
- Must have contact info (address, phone, or website)
- Filters out test/placeholder data
- Validates data completeness

### Deduplication
- **Exact matching**: Using Google place_id
- **Fuzzy matching**: Using normalized name/address/phone
- **Continuous**: Prevents duplicates across sessions

## Troubleshooting

### Common Issues

**API Key Issues**:
```bash
Error: Google Places API key is required
```
- Verify your API key in `config.py`
- Check API key permissions in Google Cloud Console
- Ensure Places API is enabled

**Rate Limiting**:
```bash
Rate limit reached. Sleeping for X seconds
```
- Normal behavior, tool will automatically wait
- Reduce `MAX_REQUESTS_PER_MINUTE` in config if needed

**Geocoding Failures**:
```bash
Could not geocode postal code: ABC123
```
- Postal code might be invalid or non-existent
- Check postal code format for your region

**No Results**:
```bash
Found 0 places for query
```
- Try broader search terms
- Increase search radius in config
- Verify postal code has businesses of that type

### Performance Tips

1. **Use parallel processing** for faster results:
   ```bash
   python main.py --query "..." --start-postal "..." --parallel --max-workers 5
   ```

2. **Use basic mode** for faster, less detailed results:
   ```bash
   python main.py --query "..." --start-postal "..." --basic
   ```

3. **Adjust batch sizes** in config for memory optimization

4. **Monitor API quotas** in Google Cloud Console

## Advanced Usage

### Custom Postal Code Lists
Modify `utils.py` to use custom postal code lists:

```python
postal_codes = ["N2J 4Z2", "N2J 4Z3", "N2J 4Z4"]  # Custom list
# Skip the generate_postal_codes() call in main.py
```

### Data Filtering
Export filtered results:

```python
from data_handler import DataHandler

handler = DataHandler()

# Export only businesses with ratings >= 4.0
def high_rated_filter(row):
    return row.get('rating', 0) >= 4.0

handler.export_filtered_data(high_rated_filter, "high_rated_leads.csv")
```

### API Optimization
For high-volume scraping:

1. **Increase API quotas** in Google Cloud Console
2. **Use multiple API keys** (implement key rotation)
3. **Implement retry logic** for failed requests
4. **Cache geocoding results** to reduce API calls

## Legal Compliance

- ✅ Uses official Google Places API (no TOS violations)
- ✅ Respects rate limits and API quotas
- ✅ Only accesses publicly available business data
- ✅ No browser automation or scraping detection issues

**Note**: Always comply with:
- Google Places API Terms of Service
- Local data privacy laws (GDPR, CCPA, etc.)
- Business contact preferences
- Rate limiting and fair use policies

## Support

For issues:
1. Check the logs in `scraper.log`
2. Verify API key and quotas
3. Test with a small `--count` first
4. Use `--verbose` for detailed debugging

## Cost Calculator

Estimate your costs:
- **25 postal codes** ≈ $2.50-3.75
- **100 postal codes** ≈ $10-15
- **500 postal codes** ≈ $50-75

Monitor usage in [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).

---

**Ready to start?** Run your first search:
```bash
python main.py --query "Dental offices in {}" --start-postal "N2J 4Z2" --count 10
``` 