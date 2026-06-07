from flask import Flask, request, jsonify
from faker import Faker
from faker.config import AVAILABLE_LOCALES
from unidecode import unidecode

app = Flask(__name__)
app.json.ensure_ascii = False

# Country name -> locale for names/phones (native script)
COUNTRY_LOCALE = {
    'india': 'hi_IN',
    'iran': 'fa_IR',
    'japan': 'ja_JP',
    'germany': 'de_DE',
    'france': 'fr_FR',
    'usa': 'en_US',
    'uk': 'en_GB',
    # ... add others as needed
}

# Country name -> English locale for address (perfect English)
ENGLISH_ADDRESS_LOCALE = {
    'india': 'en_IN',      # <-- FIXES YOUR ISSUE
    'usa': 'en_US',
    'uk': 'en_GB',
    'canada': 'en_CA',
    'australia': 'en_AU',
}

def get_address_faker(country_name):
    """Returns a Faker instance that generates English addresses."""
    key = country_name.lower().strip()
    if key in ENGLISH_ADDRESS_LOCALE:
        return Faker(ENGLISH_ADDRESS_LOCALE[key])
    # For countries without English locale (Iran, Japan, etc.)
    if key in COUNTRY_LOCALE:
        return Faker(COUNTRY_LOCALE[key])  # will be transliterated later
    return Faker('en_US')  # fallback

@app.route('/fake', methods=['GET'])
def fake_person_and_address():
    country_param = request.args.get('country')
    if not country_param:
        return jsonify({'error': 'Missing country'}), 400

    country_lower = country_param.lower().strip()
    
    # Get name/phone faker (native locale)
    if country_lower not in COUNTRY_LOCALE:
        return jsonify({'error': f'Country "{country_param}" not supported'}), 400
    native_faker = Faker(COUNTRY_LOCALE[country_lower])
    first_name = native_faker.first_name()
    last_name = native_faker.last_name()
    phone_number = native_faker.phone_number()

    # Get address faker (English where possible)
    addr_faker = get_address_faker(country_lower)
    street = addr_faker.street_address()
    city = addr_faker.city()
    # Handle state/administrative unit safely
    if hasattr(addr_faker, 'state'):
        state = addr_faker.state()
    elif hasattr(addr_faker, 'administrative_unit'):
        state = addr_faker.administrative_unit()
    else:
        state = ''
    zipcode = addr_faker.postcode()
    country = addr_faker.current_country()

    # Transliterate only if the address might be non-English (i.e., we used native locale)
    if country_lower not in ENGLISH_ADDRESS_LOCALE:
        street = unidecode(street)
        city = unidecode(city)
        state = unidecode(state)
        zipcode = unidecode(zipcode)
        country = unidecode(country)

    full = f"{street}, {city}, {state} {zipcode}".strip()
    response = {
        'locale': COUNTRY_LOCALE[country_lower],
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'address': {
            'street': street,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'country': country,
            'full_address': full
        }
    }
    return jsonify(response)

@app.route('/countries', methods=['GET'])
def list_countries():
    return jsonify({
        'supported_countries': list(COUNTRY_LOCALE.keys()),
        'english_address_countries': list(ENGLISH_ADDRESS_LOCALE.keys())
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
