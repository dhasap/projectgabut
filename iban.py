import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

# Map 2-letter country codes to Country Names for URL (randomiban.com)
# URL Pattern: https://randomiban.com/?country=Germany
COUNTRY_NAMES_URL = {
    'gb': 'United Kingdom',
    'de': 'Germany',
    'fr': 'France',
    'nl': 'Netherlands',
    'es': 'Spain',
    'it': 'Italy',
    'ch': 'Switzerland',
    'be': 'Belgium',
    'pl': 'Poland',
    'at': 'Austria',
    'pt': 'Portugal',
    'se': 'Sweden',
    'no': 'Norway',
    'dk': 'Denmark',
    'fi': 'Finland',
    'cz': 'Czech Republic',
    'hu': 'Hungary',
    'ie': 'Ireland',
    'ro': 'Romania',
    'gr': 'Greece'
}

FAKEIBAN_COUNTRIES = COUNTRY_NAMES_URL

def get_fake_iban(country_code):
    """
    Hanya melakukan scraping IBAN dari randomiban.com.
    Tidak ada fallback Faker lokal.
    Returns: IBAN string or None.
    """
    country_code = country_code.lower()
    country_name = COUNTRY_NAMES_URL.get(country_code)
    
    if country_name:
        try:
            # Scrape from randomiban.com
            url = f"https://randomiban.com/?country={country_name}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Target: <div id="demo">IBAN...</div>
                iban_div = soup.find('div', id='demo')
                if iban_div:
                    iban_text = iban_div.text.strip()
                    if iban_text and len(iban_text) > 10: # Basic validation
                        return iban_text
        except Exception as e:
            logger.error(f"Scraping IBAN failed for {country_code}: {e}")

    return None

def get_country_name(code):
    return FAKEIBAN_COUNTRIES.get(code.lower(), code.upper())