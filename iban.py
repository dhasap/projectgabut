import logging
from faker import Faker

# Set up logging
logger = logging.getLogger(__name__)

# Map 2-letter country codes to Faker locales
# This ensures we generate IBANs valid for the requested country
COUNTRY_LOCALES = {
    'gb': 'en_GB',
    'de': 'de_DE',
    'fr': 'fr_FR',
    'nl': 'nl_NL',
    'es': 'es_ES',
    'it': 'it_IT',
    'ch': 'de_CH', # Switzerland (could be fr_CH, it_CH)
    'be': 'nl_BE', # Belgium (could be fr_BE)
    'pl': 'pl_PL',
    'at': 'de_AT',
    'pt': 'pt_PT',
    'se': 'sv_SE',
    'no': 'no_NO',
    'dk': 'dk_DK',
    'fi': 'fi_FI',
    'cz': 'cs_CZ',
    'hu': 'hu_HU',
    'ie': 'en_IE',
    'ro': 'ro_RO',
    'gr': 'el_GR'
}

# List of countries likely supported (Keep this for the bot menu)
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
    Menghasilkan IBAN valid menggunakan library Faker.
    Tidak lagi menggunakan scraping agar lebih cepat dan reliabel.
    """
    country_code = country_code.lower()
    
    # Dapatkan locale yang sesuai, default ke GB jika tidak ditemukan
    locale = COUNTRY_LOCALES.get(country_code, 'en_GB')
    
    try:
        fake = Faker(locale)
        return fake.iban()
    except Exception as e:
        logger.error(f"Faker IBAN generation failed for {country_code}: {e}")
        # Fallback to generic if specific locale fails
        try:
            return Faker().iban()
        except:
            return "Gagal membuat IBAN."

def get_country_name(code):
    return FAKEIBAN_COUNTRIES.get(code.lower(), code.upper())