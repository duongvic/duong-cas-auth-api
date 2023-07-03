COUNTRY_CODE = {
    'vn': 'Vietnam',
    'us': 'United States',
    'jp': 'Japan',
}

LANGUAGE_CODE = {
    'vi': 'Vietnam',
    'en': 'English',
}


def get_country_name(country_code):
    """
    Get country name by code.
    :param country_code:
    :return:
    """
    return COUNTRY_CODE.get(country_code.lower()) if country_code else None


def get_language_name(language):
    """
    Get language name by code.
    :param language:
    :return:
    """
    return LANGUAGE_CODE.get(language.lower())
