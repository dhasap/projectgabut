import logging
from faker import Faker

# Set up logging
logger = logging.getLogger(__name__)

# Map 2-letter country codes to Faker Locales
COUNTRY_LOCALES = {
    'gb': 'en_GB',
    'de': 'de_DE',
    'fr': 'fr_FR',
    'nl': 'nl_NL',
    'es': 'es_ES',
    'it': 'it_IT',
    'ch': 'de_CH',
    'be': 'nl_BE',
    'pl': 'pl_PL',
    'at': 'de_AT',
    'pt': 'pt_PT',
    'se': 'sv_SE',
    'no': 'no_NO',
    'dk': 'da_DK',
    'fi': 'fi_FI',
    'cz': 'cs_CZ',
    'hu': 'hu_HU',
    'ie': 'en_IE',
    'ro': 'ro_RO',
    'gr': 'el_GR'
}

# For display purposes in the bot
COUNTRY_NAMES = {
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
    Generates a valid fake IBAN for the given country code using Faker.
    """
    country_code = country_code.lower()
    locale = COUNTRY_LOCALES.get(country_code)
    
    if not locale:
        # Fallback or return None if code not supported
        return None

    try:
        # Initialize Faker with specific locale
        fake = Faker(locale)
        # Generate IBAN
        return fake.iban()
    except Exception as e:
        logger.error(f"Faker IBAN generation failed for {country_code} ({locale}): {e}")
        return None

def get_country_name(code):
    return COUNTRY_NAMES.get(code.lower(), code.upper())
