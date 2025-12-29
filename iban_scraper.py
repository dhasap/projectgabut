import requests
import random
from faker import Faker
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Fallback Faker instance
fake = Faker()

# List of countries likely supported by fakeiban.org (European/SEPA mostly)
FAKEIBAN_COUNTRIES = {
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

def get_fake_iban(country_code):
    """
    Mencoba mengambil IBAN dari fakeiban.org.
    Jika gagal, fallback ke library Faker lokal.
    """
    country_code = country_code.lower()
    
    # 1. Attempt to scrape/request from fakeiban.org
    # Based on standard form behavior analysis
    url = "https://fakeiban.org/"
    
    # Payload tebakan berdasarkan elemen form umum
    # Site returns HTML usually, but let's try to extract from response
    payload = {
        'country': country_code,
        'quantity': '1',
        'format': 'json' # Hoping for JSON response directly
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Referer': 'https://fakeiban.org/',
        'Origin': 'https://fakeiban.org'
    }

    try:
        # Menggunakan session untuk handling cookies jika perlu
        s = requests.Session()
        # Get page first to set cookies/tokens
        s.get(url, headers=headers, timeout=5)
        
        # Post Request
        # Note: Endpoint might be /process or just /
        r = s.post(url, data=payload, headers=headers, timeout=10)
        
        if r.status_code == 200:
            # Check content type
            if 'application/json' in r.headers.get('Content-Type', ''):
                data = r.json()
                # Adjust key extraction based on actual JSON structure
                # Typically array of strings or object
                if isinstance(data, list) and len(data) > 0:
                    return data[0]['iban'] if isinstance(data[0], dict) else data[0]
                elif isinstance(data, dict):
                     return data.get('iban') or data.get('0')
            
            # If HTML response (fallback parsing)
            elif 'text/html' in r.headers.get('Content-Type', ''):
                 from bs4 import BeautifulSoup
                 soup = BeautifulSoup(r.text, 'html.parser')
                 # Try to find result container
                 # Common classes: result, iban, output
                 # Assuming it returns a textarea or div with result
                 textarea = soup.find('textarea')
                 if textarea:
                     return textarea.text.strip()
                     
    except Exception as e:
        logger.warning(f"Scraping fakeiban.org failed: {e}. Falling back to Faker.")

    # 2. Fallback: Use Faker
    # Map country code to Faker locale if possible, or just use general IBAN
    try:
        if country_code == 'gb':
            return fake.iban() # Default often GB/Random
        else:
            # Faker's iban() allows country_code param
            return fake.iban(country_code=country_code.upper())
    except Exception as e:
        logger.error(f"Faker IBAN generation failed: {e}")
        return "Gagal membuat IBAN."

def get_country_name(code):
    return FAKEIBAN_COUNTRIES.get(code.lower(), code.upper())
