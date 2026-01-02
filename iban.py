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

def analyze_iban(iban_str):
    """
    Parses an IBAN string to extract component details based on country rules.
    Returns a dictionary with details.
    """
    if not iban_str: return None
    
    iban = iban_str.replace(' ', '').upper()
    length = len(iban)
    
    if length < 5: return None
    
    country_code = iban[:2]
    check_digits = iban[2:4]
    bban = iban[4:]
    
    details = {
        'iban': iban,
        'length': length,
        'country_code': country_code,
        'check_digits': check_digits,
        'bban': bban,
        'bank_code': None,
        'account_number': None,
        'branch_code': None
    }
    
    # Specific Parsing Rules based on standard IBAN registry formats
    try:
        if country_code == 'DE': # Germany (22 chars) -> BLZ (8) + Account (10)
            details['bank_code'] = bban[:8]      # Bankleitzahl
            details['account_number'] = bban[8:] # Kontonummer
            
        elif country_code == 'GB': # UK (22 chars) -> Bank (4) + Sort (6) + Account (8)
            # BBAN: AAAA SSSSSS CCCCCCCC
            details['bank_code'] = bban[:4]        # Bank Identifier
            details['branch_code'] = bban[4:10]    # Sort Code
            details['account_number'] = bban[10:]  # Account Number
            
        elif country_code == 'FR': # France (27 chars) -> Bank (5) + Branch (5) + Account (11) + Key (2)
            details['bank_code'] = bban[:5]
            details['branch_code'] = bban[5:10]
            details['account_number'] = bban[10:21]
            
        elif country_code == 'ES': # Spain (24 chars) -> Bank (4) + Branch (4) + Check (2) + Account (10)
            details['bank_code'] = bban[:4]
            details['branch_code'] = bban[4:8]
            details['account_number'] = bban[10:]
            
        elif country_code == 'IT': # Italy (27 chars) -> Check (1) + Bank (5) + Branch (5) + Account (12)
            details['bank_code'] = bban[1:6]  # ABI
            details['branch_code'] = bban[6:11] # CAB
            details['account_number'] = bban[11:]
            
        elif country_code == 'NL': # Netherlands (18 chars) -> Bank (4) + Account (10)
            details['bank_code'] = bban[:4]
            details['account_number'] = bban[4:]
            
        elif country_code == 'CH': # Switzerland (21 chars) -> Bank (5) + Account (12)
             details['bank_code'] = bban[:5]
             details['account_number'] = bban[5:]
             
        elif country_code == 'PL': # Poland (28 chars) -> Bank (8) + Account (16)
            # Actually BBAN start with 8 digit bank ID (including check sum)
            details['bank_code'] = bban[:8]
            details['account_number'] = bban[8:]
            
        # Add more specific parsers if needed, otherwise fallback to generic BBAN display
        
    except Exception as e:
        logger.error(f"Error parsing IBAN details for {country_code}: {e}")
        
    return details
