Google Maps Lead Automation Tool - Prompt for Cursor

Build a Python-based automation tool that uses Selenium WebDriver and the "Instant Data Scraper" Chrome extension to extract business leads from Google Maps. The tool should:

- Accept a search query template (e.g., "Dental offices in {}") and a starting pincode (e.g., "N2J 4Z2") as input.
- Automatically substitute the pincode into the query and search Google Maps.
- Use Selenium to automate Chrome, load the Instant Data Scraper extension, and trigger it to extract business data from each search result page.
- Iterate through postal codes (pincodes), generating new searches for each, until the user stops the process.
- Extract data such as business name, address, phone, website, ratings, and any other available info.
- Save all results continuously into both CSV and XLSX files, using pandas and openpyxl/xlsxwriter.
- Validate and deduplicate data before saving.
- Implement rate limiting (random delays, e.g., 2-5 seconds), user-agent rotation, and optional proxy support to avoid detection or bans.
- Log progress and errors in real time.
- Structure the code modularly for maintainability, with clear separation for automation, data extraction, export, and utility functions.
- Optionally, support parallel processing (multiprocessing or concurrent.futures) to speed up scraping.
- Optionally, provide a CLI (using argparse) for user inputs and configuration.

Enhancements to consider:
- Captcha detection and pause/resume handling.
- Enrich data with Google Places API or other business info APIs.
- Use machine learning for deduplication, business classification, and data quality scoring.
- Build a simple Flask or FastAPI dashboard for real-time monitoring.
- Use Docker for easy deployment.
- Ensure GDPR and data privacy compliance.

Example usage:
python main.py --query "Dental offices in {}" --start-postal "N2J 4Z2" --output-dir output/

References:
- Selenium: https://selenium.dev/documentation/
- Instant Data Scraper: https://chrome.google.com/webstore/detail/instant-data-scraper
- pandas: https://pandas.pydata.org/
- Google Maps Terms: https://maps.google.com/help/terms_maps/

Disclaimer: This tool is for educational and ethical use only. Always comply with data privacy laws and website terms of service.
